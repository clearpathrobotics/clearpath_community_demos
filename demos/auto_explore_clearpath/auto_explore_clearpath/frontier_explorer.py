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
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from tf2_ros import Buffer, LookupException, TransformException
from tf2_ros.transform_listener import TransformListener

GridPoint = tuple[int, int]


class FrontierExplorer(Node):
    """Select frontier cells from map updates and send them as Nav2 goals."""

    def __init__(self) -> None:
        super().__init__('frontier_explorer')

        self.declare_parameter('replan_period_sec', 2.0)
        self.declare_parameter('goal_timeout_sec', 90.0)
        self.declare_parameter('frontier_neighbor_unknown_min', 1)
        self.declare_parameter('obstacle_inflation_cells', 3)
        self.declare_parameter('min_goal_distance_m', 1.0)
        self.declare_parameter('max_goal_distance_m', 20.0)
        self.declare_parameter('goal_revisit_distance_m', 1.0)
        self.declare_parameter('exploration_complete_cycles', 8)

        self._replan_period_sec = self.get_parameter('replan_period_sec').value
        self._goal_timeout_sec = self.get_parameter('goal_timeout_sec').value
        self._frontier_neighbor_unknown_min = self.get_parameter(
            'frontier_neighbor_unknown_min',
        ).value
        self._obstacle_inflation_cells = self.get_parameter('obstacle_inflation_cells').value
        self._min_goal_distance_m = self.get_parameter('min_goal_distance_m').value
        self._max_goal_distance_m = self.get_parameter('max_goal_distance_m').value
        self._goal_revisit_distance_m = self.get_parameter('goal_revisit_distance_m').value
        self._exploration_complete_cycles = self.get_parameter('exploration_complete_cycles').value

        self._latest_map: OccupancyGrid | None = None
        self._goal_sent_at: Time | None = None
        self._goal_xy: tuple[float, float] | None = None
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

        if self._goal_handle is not None:
            self._check_goal_timeout()
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

    def _check_goal_timeout(self) -> None:
        if self._goal_sent_at is None:
            return

        elapsed = self.get_clock().now() - self._goal_sent_at
        if elapsed > Duration(seconds=self._goal_timeout_sec):
            self.get_logger().warn('goal timeout reached, canceling and replanning')
            cancel_future = self._goal_handle.cancel_goal_async()
            cancel_future.add_done_callback(self._on_cancel_done)

    def _on_cancel_done(self, future) -> None:
        try:
            _ = future.result()
        except Exception as exc:
            self.get_logger().warn(f'failed to cancel goal cleanly: {exc}')
        self._goal_handle = None
        self._result_future = None
        self._goal_sent_at = None

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

    def _select_frontier_goal(
        self,
        occ: OccupancyGrid,
        robot_xy: tuple[float, float],
    ) -> tuple[float, float] | None:
        width = occ.info.width
        height = occ.info.height
        resolution = occ.info.resolution
        origin_x = occ.info.origin.position.x
        origin_y = occ.info.origin.position.y

        data: list[int] = list(occ.data)
        robot_mx = int((robot_xy[0] - origin_x) / resolution)
        robot_my = int((robot_xy[1] - origin_y) / resolution)

        best_score = -1.0
        best_goal: GridPoint | None = None

        for my in range(1, height - 1):
            for mx in range(1, width - 1):
                idx = my * width + mx
                if data[idx] != 0:
                    continue

                unknown_neighbors = 0
                occupied_neighbor = False
                for ny in range(my - 1, my + 2):
                    for nx in range(mx - 1, mx + 2):
                        nidx = ny * width + nx
                        nval = data[nidx]
                        if nval == -1:
                            unknown_neighbors += 1
                        elif nval > 50:
                            occupied_neighbor = True

                if unknown_neighbors < self._frontier_neighbor_unknown_min:
                    continue

                if occupied_neighbor:
                    continue

                if not self._is_safe_from_obstacles(
                    data,
                    width,
                    height,
                    mx,
                    my,
                    self._obstacle_inflation_cells,
                ):
                    continue

                dx = mx - robot_mx
                dy = my - robot_my
                dist_cells = math.hypot(dx, dy)
                dist_m = dist_cells * resolution

                if dist_m < self._min_goal_distance_m or dist_m > self._max_goal_distance_m:
                    continue

                gx = origin_x + (mx + 0.5) * resolution
                gy = origin_y + (my + 0.5) * resolution
                if self._was_recently_visited(gx, gy):
                    continue

                score = dist_m + (0.5 * float(unknown_neighbors))
                if score > best_score:
                    best_score = score
                    best_goal = (mx, my)

        if best_goal is None and self._visited_goals:
            self.get_logger().info('no unseen frontier left, clearing goal history and retrying')
            self._visited_goals.clear()
            return None

        if best_goal is None:
            return None

        gx = origin_x + (best_goal[0] + 0.5) * resolution
        gy = origin_y + (best_goal[1] + 0.5) * resolution
        return (gx, gy)

    @staticmethod
    def _is_safe_from_obstacles(
        data: list[int],
        width: int,
        height: int,
        mx: int,
        my: int,
        radius: int,
    ) -> bool:
        min_x = max(0, mx - radius)
        max_x = min(width - 1, mx + radius)
        min_y = max(0, my - radius)
        max_y = min(height - 1, my + radius)

        for ny in range(min_y, max_y + 1):
            row = ny * width
            for nx in range(min_x, max_x + 1):
                if data[row + nx] > 50:
                    return False
        return True

    def _was_recently_visited(self, x: float, y: float) -> bool:
        threshold = self._goal_revisit_distance_m
        return any(math.hypot(x - vx, y - vy) < threshold for vx, vy in self._visited_goals)

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

    def _on_goal_response(self, future) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:
            self.get_logger().warn(f'goal request failed: {exc}')
            self._goal_handle = None
            self._result_future = None
            self._goal_sent_at = None
            return

        if not goal_handle.accepted:
            self.get_logger().warn('frontier goal rejected by Nav2')
            self._goal_handle = None
            self._result_future = None
            self._goal_sent_at = None
            return

        self._goal_handle = goal_handle
        self._result_future = goal_handle.get_result_async()
        self._result_future.add_done_callback(self._on_goal_result)

    def _on_goal_result(self, future) -> None:
        status = GoalStatus.STATUS_UNKNOWN
        try:
            result = future.result()
            status = result.status
        except Exception as exc:
            self.get_logger().warn(f'goal result failed: {exc}')

        if self._goal_xy is not None:
            self._visited_goals.append(self._goal_xy)

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('frontier goal reached')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('frontier goal canceled')
        else:
            self.get_logger().warn(f'frontier goal finished with status {status}')

        self._goal_handle = None
        self._result_future = None
        self._goal_sent_at = None
        self._goal_xy = None

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
