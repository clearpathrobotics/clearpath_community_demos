"""
Drive the robot in a small square using odometry feedback.

Example of a demo.
Python counterpart to the C++ ``hello_square_cpp`` executable. Use either to
verify your environment is set up correctly before trying more complex demos.
"""

import math

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node

SIDE_LENGTH_M = 1.0
TURN_ANGLE_RAD = math.pi / 2
LINEAR_SPEED = 0.2  # m/s
ANGULAR_SPEED = 0.5  # rad/s
POSITION_TOLERANCE_M = 0.02
HEADING_TOLERANCE_RAD = math.radians(2.0)


def yaw_from_quaternion(q) -> float:
    """Extract yaw (rotation about Z) from a geometry_msgs Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def angle_diff(a: float, b: float) -> float:
    """Return the smallest signed difference ``a - b`` wrapped to [-pi, pi]."""
    return math.atan2(math.sin(a - b), math.cos(a - b))


class HelloSquare(Node):
    """Drive a 1 m x 1 m square using odometry to close the loop."""

    def __init__(self) -> None:
        super().__init__('hello_square')
        self._cmd_pub = self.create_publisher(TwistStamped, 'cmd_vel', 10)
        self._odom_sub = self.create_subscription(
            Odometry, 'platform/odom', self._on_odom, 10
        )
        self._side = 0
        self._phase = 'forward'
        self._have_odom = False
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0
        self._start_x = 0.0
        self._start_y = 0.0
        self._start_yaw = 0.0
        self._timer = self.create_timer(0.05, self._tick)
        self.get_logger().info('Hello, Clearpath! Driving a 1m x 1m square.')

    def _on_odom(self, msg: Odometry) -> None:
        self._x = msg.pose.pose.position.x
        self._y = msg.pose.pose.position.y
        self._yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        if not self._have_odom:
            self._start_x = self._x
            self._start_y = self._y
            self._start_yaw = self._yaw
            self._have_odom = True

    def _publish(self, linear: float = 0.0, angular: float = 0.0) -> None:
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.twist.linear.x = linear
        msg.twist.angular.z = angular
        self._cmd_pub.publish(msg)

    def _distance_traveled(self) -> float:
        dx = self._x - self._start_x
        dy = self._y - self._start_y
        return math.hypot(dx, dy)

    def _heading_change(self) -> float:
        return abs(angle_diff(self._yaw, self._start_yaw))

    def _tick(self) -> None:
        if not self._have_odom:
            return

        if self._phase == 'forward':
            if self._distance_traveled() + POSITION_TOLERANCE_M < SIDE_LENGTH_M:
                self._publish(linear=LINEAR_SPEED)
            else:
                self._publish()
                self.get_logger().info(f'Side {self._side + 1} complete.')
                self._phase = 'turn'
                self._start_yaw = self._yaw
        elif self._phase == 'turn':
            if self._heading_change() + HEADING_TOLERANCE_RAD < TURN_ANGLE_RAD:
                self._publish(angular=ANGULAR_SPEED)
            else:
                self._publish()
                self._side += 1
                if self._side >= 4:
                    self.get_logger().info('Square complete.')
                    rclpy.shutdown()
                    return
                self._phase = 'forward'
                self._start_x = self._x
                self._start_y = self._y


def main(args=None) -> None:
    """Spin the ``HelloSquare`` node."""
    rclpy.init(args=args)
    node = HelloSquare()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
