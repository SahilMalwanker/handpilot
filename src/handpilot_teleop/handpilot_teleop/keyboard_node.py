from contextlib import contextmanager
from dataclasses import dataclass
import math
import os
import select
import sys
import time
import uuid


@dataclass(frozen=True)
class KeyAction:
    kind: str
    velocity_x: float = 0.0
    velocity_y: float = 0.0


def map_key(key: str, speed: float) -> KeyAction:
    if not math.isfinite(speed) or not 0.0 < speed <= 10.0:
        raise ValueError("speed must be finite and in (0, 10] m/s")
    return {
        "w": KeyAction("motion", 0.0, speed),
        "s": KeyAction("motion", 0.0, -speed),
        "a": KeyAction("motion", -speed, 0.0),
        "d": KeyAction("motion", speed, 0.0),
        "e": KeyAction("engage"),
        " ": KeyAction("stop"),
        "r": KeyAction("reset"),
        "q": KeyAction("quit"),
    }.get(key, KeyAction("ignore"))


class MotionWindow:
    def __init__(self, validity: float):
        if not math.isfinite(validity) or not 0.05 <= validity <= 1.0:
            raise ValueError("motion_validity must be 0.05..1.0 s")
        self.validity = validity
        self.clear()

    def clear(self):
        self.started_at = None
        self.deadline = None
        self.velocity = (0.0, 0.0)

    def apply(self, action: KeyAction, now: float):
        if not math.isfinite(now):
            self.clear()
            return
        if action.kind in ("motion", "engage"):
            self.velocity = (action.velocity_x, action.velocity_y)
            self.started_at = now
            self.deadline = now + self.validity
        elif action.kind in ("stop", "reset", "quit"):
            self.clear()

    def sample(self, now: float) -> tuple[float, float, bool]:
        if (not math.isfinite(now) or self.started_at is None or self.deadline is None
                or now >= self.deadline or now < self.started_at):
            self.clear()
            return 0.0, 0.0, False
        return *self.velocity, True


@contextmanager
def terminal_mode(stream):
    import termios
    import tty

    if not stream.isatty():
        raise RuntimeError("keyboard_node requires an interactive Linux terminal")
    descriptor = stream.fileno()
    saved = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSANOW, saved)


def create_keyboard_node():
    from rcl_interfaces.msg import ParameterDescriptor
    from rclpy.node import Node
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
    from std_srvs.srv import Trigger
    from handpilot_interfaces.msg import TeleopCommand
    from handpilot_interfaces.srv import SetEngaged

    class KeyboardNode(Node):
        def __init__(self):
            super().__init__("handpilot_keyboard")
            descriptor = ParameterDescriptor(read_only=True)
            self.speed = self.declare_parameter("speed", 0.06, descriptor).value
            validity = self.declare_parameter("motion_validity", 0.35, descriptor).value
            rate = self.declare_parameter("publish_rate_hz", 50.0, descriptor).value
            map_key("", self.speed)
            if not math.isfinite(rate) or not 10.0 <= rate <= 100.0:
                raise ValueError("publish_rate_hz must be 10..100")
            self.window = MotionWindow(validity)
            self.source = uuid.uuid4().hex
            self.sequence = 0
            self.pending = None
            self.pending_kind = None
            self.stop_queued = False
            qos = QoSProfile(
                history=HistoryPolicy.KEEP_LAST, depth=1,
                reliability=ReliabilityPolicy.BEST_EFFORT,
                durability=DurabilityPolicy.VOLATILE,
            )
            self.publisher = self.create_publisher(TeleopCommand, "teleop/command", qos)
            self.engage_client = self.create_client(SetEngaged, "controller/set_engaged")
            self.reset_client = self.create_client(Trigger, "controller/reset")
            self.create_timer(1.0 / rate, self.publish_command)

        def publish_command(self):
            if self.sequence == (1 << 64) - 1:
                raise RuntimeError("sequence exhausted; restart to obtain a new session")
            self.sequence += 1
            message = TeleopCommand()
            message.header.stamp = self.get_clock().now().to_msg()
            message.header.frame_id = "base_link"
            message.source_id = self.source
            message.sequence = self.sequence
            message.velocity_x, message.velocity_y, message.active = self.window.sample(time.monotonic())
            self.publisher.publish(message)

        def request(self, kind):
            if kind == "stop":
                self.window.clear()
                self.publish_command()
                self.stop_queued = True
            if self.pending is not None:
                if kind != "stop":
                    self.get_logger().warning("Service request pending; repeat the key after its response")
                return
            if self.stop_queued:
                kind = "stop"
            client = self.reset_client if kind == "reset" else self.engage_client
            if not client.service_is_ready():
                self.get_logger().warning("Controller service unavailable; motion remains bounded by timeout")
                return
            request = Trigger.Request() if kind == "reset" else SetEngaged.Request(engaged=kind == "engage")
            self.pending = client.call_async(request)
            self.pending_kind = kind
            if kind == "stop":
                self.stop_queued = False

        def service_progress(self):
            if self.pending is not None and self.pending.done():
                future = self.pending
                self.pending = None
                self.pending_kind = None
                try:
                    response = future.result()
                    if response is None or not response.success:
                        self.window.clear()
                    self.get_logger().info(response.message if response else "No service response")
                except Exception as error:
                    self.window.clear()
                    self.get_logger().error(f"Service failed: {error}")
            if self.stop_queued and self.pending is None and self.engage_client.service_is_ready():
                self.request("stop")

        def handle_key(self, key):
            action = map_key(key, self.speed)
            if action.kind in ("motion", "engage") and (self.stop_queued or self.pending_kind == "stop"):
                return True
            self.window.apply(action, time.monotonic())
            if action.kind == "engage":
                self.publish_command()
                self.request("engage")
            elif action.kind in ("stop", "reset"):
                self.publish_command()
                self.request(action.kind)
            elif action.kind == "quit":
                self.request("stop")
                return False
            return True

    return KeyboardNode()


def main(args=None):
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.signals import SignalHandlerOptions

    node = None
    # Ctrl-C raises KeyboardInterrupt so the stop request is sent before ROS shutdown.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.SIGTERM)
    try:
        if not sys.stdin.isatty():
            raise RuntimeError("Use ros2 run in a separate interactive SSH terminal")
        node = create_keyboard_node()
        print("w/a/s/d: velocity pulse | e: engage | Space: HOLD | r: reset | q: quit")
        print("Terminal repeats are not a held-key deadman. Motion pulses expire.")
        with terminal_mode(sys.stdin):
            while rclpy.ok():
                rclpy.spin_once(node, timeout_sec=0.01)
                node.service_progress()
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    data = os.read(sys.stdin.fileno(), 1)
                    if not data or not node.handle_key(data.decode("ascii", errors="ignore")):
                        break
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            try:
                if rclpy.ok():
                    node.request("stop")
                    deadline = time.monotonic() + 0.25
                    while rclpy.ok() and time.monotonic() < deadline:
                        node.service_progress()
                        if node.pending is None and not node.stop_queued:
                            break
                        rclpy.spin_once(node, timeout_sec=0.01)
            except (KeyboardInterrupt, ExternalShutdownException):
                pass
            finally:
                node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
