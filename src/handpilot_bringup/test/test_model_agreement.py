"""Full-launch check that the URDF/TF model agrees with the controller's kinematics.

Launches handpilot.launch.py with non-default link lengths, then compares the
base_link -> tool_link transform from robot_state_publisher with the controller's
achieved position and with FK computed here from the published joints. It checks
both the startup pose and a pose reached after real engaged motion.
"""

import math
import os
import time
import unittest
import uuid

from ament_index_python.packages import get_package_share_directory
import launch
from launch.launch_description_sources import PythonLaunchDescriptionSource
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.time import Time
from tf2_msgs.msg import TFMessage
import tf2_ros

from handpilot_interfaces.msg import ControllerStatus, TeleopCommand
from handpilot_interfaces.srv import SetEngaged

LINK1, LINK2 = 0.35, 0.20
TOLERANCE = 1e-6


@pytest.mark.launch_test
def generate_test_description():
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    namespace = "model_" + uuid.uuid4().hex[:10]
    bringup = launch.actions.IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("handpilot_bringup"), "launch", "handpilot.launch.py")),
        launch_arguments={"namespace": namespace, "link1_length": str(LINK1),
                          "link2_length": str(LINK2)}.items(),
    )
    return launch.LaunchDescription([bringup, launch_testing.actions.ReadyToTest()]), {
        "namespace": namespace}


def fk(joints):
    q1, q2 = joints
    return (LINK1 * math.cos(q1) + LINK2 * math.cos(q1 + q2),
            LINK1 * math.sin(q1) + LINK2 * math.sin(q1 + q2))


class TestModelAgreement(unittest.TestCase):
    def test_tf_matches_controller_kinematics(self, namespace):
        rclpy.init()
        node = rclpy.create_node("model_probe", namespace=namespace)
        buffer = tf2_ros.Buffer()
        self.status = None
        # The launch remaps TF into the namespace, so feed the buffer directly.
        node.create_subscription(TFMessage, "tf", lambda m: [
            buffer.set_transform(t, "probe") for t in m.transforms], 50)
        static_qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=10,
                                reliability=ReliabilityPolicy.RELIABLE,
                                durability=DurabilityPolicy.TRANSIENT_LOCAL)
        node.create_subscription(TFMessage, "tf_static", lambda m: [
            buffer.set_transform_static(t, "probe") for t in m.transforms], static_qos)
        node.create_subscription(ControllerStatus, "controller/status",
                                 lambda m: setattr(self, "status", m), 10)
        command_qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                                 reliability=ReliabilityPolicy.BEST_EFFORT,
                                 durability=DurabilityPolicy.VOLATILE)
        publisher = node.create_publisher(TeleopCommand, "teleop/command", command_qos)
        engage = node.create_client(SetEngaged, "controller/set_engaged")
        source, sequence = uuid.uuid4().hex, [0]

        def send(vx, vy, active=True):
            sequence[0] += 1
            message = TeleopCommand()
            message.header.frame_id = "base_link"
            message.source_id = source
            message.sequence = sequence[0]
            message.velocity_x, message.velocity_y, message.active = vx, vy, active
            publisher.publish(message)

        def spin(seconds, command=None):
            finish = time.monotonic() + seconds
            while time.monotonic() < finish:
                if command:
                    send(*command)
                rclpy.spin_once(node, timeout_sec=0.02)

        def compare(label):
            joints = tuple(self.status.joints)
            spin(0.3)  # let TF catch up with these frozen joints
            self.assertEqual(tuple(self.status.joints), joints, f"{label}: joints still moving")
            tool = buffer.lookup_transform("base_link", "tool_link", Time()).transform.translation
            expected = fk(joints)
            achieved = tuple(self.status.achieved_position)
            for axis, (tf_value, fk_value, ctrl_value) in enumerate(
                    zip((tool.x, tool.y), expected, achieved)):
                self.assertAlmostEqual(tf_value, fk_value, delta=TOLERANCE, msg=f"{label} axis {axis}")
                self.assertAlmostEqual(ctrl_value, fk_value, delta=TOLERANCE, msg=f"{label} axis {axis}")
            self.assertAlmostEqual(tool.z, 0.0, delta=TOLERANCE)
            return joints

        try:
            self.assertTrue(engage.wait_for_service(timeout_sec=15.0))
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline and not (
                    self.status is not None and buffer.can_transform("base_link", "tool_link", Time())):
                rclpy.spin_once(node, timeout_sec=0.05)
            self.assertIsNotNone(self.status, "no controller status")
            start = compare("startup pose")
            self.assertAlmostEqual(start[0], 0.4, delta=TOLERANCE)

            spin(0.2, (0.0, 0.0))
            future = engage.call_async(SetEngaged.Request(engaged=True))
            while not future.done():
                send(0.0, 0.0)
                rclpy.spin_once(node, timeout_sec=0.02)
            self.assertTrue(future.result().success, future.result().message)
            spin(1.5, (-0.08, -0.04))
            spin(0.6)  # silence -> watchdog HOLD freezes the joints
            self.assertEqual(self.status.state, ControllerStatus.HOLD)
            moved = compare("after motion")
            self.assertGreater(math.dist(moved, start), 0.05, "arm did not move")
        finally:
            node.destroy_node()
            rclpy.shutdown()


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):
    def test_processes_exit_cleanly(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info, allowable_exit_codes=[0])
