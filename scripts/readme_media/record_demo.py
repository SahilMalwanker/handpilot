"""Drive a real controller_node through a scripted session and record its status.

Run on Ubuntu after building and sourcing the workspace:

    python3 scripts/readme_media/record_demo.py docs/media/demo_session.csv

The script starts its own controller_node in a private namespace, plays a fixed
operator script (commands before engagement, a circle, a push past the reach
limit, then silence), and writes every received ControllerStatus to CSV.
The recording is real controller output on the machine that ran it; timing
depends on that machine and is not a performance measurement.
"""

import csv
import math
import os
import signal
import subprocess
import sys
import time
import uuid

import rclpy
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy

from handpilot_interfaces.msg import ControllerStatus, TeleopCommand
from handpilot_interfaces.srv import SetEngaged

# Operator script, seconds since the first command.
ENGAGE_AT = 1.2          # commands flow before this, but nothing may move
CIRCLE_END = ENGAGE_AT + 0.3 + 2 * math.pi * 0.07 / 0.07  # one lap, r=0.07 m, v=0.07 m/s
PUSH_END = CIRCLE_END + 2.6   # drive radially outward past full reach
SILENCE_END = PUSH_END + 1.4  # stop publishing: watchdog must produce HOLD
CIRCLE_RADIUS = 0.07
CIRCLE_SPEED = 0.07
PUSH_SPEED = 0.12

FIELDS = ["t", "phase", "sent_vx", "sent_vy", "sending", "state", "reason",
          "req_x", "req_y", "ach_x", "ach_y", "q1", "q2",
          "limited", "rejected", "age_valid", "age"]


def command_for(t, achieved):
    """Return (phase, vx, vy, active, send) for script time t."""
    if t < ENGAGE_AT:
        return "pre-engage", 0.0, 0.05, True, True
    if t < ENGAGE_AT + 0.3:
        return "engage", 0.0, 0.0, True, True
    if t < CIRCLE_END:
        angle = (t - ENGAGE_AT - 0.3) * CIRCLE_SPEED / CIRCLE_RADIUS
        # Start heading left so the circle stays inside the workspace.
        return "circle", -CIRCLE_SPEED * math.cos(angle), -CIRCLE_SPEED * math.sin(angle), True, True
    if t < PUSH_END:
        norm = math.hypot(*achieved) or 1.0
        return "reach-limit", PUSH_SPEED * achieved[0] / norm, PUSH_SPEED * achieved[1] / norm, True, True
    return "silence", 0.0, 0.0, False, False


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else "demo_session.csv"
    namespace = "media_" + uuid.uuid4().hex[:8]
    env = dict(os.environ, ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST")
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    controller = subprocess.Popen(
        ["ros2", "run", "handpilot_control", "controller_node",
         "--ros-args", "-r", f"__ns:=/{namespace}"], env=env, start_new_session=True)
    rclpy.init()
    node = rclpy.create_node("media_recorder", namespace=namespace)
    rows = []
    latest = {"achieved": (0.0, 0.0)}
    clock = {"start": None, "phase": "boot", "sent": (0.0, 0.0), "sending": False}

    def on_status(message):
        if clock["start"] is None:
            return
        latest["achieved"] = tuple(message.achieved_position)
        rows.append([
            f"{time.monotonic() - clock['start']:.4f}", clock["phase"],
            f"{clock['sent'][0]:.5f}", f"{clock['sent'][1]:.5f}", int(clock["sending"]),
            message.state, message.reason,
            *(f"{v:.6f}" for v in message.requested_position),
            *(f"{v:.6f}" for v in message.achieved_position),
            *(f"{v:.6f}" for v in message.joints),
            int(message.limited), int(message.rejected),
            int(message.command_age_valid), f"{message.command_age:.4f}",
        ])

    qos = QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1,
                     reliability=ReliabilityPolicy.BEST_EFFORT,
                     durability=DurabilityPolicy.VOLATILE)
    publisher = node.create_publisher(TeleopCommand, "teleop/command", qos)
    node.create_subscription(ControllerStatus, "controller/status", on_status, 50)
    engage = node.create_client(SetEngaged, "controller/set_engaged")
    source = uuid.uuid4().hex
    sequence = 0
    try:
        if not engage.wait_for_service(timeout_sec=15.0):
            raise RuntimeError("controller did not start")
        print("controller ready; playing script", file=sys.stderr, flush=True)
        clock["start"] = time.monotonic()
        next_send = 0.0
        engage_future = None
        while True:
            t = time.monotonic() - clock["start"]
            if t > SILENCE_END:
                break
            phase, vx, vy, active, send = command_for(t, latest["achieved"])
            clock.update(phase=phase, sent=(vx, vy) if send else (0.0, 0.0), sending=send)
            if send and t >= next_send:
                sequence += 1
                message = TeleopCommand()
                message.header.stamp = node.get_clock().now().to_msg()
                message.header.frame_id = "base_link"
                message.source_id = source
                message.sequence = sequence
                message.velocity_x, message.velocity_y, message.active = vx, vy, active
                publisher.publish(message)
                next_send = t + 0.02
            if phase == "engage" and engage_future is None:
                engage_future = engage.call_async(SetEngaged.Request(engaged=True))
            rclpy.spin_once(node, timeout_sec=0.002)
        if engage_future is None or not engage_future.done() or not engage_future.result().success:
            raise RuntimeError("engagement was not confirmed; recording would be misleading")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        os.killpg(controller.pid, signal.SIGINT)
        try:
            controller.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(controller.pid, signal.SIGKILL)
    with open(output, "w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print(f"Recorded {len(rows)} status messages to {output}")


if __name__ == "__main__":
    main()
