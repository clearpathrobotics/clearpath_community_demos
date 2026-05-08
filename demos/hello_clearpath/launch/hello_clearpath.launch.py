"""
Launch the C++ or Python hello_square node.

The default is the C++ implementation. Pass ``language:=python`` to launch the
Python version instead. The launched node is pushed under the namespace
declared in the robot's ``robot.yaml`` (read from ``setup_path``), and
``use_sim_time`` is forwarded so the demo behaves correctly in simulation.
"""

import os

from clearpath_config.clearpath_config import ClearpathConfig
from launch_ros.actions import Node, PushRosNamespace

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression

ARGUMENTS = [
    DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        choices=['true', 'false'],
        description='Use simulation (Gazebo) clock if true.',
    ),
    DeclareLaunchArgument(
        'setup_path',
        default_value='/etc/clearpath/',
        description='Clearpath setup path containing robot.yaml.',
    ),
    DeclareLaunchArgument(
        'language',
        default_value='cpp',
        choices=['cpp', 'python'],
        description='Which implementation to launch: "cpp" (default) or "python".',
    ),
]


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    setup_path = LaunchConfiguration('setup_path')
    language = LaunchConfiguration('language')

    # Parse robot YAML and resolve the namespace from it.
    clearpath_config = ClearpathConfig(
        os.path.join(str(setup_path.perform(context)), 'robot.yaml'))
    namespace = clearpath_config.system.namespace

    cpp_node = Node(
        package='hello_clearpath',
        executable='hello_square_cpp',
        name='hello_square',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(PythonExpression(["'", language, "' == 'cpp'"])),
    )

    py_node = Node(
        package='hello_clearpath',
        executable='hello_square_py',
        name='hello_square',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(PythonExpression(["'", language, "' == 'python'"])),
    )

    return [
        GroupAction([
            PushRosNamespace(namespace),
            cpp_node,
            py_node,
        ]),
    ]


def generate_launch_description() -> LaunchDescription:
    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(OpaqueFunction(function=launch_setup))
    return ld
