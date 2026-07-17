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

"""Launch SLAM, Nav2, and frontier exploration for autonomous mapping."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

ARGUMENTS = [
    DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
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
        'scan_topic',
        default_value='',
        description='Optional override for 2D scan topic.',
    ),
    DeclareLaunchArgument(
        'max_goal_distance_m',
        default_value='20.0',
        description='Maximum frontier goal distance from robot in meters.',
    ),
]


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration('use_sim_time')
    setup_path = LaunchConfiguration('setup_path')
    namespace = LaunchConfiguration('namespace')
    scan_topic = LaunchConfiguration('scan_topic')
    max_goal_distance_m = LaunchConfiguration('max_goal_distance_m')

    nav2_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('clearpath_nav2_demos'),
                'launch',
                'slam.launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'setup_path': setup_path,
            'scan_topic': scan_topic,
        }.items(),
    )

    nav2_navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('clearpath_nav2_demos'),
                'launch',
                'nav2.launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'setup_path': setup_path,
            'scan_topic': scan_topic,
        }.items(),
    )

    explorer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('auto_explore_clearpath'),
                'launch',
                'auto_explore.launch.py',
            ])
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'setup_path': setup_path,
            'namespace': namespace,
            'max_goal_distance_m': max_goal_distance_m,
        }.items(),
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(nav2_slam)
    ld.add_action(nav2_navigation)
    ld.add_action(explorer)
    return ld
