# Validation Status

Source was authored on 2026-10-19 on a separate workstation with no toolchain.
Everything marked PASSED below was executed afterwards on the target VM.
Rows still marked NOT RUN have no evidence yet. No measured performance exists.

## Execution Environment

| Item | Value |
| --- | --- |
| Machine | UTM VM on Apple M2, 2 vCPU, ~3 GB RAM |
| Architecture | aarch64 |
| OS | Ubuntu 24.04.5 LTS |
| ROS | Jazzy, `rmw_fastrtps_cpp` (default RMW) |
| Compiler / Python | GCC 13.3.0 / Python 3.12.3 |
| Source revision | `d47f804` plus the test and CI changes in this update |

## Results

Build command: `CMAKE_BUILD_PARALLEL_LEVEL=2 colcon build --symlink-install --executor sequential`
Test commands: `colcon test --executor sequential` then `colcon test-result --verbose`

| Requirement | Build | Runtime / tests | Evidence |
| --- | --- | --- | --- |
| Package metadata and discovery (6 packages) | PASSED | n/a | colcon build, 0 compiler warnings with `-Wall -Wextra -Wpedantic` |
| rosidl C++/Python messages and services | PASSED | PASSED | used by the controller (C++) and by teleop/tests (Python) |
| Pure C++ FK/IK/Jacobian | PASSED | PASSED | `test_kinematics`: 6 gtests |
| Cartesian, joint-position and joint-rate limits | PASSED | PASSED | `test_constraints`: 4 gtests |
| HOLD, engagement, session, sequence and fault reset | PASSED | PASSED | `test_controller`: 13 gtests |
| Keyboard mapping and pulse expiry (pure classes) | PASSED | PASSED | `test_keyboard_mapping.py`: 21 pytest cases |
| launch_testing integration and clean shutdown | PASSED | PASSED | `test_controller_integration.py`: 2 tests (vertical slice, clean exit) |
| Real controller session (engage, motion, reach limit, watchdog) | PASSED | PASSED | `docs/media/demo_session.csv`, see below |
| Source hygiene inspector | n/a | PASSED, 0 errors | `python3 scripts/inspect_source.py`; 0 warnings after the Apache-2.0 license was set |
| Keyboard node in a real terminal (cbreak, keys, `q`, Ctrl-C, restore) | PASSED | PASSED | `test_keyboard_terminal.py`: real keyboard_node on a pseudo-terminal, 3 tests, stable over 3 repeated runs |
| Xacro, launch-shared link lengths, TF vs FK agreement | PASSED | PASSED | `test_model_agreement.py`: full launch with 0.35/0.20 m links; TF `tool_link` = FK = controller within 1e-6 m, at startup and after motion. Fails (46 mm error) if the launch stops passing a length to Xacro |
| Optional Foxglove bridge launch | n/a | PASSED (server) | `visualization.launch.py` listens on 127.0.0.1:8765 on ARM64; a desktop client connection is NOT RUN |
| Recording/replay procedure | n/a | PASSED | RECORD_AND_REPLAY steps run, see below |
| GitHub Actions CI (x86_64) | PASSED | PASSED | run 44647686217 on `f42082a`, ubuntu-24.04 runner: all 57 test results (51 cases) pass. The first run failed because `set -u` broke sourcing ROS; fixed in the workflow |
| Webcam/rosbridge adapter | NO, planned | NOT RUN | CAMERA_INTEGRATION_PLAN only |
| Performance/latency/memory measurements | NO | NOT RUN | no benchmark claims |

Total: 51 test cases, 0 failures. `colcon test-result` reports 57 because it also
counts six CTest wrapper entries.

## Recorded Controller Session

`scripts/readme_media/record_demo.py` starts a real `controller_node` in a private
namespace, plays a fixed operator script, and records every `controller/status`
message (591 samples). Observed transitions:

| Time (s) | Operator action | Observed state and reason |
| --- | --- | --- |
| 0.00 | Active velocity commands, no engage | DISENGAGED; joints unchanged |
| 1.21 | `set_engaged(true)` | ENGAGED, "explicit engagement; awaiting input"; no jump |
| 1.51 | Circle, r = 0.07 m at 0.07 m/s | ENGAGED, "tracking velocity" |
| 7.81 | Push radially outward at 0.12 m/s | "motion limited" (joint rate limit), then "outside radial workspace" (IK rejection) |
| 8.85 to 10.39 | Keep pushing | Arm parks at radius 0.548 m of 0.55 m; rejected steps do not accumulate |
| 10.39 | Stop publishing | ENGAGED until the age exceeds the timeout |
| 10.63 | (silence) | HOLD, "command timeout", age 0.263 s |

These timings come from one run on a loaded VM. They show the order of events,
not latency guarantees. The outward push curves rather than moving straight,
because joint rate limiting near full extension does not preserve straight
Cartesian lines, as CONTROL_SPEC already states.

## Record And Replay Check

On ROS_DOMAIN_ID 77 with localhost discovery: a 5.8 s session recorded 291
`controller/status`, 291 `joint_states`, 184 `teleop/command`, 97 `/tf`, and one
each of `/tf_static` and `/robot_description`. Playing back the output topics, a
subscriber that joined late with transient-local QoS still received
`/robot_description` and the static `tool_link` transform. Playing back only
`/teleop/command` into a fresh controller left it DISENGAGED with joints exactly
[0.4, 1.0]: recorded input cannot engage the robot.

The recorder must exit cleanly (Ctrl-C in a terminal, or SIGTERM) to write its
metadata. A SIGKILL leaves an empty `.mcap` and no `metadata.yaml`.

## Earlier Fixes Found By Running

- Teleop: `main()` called `node.handle(...)` while the method was named
  `handle_key`. Fixed before publication.
- Integration test: the post-shutdown check waited for a process that launch_testing
  had already stopped. It now asserts the exit code only.

## Next Validation Priorities

1. Human feel: your own terminal's autorepeat delay against the 0.35 s pulse
   (the automated test sends keys every 0.1 s).
2. Foxglove desktop client connected over the SSH tunnel.

## Recording Future Evidence

For each check add the exact command, machine/architecture, Ubuntu/ROS/RMW versions,
source revision, date, result summary and evidence location. Mark failed checks
FAILED with their first error. Keep unmeasured requirements NOT RUN until evidence
exists.
