# Run And Debug

Commands are for the Ubuntu target after metadata completion and a successful
build. NOT RUN here. Every terminal first sources:

```bash
source /opt/ros/jazzy/setup.bash
source ~/handpilot/install/setup.bash
```

## Three Terminals

Controller/model terminal:

```bash
ros2 launch handpilot_bringup handpilot.launch.py
```

Interactive input terminal:

```bash
ros2 run handpilot_teleop keyboard_node
```

Inspection terminal:

```bash
ros2 topic echo /controller/status
```

`e`, then a direction key within the short active-zero window; service success is
printed. The controller still requires a directional message after engagement.
An inactive heartbeat stops engagement. `w/s` are +/-Y, `a/d` are -/+X, Space is
HOLD, `r` is explicit fault reset, `q` attempts a stop then exits. After HOLD or
reset, `e` is needed again. Repeated direction alone never re-engages.

Terminal autorepeat starts after an OS-configured delay and may repeat faster
than fresh physical presses. Default pulse validity 0.35 s may expire during
that initial delay. Try deliberate taps first. Tuning is an explicit tradeoff:

```bash
ros2 run handpilot_teleop keyboard_node --ros-args -p speed:=0.04 -p motion_validity:=0.5
```

Longer validity sustains motion longer after the last processed key. It is not
a held-key deadman or hardware stop. Queued terminal characters, SSH delays, VM
pauses, and transport delay can postpone observation. The controller separately
enforces its 0.25 s receiver-side watchdog. Do not describe either as certified.

## Introspection

```bash
ros2 node list
ros2 node info /handpilot_controller
ros2 topic info /teleop/command --verbose
ros2 interface show handpilot_interfaces/msg/TeleopCommand
ros2 topic echo /joint_states --once
ros2 param dump /handpilot_controller
ros2 service call /controller/set_engaged handpilot_interfaces/srv/SetEngaged "{engaged: false}"
ros2 service call /controller/reset std_srvs/srv/Trigger "{}"
```

Reset succeeds only in FAULT. Check response success/message and current status.
Parameters are startup-only: restart with reviewed parameters, not live mutation.
Rejecting wrong frame/non-finite input leads to FAULT while leaving the node alive.
Duplicate sequence leads to HOLD if engaged; unreachable velocity steps are
rejected while ENGAGED without accumulating target error.

Check status.reason, command_age_valid, command_age, limited, and rejected.
Event flags can be missed by sparse echo sampling; recording captures more of the
stream. Service success does not override a subsequent inactive heartbeat.
Topics and services have no guaranteed cross-channel delivery order.

To deliberately request a frame fault with teleop stopped, on Ubuntu:

```bash
ros2 topic pub --once /teleop/command handpilot_interfaces/msg/TeleopCommand \
	'{header: {frame_id: wrong_frame}, source_id: manual-test, sequence: 1, velocity_x: 0.0, velocity_y: 0.0, active: false}'
```

Expected example, not an observed result: FAULT with a frame reason and continued
status publication. Correct the source, reset, then explicitly engage with fresh
input. A repeating CLI publisher with a fixed sequence is not a valid live source.

For one namespaced instance:

```bash
ros2 launch handpilot_bringup handpilot.launch.py namespace:=practice
ros2 run handpilot_teleop keyboard_node --ros-args -r __ns:=/practice
ros2 topic echo /practice/controller/status
```

The first two commands belong in separate terminals. TF topics also move under
the namespace; remap a TF tool's /tf and /tf_static accordingly. Frame IDs remain
unchanged; combining multiple arms in one TF tree is out of scope.

## Deliberate Failure Exercises

Stop teleop with Ctrl-C or, from another Ubuntu terminal after identifying its
specific PID with `pgrep -af keyboard_node`, send `kill -TERM <PID>`. Do not kill
unrelated processes. The controller should reach HOLD; inspect the reason and
verify joint positions no longer change. Ctrl-C is intended to send an explicit
HOLD request before ROS shutdown. SIGTERM shuts down ROS first, so expect a
watchdog/inactive HOLD instead; both paths should restore the terminal. Hard-kill testing is separate: SIGKILL
cannot run terminal cleanup. Use `stty sane` in the affected terminal if needed.

To study unreachable input, first add/run a core test with a full-extension pose
and outward velocity. ROS input is velocity, so there is no absolute-position
command to send. A deliberate Ubuntu-only controller exercise can start a
standalone controller at q=[0,0] (no bringup simultaneously), then engage and
request +X. Inspect `rejected` and compare requested versus achieved. This is
an exercise configuration, not the normal away-from-extension startup.

For build errors retain the first compiler error, package name, command, and
environment. A Debug build can be requested with `--cmake-args -DCMAKE_BUILD_TYPE=Debug`.
Do not hide errors by disabling tests or replacing real integration with mocks.
Ctrl-C should stop launch processes; shutdown behavior still requires target testing.
