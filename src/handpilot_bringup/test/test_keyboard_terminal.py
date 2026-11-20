"""Drive the real keyboard_node through a pseudo-terminal against a real controller.

Checks what the unit tests cannot: cbreak terminal handling, real key bytes,
pulse expiry over the ROS graph, the stop on 'q' and on Ctrl-C, and that the
terminal settings are restored when the node exits.
"""

import fcntl
import os
import select
import subprocess
import termios
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

from handpilot_interfaces.msg import ControllerStatus


@pytest.mark.launch_test
def generate_test_description():
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    namespace = "keys_" + uuid.uuid4().hex[:10]
    controller = launch_ros.actions.Node(
        package="handpilot_control", executable="controller_node",
        namespace=namespace, output="screen")
    return launch.LaunchDescription([controller, launch_testing.actions.ReadyToTest()]), {
        "namespace": namespace, "controller": controller}


class Terminal:
    """keyboard_node attached to a pseudo-terminal as its controlling terminal."""

    def __init__(self, namespace):
        self.master, self.slave = os.openpty()
        self.saved = termios.tcgetattr(self.slave)
        slave = self.slave

        def attach():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

        self.process = subprocess.Popen(
            ["ros2", "run", "handpilot_teleop", "keyboard_node",
             "--ros-args", "-r", f"__ns:=/{namespace}"],
            stdin=slave, stdout=slave, stderr=slave, preexec_fn=attach, close_fds=True)
        self.output = b""

    def drain(self):
        while select.select([self.master], [], [], 0)[0]:
            try:
                chunk = os.read(self.master, 4096)
            except OSError:
                return
            if not chunk:
                return
            self.output += chunk

    def press(self, key):
        os.write(self.master, key.encode())

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=5)
        os.close(self.master)
        os.close(self.slave)


class TestKeyboardTerminal(unittest.TestCase):
    def setUp(self):
        rclpy.init()

    def tearDown(self):
        rclpy.shutdown()

    def run_session(self, namespace, finish_key):
        node = rclpy.create_node("keys_probe", namespace=namespace)
        status = {}
        node.create_subscription(ControllerStatus, "controller/status",
                                 lambda m: status.__setitem__("last", m), 10)
        terminal = Terminal(namespace)

        def wait_for(predicate, timeout, keys=None, period=0.1):
            deadline, next_key = time.monotonic() + timeout, 0.0
            while time.monotonic() < deadline:
                if keys and time.monotonic() >= next_key:
                    terminal.press(keys)
                    next_key = time.monotonic() + period
                rclpy.spin_once(node, timeout_sec=0.02)
                terminal.drain()
                if "last" in status and predicate(status["last"]):
                    return status["last"]
            self.fail(f"timeout; last status {status.get('last')}; terminal output:\n"
                      f"{terminal.output.decode(errors='replace')}")

        try:
            wait_for(lambda s: b"w/a/s/d" in terminal.output, 20.0)
            start = tuple(wait_for(lambda s: True, 5.0).joints)
            # Engage with retries: the first 'e' may arrive before discovery completes.
            wait_for(lambda s: s.state == ControllerStatus.ENGAGED, 10.0, keys="e", period=0.5)
            # A held key: repeated 'w' faster than the 0.35 s pulse keeps it moving.
            moved = wait_for(lambda s: s.achieved_position[1] > 0.0, 0.0 + 3.0, keys="w")
            wait_for(lambda s: abs(s.joints[0] - start[0]) > 0.02, 3.0, keys="w")
            self.assertEqual(moved.state, ControllerStatus.ENGAGED)
            # Releasing the key: the pulse expires and inactive input stops motion.
            held = wait_for(lambda s: s.state == ControllerStatus.HOLD, 2.0)
            self.assertIn("inactive", held.reason)
            # Re-engage, then leave via finish_key while engaged.
            wait_for(lambda s: s.state == ControllerStatus.ENGAGED, 10.0, keys="e", period=0.5)
            terminal.press(finish_key)
            wait_for(lambda s: s.state == ControllerStatus.HOLD, 3.0)
            terminal.process.wait(timeout=10)
            # The explicit stop service, not only the heartbeat, must have landed.
            stopped = wait_for(lambda s: s.reason == "explicit disengage", 2.0)
            terminal.drain()
            restored = termios.tcgetattr(terminal.slave)
            self.assertEqual(restored[3] & (termios.ICANON | termios.ECHO),
                             terminal.saved[3] & (termios.ICANON | termios.ECHO),
                             "terminal not restored to canonical echo mode")
            return stopped, terminal.process.returncode
        finally:
            terminal.close()
            node.destroy_node()

    def test_keys_move_then_q_stops(self, namespace):
        stopped, code = self.run_session(namespace, "q")
        self.assertEqual(code, 0)
        self.assertEqual(stopped.state, ControllerStatus.HOLD)

    def test_ctrl_c_stops(self, namespace):
        stopped, _ = self.run_session(namespace, "\x03")
        self.assertEqual(stopped.state, ControllerStatus.HOLD)


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):
    def test_controller_exit(self, proc_info, controller):
        launch_testing.asserts.assertExitCodes(proc_info, process=controller,
                                               allowable_exit_codes=[0])
