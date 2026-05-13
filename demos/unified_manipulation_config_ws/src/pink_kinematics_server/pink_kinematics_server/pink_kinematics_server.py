#!/usr/bin/env python3
import math
import numpy as np
import rclpy
from rclpy.node import Node
import pinocchio as pin
from pink import Configuration
from pink.tasks import FrameTask
from pink.solve_ik import solve_ik

import traceback

from geometry_msgs.msg import Transform, Vector3, Quaternion
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import MoveItErrorCodes, RobotState
from pink_kinematics_server.pink_kinematics_server_parameters import pink_kinematics_server as ServerParams


class PinkIKServer(Node):
    def __init__(self):
        super().__init__("pink_ik_server")
        param_listener = ServerParams.ParamListener(self)
        self.params = param_listener.get_params()
        robot_description = self.params.robot_description
        base_joint_name = self.params.base_joint_name
        service_name = self.params.service_name

        # Load robot model with Pinocchio
        self.model = pin.buildModelFromXML(
            robot_description,
            root_joint=pin.JointModelPlanar(),
            root_joint_name=base_joint_name,
        )

        self.data = self.model.createData()

        # Find the child frame of the planar base joint to use as the base anchor frame
        base_jid = self.model.getJointId(base_joint_name)
        for frame in self.model.frames:
            if frame.parentJoint == base_jid and frame.type == pin.FrameType.BODY:
                self.base_frame_name = frame.name
                break
        if not self.base_frame_name:
            self.get_logger().warn(
                f"Could not find a child frame of the base joint '{base_joint_name}', assuming base_link"
            )
            self.base_frame_name = "base_link"
        self.get_logger().info(f"Using '{self.base_frame_name}' as base frame")

        self.srv = self.create_service(GetPositionIK, service_name, self.solve_ik_callback)
        self.get_logger().info(f"Pink IK service '{service_name}' ready")

    def solve_ik_callback(self, request, response):
        ik_req = request.ik_request

        joint_names = list(ik_req.robot_state.joint_state.name)

        tip_link = ik_req.ik_link_name
        target_pose = ik_req.pose_stamped.pose
        ik_base_frame = ik_req.pose_stamped.header.frame_id
        timeout_secs = ik_req.timeout.sec + ik_req.timeout.nanosec * 1e-9

        try:
            # Convert from ROS robot state message to Pinocchio configuration
            q = self._robot_state_to_pinocchio_q(ik_req.robot_state)
            configuration = Configuration(self.model, self.data, q)

            # Create a frame task for the tip link
            tasks = {
                "tip": FrameTask(
                    tip_link,
                    position_cost=1.0,
                    orientation_cost=1.0,
                ),
                "base": FrameTask(
                    self.base_frame_name,
                    position_cost=self.params.ik_base_cost,
                    orientation_cost=self.params.ik_base_cost,
                ),
            }

            # Convert target pose to Pinocchio SE3
            target_in_base = pin.SE3(
                pin.Quaternion(
                    target_pose.orientation.w,
                    target_pose.orientation.x,
                    target_pose.orientation.y,
                    target_pose.orientation.z,
                ).toRotationMatrix(),
                np.array(
                    [
                        target_pose.position.x,
                        target_pose.position.y,
                        target_pose.position.z,
                    ]
                ),
            )

            # Transform target to world frame
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)

            if ik_base_frame and self.model.existFrame(ik_base_frame):
                frame_id = self.model.getFrameId(ik_base_frame)
                transform_world_base = self.data.oMf[frame_id]
                target = transform_world_base * target_in_base
            elif ik_base_frame == self.params.odom_frame:  # No transform needed if target is already in odom frame
                target = target_in_base
            else:
                # If we don't have a base frame, assume base frame is world frame
                self.get_logger().warn(
                    f"Base frame '{ik_base_frame}' not found in model, assuming target pose is in world frame"
                )
                target = target_in_base

            tasks["tip"].set_target(target)

            # Set the base task target to the current base pose to minimize unnecessary base motion during IK.
            base_fid = self.model.getFrameId(self.base_frame_name)
            tasks["base"].set_target(self.data.oMf[base_fid])

            dt = self.params.ik_time_step
            min_iters = self.params.ik_min_iterations
            max_iters = max(min_iters, int(timeout_secs / dt))
            velocity = np.zeros(self.model.nv)
            converge_tol = self.params.ik_convergence_tolerance

            # Solve IK by iteratively integrating velocity commands
            for _ in range(max_iters):
                velocity = solve_ik(configuration, tasks.values(), dt, solver="quadprog")
                configuration.integrate_inplace(velocity, dt)
                if np.linalg.norm(velocity) < converge_tol:
                    break

            converged = bool(np.linalg.norm(velocity) < converge_tol)
            if converged:
                response.error_code.val = MoveItErrorCodes.SUCCESS
                # Convert Pinocchio configuration back to MoveIt robot state message
                response.solution = self._pinocchio_q_to_robot_state(configuration.q)
            else:
                response.error_code.val = MoveItErrorCodes.NO_IK_SOLUTION
                response.error_code.message = "Did not converge"
                self.get_logger().warn("IK solve did not converge within the timeout")
        except Exception as e:
            response.error_code.val = MoveItErrorCodes.NO_IK_SOLUTION
            response.error_code.message = str(e)
            self.get_logger().error(
                f"IK solve failed:\n"
                f"  joint_names ({len(joint_names)}): {joint_names}\n"
                f"  tip_link: {tip_link}\n"
                f"{traceback.format_exc()}"
            )
        return response

    def _pinocchio_q_to_robot_state(self, q):
        """Convert a Pinocchio configuration vector to a robot state message used by MoveIt.

        - Planar joints (nq=4): (x, y, sin, cos) converted to geometry_msgs/Transform in multi_dof_joint_state
        - Continuous revolute joints (nq=2): (cos, sin) converted back to raw angle in joint_state
        - Bounded revolute / prismatic joints (nq=1): copied directly in joint_state
        - Fixed joints (nq=0): ignored
        """
        joint_state_names = []
        joint_state_positions = []
        mdof_joint_names = []
        mdof_transforms = []

        for name in self.model.names:
            jid = self.model.getJointId(name)
            idx = self.model.idx_qs[jid]
            nq = self.model.nqs[jid]
            if nq == 4:
                # Planar joint: (x, y, cos, sin) -> Transform in multi_dof_joint_state
                x = float(q[idx])
                y = float(q[idx + 1])
                theta = float(np.arctan2(q[idx + 3], q[idx + 2]))
                t = Transform()
                t.translation = Vector3(x=x, y=y, z=0.0)
                t.rotation = Quaternion(
                    x=0.0,
                    y=0.0,
                    z=math.sin(theta / 2.0),
                    w=math.cos(theta / 2.0),
                )
                mdof_joint_names.append(name)
                mdof_transforms.append(t)
            elif nq == 2:
                # Continuous revolute: (cos, sin) -> raw angle
                joint_state_names.append(name)
                joint_state_positions.append(float(np.arctan2(q[idx + 1], q[idx])))
            elif nq == 1:
                # Bounded revolute/prismatic: copy directly
                joint_state_names.append(name)
                joint_state_positions.append(float(q[idx]))
            elif nq == 0:
                # Fixed joint, no configuration variable
                continue
            else:
                self.get_logger().error(
                    f"Failed to convert joint {name} from configuration vector to RobotState message: unsupported nq={nq}, skipping"
                )

        robot_state_msg = RobotState()
        robot_state_msg.joint_state.name = joint_state_names
        robot_state_msg.joint_state.position = joint_state_positions

        robot_state_msg.multi_dof_joint_state.joint_names = mdof_joint_names
        robot_state_msg.multi_dof_joint_state.transforms = mdof_transforms
        robot_state_msg.multi_dof_joint_state.header.frame_id = self.params.odom_frame
        return robot_state_msg

    def _robot_state_to_pinocchio_q(self, robot_state):
        """Convert MoveIt robot state message into a Pinocchio configuration.

        - Multi-dof joints (transform) are converted to (x, y, cos(theta), sin(theta)) for Pinocchio.
        - MoveIt continuous revolute joints(theta), are converted to (cos, sin) for Pinocchio.
        - Bounded revolute/prismatic joints are copied directly
        - Fixed joints are ignored
        """
        q = pin.neutral(self.model)

        mdof_joint_names = robot_state.multi_dof_joint_state.joint_names
        mdof_transforms = robot_state.multi_dof_joint_state.transforms

        for name, transform in zip(mdof_joint_names, mdof_transforms):
            # Convert transform to (x, y, cos(theta), sin(theta)) for Pinocchio planar joint
            # Note that this only works for planar joints for now
            t = transform.translation
            r = transform.rotation
            theta = math.atan2(
                2.0 * (r.w * r.z + r.x * r.y),
                1.0 - 2.0 * (r.y * r.y + r.z * r.z),
            )
            joint_name = name
            if self.model.existJointName(joint_name):
                jid = self.model.getJointId(joint_name)
                idx = self.model.idx_qs[jid]
                q[idx] = t.x
                q[idx + 1] = t.y
                q[idx + 2] = np.cos(theta)
                q[idx + 3] = np.sin(theta)
            else:
                self.get_logger().warn(
                    f"Robot state message contains multi-DOF joint '{joint_name}' that is not found in the Pinocchio model, skipping"
                )

        joint_names = robot_state.joint_state.name
        joint_values = robot_state.joint_state.position
        for name, value in zip(joint_names, joint_values):
            if not self.model.existJointName(name):
                self.get_logger().warn(
                    f"Robot state message contains joint '{name}' that is not found in the Pinocchio model, skipping"
                )
                continue
            jid = self.model.getJointId(name)
            idx = self.model.idx_qs[jid]
            nq = self.model.nqs[jid]
            if nq == 2:
                # Convert from angle to (cos, sin) for continuous revolute joints
                theta = value
                q[idx] = np.cos(theta)
                q[idx + 1] = np.sin(theta)
            elif nq == 1:
                # No conversion needed for bounded revolute/prismatic joints
                q[idx] = value
            elif nq == 0:
                # Fixed joint, no configuration variable
                continue
            else:
                self.get_logger().error(
                    f"Failed to convert joint {name} from RobotState message to configuration vector: unsupported nq={nq}, skipping."
                )
        return q


def main(args=None):
    rclpy.init(args=args)
    node = PinkIKServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
