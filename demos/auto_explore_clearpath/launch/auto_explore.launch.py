"""Launch autonomous frontier exploration in the robot namespace from robot.yaml."""

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

from pathlib import Path

from clearpath_config.clearpath_config import ClearpathConfig

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node, PushRosNamespace


ARGUMENTS = [
    DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        choices=['true', 'false'],
        description='Use simulation clock if true.',
    ),
    DeclareLaunchArgument(
        'setup_path',
        default_value='/etc/clearpath/',
        description='Clearpath setup path containing robot.yaml.',
    ),
    DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Robot namespace. If empty, read from robot.yaml.',
    ),
    DeclareLaunchArgument(
        'replan_period_sec',
        default_value='2.0',
        description='Seconds between frontier replanning attempts.',
    ),
    DeclareLaunchArgument(
        'goal_timeout_sec',
        default_value='90.0',
        description='Cancel active goal if not reached in this many seconds.',
    ),
    DeclareLaunchArgument(
        'max_goal_distance_m',
        default_value='20.0',
        description='Maximum frontier goal distance from robot in meters.',
    ),
]


def launch_setup(context, *args, **kwargs):
    setup_path = LaunchConfiguration('setup_path')
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace_arg = LaunchConfiguration('namespace')
    replan_period_sec = LaunchConfiguration('replan_period_sec')
    goal_timeout_sec = LaunchConfiguration('goal_timeout_sec')
    max_goal_distance_m = LaunchConfiguration('max_goal_distance_m')

    namespace = namespace_arg.perform(context)
    if not namespace:
        clearpath_config = ClearpathConfig(
            str(Path(setup_path.perform(context)) / 'robot.yaml')
        )
        namespace = clearpath_config.system.namespace

    tf_relay_node = Node(
        package='auto_explore_clearpath',
        executable='tf_relay_py',
        name='tf_relay',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'setup_path': setup_path,
            'namespace': namespace,
        }],
    )

    frontier_node = Node(
        package='auto_explore_clearpath',
        executable='frontier_explorer_py',
        name='frontier_explorer',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'replan_period_sec': replan_period_sec,
            'goal_timeout_sec': goal_timeout_sec,
            'max_goal_distance_m': max_goal_distance_m,
        }],
    )

    return [
        tf_relay_node,
        GroupAction([
            PushRosNamespace(namespace),
            frontier_node,
        ])
    ]


def generate_launch_description() -> LaunchDescription:
    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld
