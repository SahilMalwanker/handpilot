# ROS Interfaces

All APIs target ROS 2 Jazzy. This document describes the interfaces as
defined in source; interface compilation and runtime discovery were not
verified.

Relative names below respect a launch namespace. Single-threaded executor;
no callback blocks waiting for another service.

| Name | Type | Contract |
| --- | --- | --- |
| teleop/command | handpilot_interfaces/msg/TeleopCommand | Velocity in base_link, m/s |
| joint_states | sensor_msgs/msg/JointState | Authoritative simulated positions, rad; update velocities, rad/s |
| controller/status | handpilot_interfaces/msg/ControllerStatus | State, reason, positions, limits and command age |
| controller/set_engaged | handpilot_interfaces/srv/SetEngaged | Explicit engage or stop; never resets faults |
| controller/reset | std_srvs/srv/Trigger | FAULT to DISENGAGED only; clear command/session |

`TeleopCommand.header.stamp` is sender ROS time for observation only.
`header.frame_id` must be exactly `base_link` (no leading slash).
`source_id` is a nonempty process/session identifier, at most 128 bytes;
`sequence` is strictly increasing uint64 within that session.
`velocity_x`, `velocity_y` are finite Cartesian velocities. `active=false`
requires both exactly zero. Active zero velocity is allowed and produces no
motion. Inactive heartbeats maintain source availability, never engagement.

`ControllerStatus.state` uses named constants DISENGAGED=0, ENGAGED=1, HOLD=2,
FAULT=3. Position arrays are [x,y] in m. Joint array is [shoulder,elbow] in rad.
`limited` and `rejected` summarize events since the preceding status publication;
the reason persists until another meaningful event changes it. `command_age`
is receiver steady-clock seconds, with `command_age_valid=false` and age 0
when no accepted sample exists. Published headers use ROS clock and base_link.
JointState has the same two names, finite position and velocity, empty effort.

Command QoS: KEEP_LAST(1), BEST_EFFORT, VOLATILE at both ends. Losing one input
is preferable to processing a queue of old motion. The watchdog handles loss.
Status and joint states: KEEP_LAST(10), RELIABLE, VOLATILE, allowing standard
tools and robot_state_publisher to subscribe. Services use ROS service defaults.
No DDS durability can revive engagement. All topics have one intended producer;
never replay recorded joint states over the live state publisher.

`SetEngaged.engaged=true` requests ENGAGED with fresh accepted input and valid
state; success does not guarantee future engagement. `false` requests HOLD.
Response `success` and `message` must be checked. Reset uses the separate Trigger
service: success only in FAULT with valid configuration/joints. It discards all
input and returns DISENGAGED. See CONTROL_SPEC.md for the full transition table.

rosidl generates C++ headers such as
`handpilot_interfaces/msg/teleop_command.hpp` and types such as
`handpilot_interfaces::msg::TeleopCommand`; Python imports use
`from handpilot_interfaces.msg import TeleopCommand`. Generated files live in
build/install, not source. Source the new workspace overlay in every run terminal.

Controller parameters are startup-only/read-only: link1_length, link2_length
(m); shoulder_min/max, elbow_min/max, initial_shoulder/elbow (rad);
shoulder_max_speed, elbow_max_speed (rad/s); max_cartesian_speed (m/s);
command_timeout, max_dt (s); control_rate_hz (Hz). Invalid configuration aborts
node startup. Parameters are not a hidden live-reset interface. Launch lengths
feed both the controller and Xacro. Other defaults live in controller.yaml.
