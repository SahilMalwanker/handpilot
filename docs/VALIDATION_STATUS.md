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
| Source revision | `af62153` plus the documentation and media changes in this update |

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
| Source hygiene inspector | n/a | PASSED, 0 errors | `python3 scripts/inspect_source.py`; warnings only for the license TODO |
| Interactive keyboard terminal (cbreak, autorepeat, Ctrl-C) | PASSED | NOT RUN | needs a human at an interactive SSH terminal |
| Xacro expansion and robot_state_publisher TF | PASSED | NOT RUN | launch file built; TF not yet compared with FK |
| Optional Foxglove launch | n/a | NOT RUN | package/ARM64/client compatibility unverified |
| Recording/replay procedure | n/a | NOT RUN | instructions only, no bags recorded |
| GitHub Actions CI | n/a | NOT RUN here | workflow source only; check the Actions tab for real runs |
| Webcam/rosbridge adapter | NO, planned | NOT RUN | CAMERA_INTEGRATION_PLAN only |
| Performance/latency/memory measurements | NO | NOT RUN | no benchmark claims |

Total: 46 test cases, 0 failures. `colcon test-result` reports 50 because it also
counts four CTest wrapper entries.

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

## Earlier Fixes Found By Running

- Teleop: `main()` called `node.handle(...)` while the method was named
  `handle_key`. Fixed before publication.
- Integration test: the post-shutdown check waited for a process that launch_testing
  had already stopped. It now asserts the exit code only.

## Next Validation Priorities

1. Interactive keyboard: autorepeat delay against the 0.35 s pulse, Ctrl-C stop path,
   terminal restoration.
2. Model/state agreement: compare `tool_link` TF from robot_state_publisher with core
   FK for the same joints, including after changing the link lengths.
3. CI on GitHub-hosted Ubuntu 24.04 (x86_64) to complement the ARM64 results.

## Recording Future Evidence

For each check add the exact command, machine/architecture, Ubuntu/ROS/RMW versions,
source revision, date, result summary and evidence location. Mark failed checks
FAILED with their first error. Keep unmeasured requirements NOT RUN until evidence
exists.
