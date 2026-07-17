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

"""Relay namespaced TF topics to global TF topics for Nav2 compatibility."""

import os
from typing import Optional

from tf2_msgs.msg import TFMessage

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

import yaml


class TfRelay(Node):
    """Republish /<namespace>/tf(/_static) onto /tf(/_static)."""

    def __init__(self) -> None:
        super().__init__('tf_relay')

        self.declare_parameter('setup_path', '/home/ros/setup/path/')
        self.declare_parameter('namespace', '')

        setup_path = str(self.get_parameter('setup_path').value)
        namespace_param = str(self.get_parameter('namespace').value).strip()

        namespace = namespace_param or self._read_namespace_from_setup(setup_path)
        namespace = namespace.strip('/')

        if not namespace:
            self.get_logger().warn('namespace is empty, tf relay is disabled')
            return

        source_tf = f'/{namespace}/tf'
        source_tf_static = f'/{namespace}/tf_static'

        self._pub_tf = self.create_publisher(TFMessage, '/tf', self._dynamic_tf_qos())
        self._pub_tf_static = self.create_publisher(TFMessage, '/tf_static', self._static_tf_qos())

        self._sub_tf = self.create_subscription(
            TFMessage,
            source_tf,
            self._on_tf,
            self._dynamic_tf_qos(),
        )
        self._sub_tf_static = self.create_subscription(
            TFMessage,
            source_tf_static,
            self._on_tf_static,
            self._static_tf_qos(),
        )

        self.get_logger().info(
            f'relaying {source_tf} -> /tf and {source_tf_static} -> /tf_static',
        )

    def _on_tf(self, msg: TFMessage) -> None:
        self._pub_tf.publish(msg)

    def _on_tf_static(self, msg: TFMessage) -> None:
        self._pub_tf_static.publish(msg)

    @staticmethod
    def _dynamic_tf_qos() -> QoSProfile:
        return QoSProfile(
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )

    @staticmethod
    def _static_tf_qos() -> QoSProfile:
        return QoSProfile(
            depth=100,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

    def _read_namespace_from_setup(self, setup_path: str) -> str:
        robot_yaml = os.path.join(setup_path, 'robot.yaml')
        if not os.path.exists(robot_yaml):
            self.get_logger().warn(f'robot.yaml not found at {robot_yaml}')
            return ''

        try:
            with open(robot_yaml, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f'failed reading robot.yaml: {exc}')
            return ''

        namespace = self._extract_namespace(config)
        if not namespace:
            self.get_logger().warn('could not determine namespace from robot.yaml')
        return namespace

    @staticmethod
    def _extract_namespace(config: dict) -> str:
        system = config.get('system', {})
        ros2 = system.get('ros2', {})

        namespace: Optional[str] = ros2.get('namespace')
        if namespace:
            return str(namespace)

        namespace = system.get('namespace')
        if namespace:
            return str(namespace)

        return ''


def main() -> None:
    rclpy.init()
    node = TfRelay()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
