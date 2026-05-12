from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode, Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config = PathJoinSubstitution([
        FindPackageShare("fusioncore_husky"), "config", "husky_fusioncore.yaml"
    ])

    use_sim_time = LaunchConfiguration("use_sim_time", default="false")

    fc = LifecycleNode(
        package="fusioncore_ros",
        executable="fusioncore_node",
        name="fusioncore",
        namespace="",
        output="screen",
        parameters=[config, {"use_sim_time": use_sim_time}],
        remappings=[
            ("/odom/wheels", "/husky_velocity_controller/odom"),
            ("/gnss/fix",    "/fix"),
        ],
    )

    lm = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_fusioncore",
        output="screen",
        parameters=[{
            "autostart": True,
            "node_names": ["fusioncore"],
            "use_sim_time": use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        fc,
        lm,
    ])
