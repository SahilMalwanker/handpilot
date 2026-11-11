from pathlib import Path
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory("handpilot_bringup"))
    model = Path(get_package_share_directory("handpilot_description")) / "urdf" / "planar_arm.urdf.xacro"
    config_path = share / "config" / "controller.yaml"
    with config_path.open(encoding="utf-8") as stream:
        defaults = yaml.safe_load(stream)["/**"]["ros__parameters"]
    namespace = LaunchConfiguration("namespace")
    length1 = LaunchConfiguration("link1_length")
    length2 = LaunchConfiguration("link2_length")
    xacro_command = [FindExecutable(name="xacro"), " ", str(model),
                     " link1_length:=", length1, " link2_length:=", length2]
    for name in ("shoulder_min", "shoulder_max", "elbow_min", "elbow_max",
                 "shoulder_max_speed", "elbow_max_speed"):
        xacro_command.extend([f" {name}:=", str(defaults[name])])
    controller = Node(
        package="handpilot_control", executable="controller_node",
        name="handpilot_controller", namespace=namespace, output="screen",
        parameters=[str(config_path), {
            "link1_length": ParameterValue(length1, value_type=float),
            "link2_length": ParameterValue(length2, value_type=float),
        }],
    )
    state_publisher = Node(
        package="robot_state_publisher", executable="robot_state_publisher",
        namespace=namespace, output="screen",
        parameters=[{"robot_description": ParameterValue(Command(xacro_command), value_type=str)}],
        remappings=[("/tf", "tf"), ("/tf_static", "tf_static")],
    )
    return LaunchDescription([
        DeclareLaunchArgument("namespace", default_value=""),
        DeclareLaunchArgument("link1_length", default_value=str(defaults["link1_length"])),
        DeclareLaunchArgument("link2_length", default_value=str(defaults["link2_length"])),
        RegisterEventHandler(OnProcessExit(
            target_action=controller,
            on_exit=[EmitEvent(event=Shutdown(reason="Controller exited"))],
        )),
        RegisterEventHandler(OnProcessExit(
            target_action=state_publisher,
            on_exit=[EmitEvent(event=Shutdown(reason="Robot state publisher exited"))],
        )),
        controller,
        state_publisher,
    ])
