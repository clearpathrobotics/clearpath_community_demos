#!/usr/bin/env python3

# Copyright 2026 Rockwell Automation Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Frontier exploration node that drives Nav2 goals from a live occupancy grid."""

from collections import deque
import math

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from nav_msgs.srv import GetMap
import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from tf2_ros import Buffer, LookupException, TransformException
from tf2_ros.transform_listener import TransformListener

from .frontiers import goal_timeout_sec, Grid, select_frontier


class FrontierExplorer(Node):
    """Select frontier cells from map updates and send them as Nav2 goals."""

    def __init__(self) -> None:
        super().__init__('frontier_explorer')

        self.declare_parameter('replan_period_sec', 2.0)
        self.declare_parameter('goal_timeout_sec', 30.0)
        self.declare_parameter('goal_timeout_per_m_sec', 15.0)
        self.declare_parameter('frontier_neighbor_unknown_min', 1)
        self.declare_parameter('obstacle_inflation_cells', 3)
        # Nav2 costmap cost (0-100) above which a frontier is too close to obstacles to target
        self.declare_parameter('max_goal_cost', 50)
        self.declare_parameter('min_goal_distance_m', 1.0)
        self.declare_parameter('max_goal_distance_m', 20.0)
        self.declare_parameter('goal_revisit_distance_m', 1.0)
        # Close enough to count a frontier as visited; above the Nav2 progress checker radius, so
        # the robot isn't left creeping into the exact goal pose
        self.declare_parameter('goal_reached_distance_m', 0.6)
        self.declare_parameter('exploration_complete_cycles', 8)

        self._replan_period_sec = self.get_parameter('replan_period_sec').value
        self._goal_timeout_sec = self.get_parameter('goal_timeout_sec').value
        self._goal_timeout_per_m_sec = self.get_parameter('goal_timeout_per_m_sec').value
        self._frontier_neighbor_unknown_min = self.get_parameter(
            'frontier_neighbor_unknown_min',
        ).value
        self._obstacle_inflation_cells = self.get_parameter('obstacle_inflation_cells').value
        self._max_goal_cost = self.get_parameter('max_goal_cost').value
        self._min_goal_distance_m = self.get_parameter('min_goal_distance_m').value
        self._max_goal_distance_m = self.get_parameter('max_goal_distance_m').value
        self._goal_revisit_distance_m = self.get_parameter('goal_revisit_distance_m').value
        self._goal_reached_distance_m = self.get_parameter('goal_reached_distance_m').value
        self._exploration_complete_cycles = self.get_parameter('exploration_complete_cycles').value

        self._latest_map: OccupancyGrid | None = None
        self._latest_costmap: OccupancyGrid | None = None
        self._goal_sent_at: Time | None = None
        self._goal_timeout = Duration(seconds=self._goal_timeout_sec)
        self._goal_xy: tuple[float, float] | None = None
        self._cancel_requested = False
        self._close_enough = False
        self._visited_goals: deque[tuple[float, float]] = deque(maxlen=100)
        self._no_frontier_cycles = 0
        self._reported_waiting_for_map = False
        self._reported_waiting_for_nav2 = False
        self._reported_waiting_for_tf = False
        self._map_request_in_flight = False

        map_qos = QoSProfile(depth=1)
        map_qos.reliability = ReliabilityPolicy.RELIABLE
        map_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL

        self._map_sub = self.create_subscription(
            OccupancyGrid,
            'map',
            self._on_map,
            map_qos,
        )
        # Nav2's global costmap encodes the robot footprint, so goals it marks blocked are skipped
        self._costmap_sub = self.create_subscription(
            OccupancyGrid,
            'global_costmap/costmap',
            self._on_costmap,
            map_qos,
        )

        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._map_client = self.create_client(GetMap, 'slam_toolbox/dynamic_map')
        self._goal_handle = None
        self._result_future = None

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self._timer = self.create_timer(self._replan_period_sec, self._on_timer)
        self.get_logger().info('frontier_explorer started')

    def _on_map(self, msg: OccupancyGrid) -> None:
        self._latest_map = msg
        self._reported_waiting_for_map = False

    def _on_costmap(self, msg: OccupancyGrid) -> None:
        self._latest_costmap = msg

    def _on_timer(self) -> None:
        if self._latest_map is None:
            self._request_map()
            if not self._reported_waiting_for_map:
                self.get_logger().info('waiting for map')
                self._reported_waiting_for_map = True
            return

        if not self._nav_client.server_is_ready():
            if not self._reported_waiting_for_nav2:
                self.get_logger().info('waiting for navigate_to_pose action server')
                self._reported_waiting_for_nav2 = True
            return

        self._reported_waiting_for_nav2 = False

        if self._goal_xy is not None:
            self._check_active_goal()
            return

        robot_xy = self._robot_position_in_map()
        if robot_xy is None:
            return

        goal_xy = self._select_frontier_goal(self._latest_map, robot_xy)
        if goal_xy is None:
            self._no_frontier_cycles += 1
            if self._no_frontier_cycles == self._exploration_complete_cycles:
                self.get_logger().info(
                    'no new frontier goals found for several cycles; map may be complete',
                )
            return

        self._no_frontier_cycles = 0
        self._send_goal(goal_xy, robot_xy)

    def _request_map(self) -> None:
        if self._map_request_in_flight:
            return

        if not self._map_client.wait_for_service(timeout_sec=0.0):
            return

        self._map_request_in_flight = True
        future = self._map_client.call_async(GetMap.Request())
        future.add_done_callback(self._on_map_response)

    def _on_map_response(self, future) -> None:
        self._map_request_in_flight = False
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().warn(f'failed to fetch map from slam_toolbox: {exc}')
            return

        if response.map.info.width == 0 or response.map.info.height == 0:
            return

        self._latest_map = response.map
        self._reported_waiting_for_map = False

    def _check_active_goal(self) -> None:
        # Nothing to do until Nav2 accepts the goal, or while a cancel is in flight
        if self._goal_handle is None or self._cancel_requested:
            return

        robot_xy = self._robot_position_in_map()
        if (
            robot_xy is not None
            and math.hypot(
                self._goal_xy[0] - robot_xy[0],
                self._goal_xy[1] - robot_xy[1],
            )
            <= self._goal_reached_distance_m
        ):
            self._close_enough = True
            self._cancel_goal()
        elif self.get_clock().now() - self._goal_sent_at > self._goal_timeout:
            self.get_logger().warn('goal timeout reached, canceling and replanning')
            self._cancel_goal()

    def _cancel_goal(self) -> None:
        self._cancel_requested = True
        self._goal_handle.cancel_goal_async().add_done_callback(self._on_cancel_done)

    def _on_cancel_done(self, future) -> None:
        # The goal is cleared in _on_goal_result once Nav2 reports it canceled
        try:
            future.result()
        except Exception as exc:
            self.get_logger().warn(f'failed to cancel goal cleanly: {exc}')
            self._clear_goal()

    def _clear_goal(self) -> None:
        self._goal_handle = None
        self._result_future = None
        self._goal_sent_at = None
        self._goal_xy = None
        self._cancel_requested = False
        self._close_enough = False

    def _robot_position_in_map(self) -> tuple[float, float] | None:
        map_frame = self._latest_map.header.frame_id or 'map'
        try:
            tf = self._tf_buffer.lookup_transform(
                map_frame,
                'base_link',
                Time(),
                timeout=Duration(seconds=0.1),
            )
        except (LookupException, TransformException):
            if not self._reported_waiting_for_tf:
                self.get_logger().info('waiting for map->base_link transform')
                self._reported_waiting_for_tf = True
            return None

        self._reported_waiting_for_tf = False

        return (tf.transform.translation.x, tf.transform.translation.y)

    @staticmethod
    def _to_grid(msg: OccupancyGrid) -> Grid:
        info = msg.info
        data = np.frombuffer(msg.data, dtype=np.int8).reshape(info.height, info.width)
        return Grid(data, info.origin.position.x, info.origin.position.y, info.resolution)

    def _select_frontier_goal(
        self,
        occ: OccupancyGrid,
        robot_xy: tuple[float, float],
    ) -> tuple[float, float] | None:
        goal = select_frontier(
            self._to_grid(occ),
            robot_xy,
            min_unknown_neighbors=self._frontier_neighbor_unknown_min,
            clearance_cells=self._obstacle_inflation_cells,
            min_distance_m=self._min_goal_distance_m,
            max_distance_m=self._max_goal_distance_m,
            visited=self._visited_goals,
            revisit_distance_m=self._goal_revisit_distance_m,
            costmap=self._to_grid(self._latest_costmap) if self._latest_costmap else None,
            max_goal_cost=self._max_goal_cost,
        )
        if goal is None and self._visited_goals:
            self.get_logger().info('no unseen frontier left, clearing goal history and retrying')
            self._visited_goals.clear()
        return goal

    def _send_goal(self, goal_xy: tuple[float, float], robot_xy: tuple[float, float]) -> None:
        goal = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.frame_id = self._latest_map.header.frame_id or 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = goal_xy[0]
        pose.pose.position.y = goal_xy[1]
        pose.pose.position.z = 0.0

        yaw = math.atan2(goal_xy[1] - robot_xy[1], goal_xy[0] - robot_xy[0])
        pose.pose.orientation = self._yaw_to_quaternion(yaw)
        goal.pose = pose

        self.get_logger().info(f'sending frontier goal x={goal_xy[0]:.2f}, y={goal_xy[1]:.2f}')
        send_future = self._nav_client.send_goal_async(goal)
        send_future.add_done_callback(self._on_goal_response)
        self._goal_sent_at = self.get_clock().now()
        self._goal_xy = goal_xy
        distance = math.hypot(goal_xy[0] - robot_xy[0], goal_xy[1] - robot_xy[1])
        self._goal_timeout = Duration(
            seconds=goal_timeout_sec(
                distance,
                self._goal_timeout_sec,
                self._goal_timeout_per_m_sec,
            ),
        )

    def _on_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:
            self.get_logger().warn(f'goal request failed: {exc}')
            self._clear_goal()
            return

        if not goal_handle.accepted:
            self.get_logger().warn('frontier goal rejected by Nav2')
            self._clear_goal()
            return

        self._goal_handle = goal_handle
        self._result_future = goal_handle.get_result_async()
        self._result_future.add_done_callback(
            lambda result, handle=goal_handle: self._on_goal_result(result, handle),
        )

    def _on_goal_result(self, future, goal_handle) -> None:
        if goal_handle is not self._goal_handle:
            return

        status = GoalStatus.STATUS_UNKNOWN
        try:
            status = future.result().status
        except Exception as exc:
            self.get_logger().warn(f'goal result failed: {exc}')

        self._visited_goals.append(self._goal_xy)

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('frontier goal reached')
        elif status == GoalStatus.STATUS_CANCELED and self._close_enough:
            self.get_logger().info(
                f'frontier goal reached (within {self._goal_reached_distance_m:.1f} m)',
            )
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('frontier goal canceled')
        else:
            self.get_logger().warn(f'frontier goal finished with status {status}')

        self._clear_goal()

    @staticmethod
    def _yaw_to_quaternion(yaw: float) -> Quaternion:
        half = yaw * 0.5
        q = Quaternion()
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(half)
        q.w = math.cos(half)
        return q


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FrontierExplorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
