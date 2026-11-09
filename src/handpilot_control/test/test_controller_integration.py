import math
import os
import time
import unittest
import uuid

import launch
import launch_ros.actions
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger

from handpilot_interfaces.msg import ControllerStatus, TeleopCommand
from handpilot_interfaces.srv import SetEngaged


@pytest.mark.launch_test
def generate_test_description():
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    namespace = "test_" + uuid.uuid4().hex[:12]
    controller = launch_ros.actions.Node(
        package="handpilot_control", executable="controller_node",
        namespace=namespace, output="screen",
    )
    return launch.LaunchDescription([
        controller, launch_testing.actions.ReadyToTest(),
    ]), {"controller": controller, "namespace": namespace}


class TestController(unittest.TestCase):
    def test_vertical_slice(self, namespace):
        rclpy.init()
        self.node = rclpy.create_node("probe", namespace=namespace)
        self.status = None
        self.joint_messages = []
        self.status_count = 0
        self.sequence = 0
        self.active = False
        self.frame = "base_link"
        self.source = uuid.uuid4().hex
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST, depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.publisher = self.node.create_publisher(TeleopCommand, "teleop/command", qos)
        self.node.create_subscription(ControllerStatus, "controller/status", self.on_status, 10)
        self.node.create_subscription(JointState, "joint_states", self.joint_messages.append, 10)
        self.engage = self.node.create_client(SetEngaged, "controller/set_engaged")
        self.reset = self.node.create_client(Trigger, "controller/reset")
        try:
            self.assertTrue(self.engage.wait_for_service(timeout_sec=10.0))
            self.assertTrue(self.reset.wait_for_service(timeout_sec=10.0))
            self.wait_for(lambda: self.status is not None and bool(self.joint_messages))
            self.assertEqual(self.status.state, ControllerStatus.DISENGAGED)
            self.assertFalse(self.status.command_age_valid)
            self.wait_for(lambda: self.status.command_age_valid, heartbeat=True)
            self.active = True
            self.service(self.engage, SetEngaged.Request(engaged=True), heartbeat=True)
            baseline = tuple(self.status.joints)
            self.wait_for(
                lambda: max(abs(value - old) for value, old in zip(self.status.joints, baseline)) > 1e-4,
                heartbeat=True,
            )
            self.assertEqual(self.status.state, ControllerStatus.ENGAGED)
            self.active = False
            self.wait_for(lambda: self.status.state == ControllerStatus.HOLD, heartbeat=True)
            held = tuple(self.status.joints)
            self.active = True
            self.observe(0.15, heartbeat=True)
            self.assertEqual(self.status.state, ControllerStatus.HOLD)
            self.assertEqual(tuple(self.status.joints), held)
            self.service(self.engage, SetEngaged.Request(engaged=True), heartbeat=True)
            self.wait_for(lambda: self.status.state == ControllerStatus.ENGAGED, heartbeat=True)
            self.wait_for(lambda: self.status.state == ControllerStatus.HOLD)
            self.assertIn("timeout", self.status.reason)
            held = tuple(self.status.joints)
            self.observe(0.15, heartbeat=True)
            self.assertEqual(self.status.state, ControllerStatus.HOLD)
            self.assertEqual(tuple(self.status.joints), held)
            self.frame = "wrong_frame"
            self.wait_for(lambda: self.status.state == ControllerStatus.FAULT, heartbeat=True)
            self.frame = "base_link"
            count = self.status_count
            self.wait_for(lambda: self.status_count > count + 2)
            self.assertEqual(tuple(self.status.joints), held)
            response = self.service(self.engage, SetEngaged.Request(engaged=True), expect=False)
            self.assertIn("reset", response.message)
            self.service(self.reset, Trigger.Request())
            self.wait_for(lambda: self.status.state == ControllerStatus.DISENGAGED)
            for message in self.joint_messages:
                self.assertEqual(message.name, ["shoulder_joint", "elbow_joint"])
                self.assertEqual(len(message.position), 2)
                self.assertEqual(len(message.velocity), 2)
                self.assertTrue(all(math.isfinite(value) for value in message.position + message.velocity))
                self.assertTrue(all(-2.8 <= value <= 2.8 for value in message.position))
                self.assertTrue(all(abs(value) <= 0.8 + 1e-8 for value in message.velocity))
        finally:
            self.node.destroy_node()
            rclpy.shutdown()

    def on_status(self, message):
        self.status = message
        self.status_count += 1

    def send(self):
        self.sequence += 1
        message = TeleopCommand()
        message.header.stamp = self.node.get_clock().now().to_msg()
        message.header.frame_id = self.frame
        message.source_id = self.source
        message.sequence = self.sequence
        message.active = self.active
        message.velocity_x = 0.04 if self.active else 0.0
        self.publisher.publish(message)

    def wait_for(self, predicate, timeout=5.0, heartbeat=False):
        deadline = time.monotonic() + timeout
        next_send = 0.0
        while time.monotonic() < deadline:
            if heartbeat and time.monotonic() >= next_send:
                self.send()
                next_send = time.monotonic() + 0.02
            rclpy.spin_once(self.node, timeout_sec=0.01)
            if predicate():
                return
        self.fail(f"Timed out; last status: {self.status}")

    def observe(self, duration, heartbeat=False):
        finish = time.monotonic() + duration
        self.wait_for(lambda: time.monotonic() >= finish, duration + 1.0, heartbeat)

    def service(self, client, request, heartbeat=False, expect=True):
        future = client.call_async(request)
        self.wait_for(future.done, heartbeat=heartbeat)
        response = future.result()
        self.assertIsNotNone(response)
        self.assertEqual(response.success, expect, response.message)
        return response


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):
    def test_clean_exit(self, proc_info, controller):
        launch_testing.asserts.assertExitCodes(
            proc_info,
            process=controller,
            allowable_exit_codes=[0],
        )
