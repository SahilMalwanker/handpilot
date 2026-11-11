from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("port", default_value="8765"),
        Node(
            package="foxglove_bridge", executable="foxglove_bridge", output="screen",
            parameters=[{
                "address": "127.0.0.1",
                "port": ParameterValue(LaunchConfiguration("port"), value_type=int),
            }],
        ),
    ])
