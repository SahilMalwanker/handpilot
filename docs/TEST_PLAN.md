# Test Plan

All tests are authored and NOT RUN. No camera, display, physical robot, downloads,
or external network service is required. ROS tests need local DDS/process IPC.
Real package metadata and a successful build are prerequisites.

## Automated Source

| Source | Behavioral assertions |
| --- | --- |
| src/handpilot_core/test/test_kinematics.cpp | Known FK, IK/FK round trips, both branches, nearest hard-limit-valid equivalents, inner/outer unreachable targets, joint exclusions, cosine tolerance, finite failure output, Jacobian central differences |
| src/handpilot_core/test/test_constraints.cpp | Cartesian magnitude including huge finite input, joint rate/position bounds, invalid dt, invalid desired joints, invalid config |
| src/handpilot_core/test/test_controller.cpp | No motion while stopped, no jump at engage/re-engage, fresh target, stale/inactive HOLD, no recovery auto-engage, timeout not hidden by new arrival, session changes, duplicate sequences, invalid dt/time/velocity, reset gates, rate-limited and unreachable anti-windup |
| src/handpilot_teleop/test/test_keyboard_mapping.py | Direction/action mapping, finite speed, pulse expiry/repeat, stop clearing, active-zero engage window, invalid time |
| src/handpilot_control/test/test_controller_integration.py | Startup DISENGAGED, fresh input plus explicit engage, observable motion, finite named joints/speed bounds, inactive and stale HOLD, recovery alone stays stopped, rejected frame faults without process exit, explicit reset, clean launch shutdown |

Core tests supply time directly and need no sleeping or ROS. They use finite
differences with epsilon=1e-6 and comparison tolerances appropriate to the checked
quantity, not exact equality for trigonometric round trips. Exact equality is used
for unchanged joint arrays, a deliberate stop invariant. IK tie order is deterministic.

Integration uses launch_testing_ament_cmake/add_launch_test, one unique namespace,
localhost discovery, a real controller process, explicit service responses, bounded
polls, and post-shutdown process assertions. It does not claim fake success when
messages are absent. Timing is intentionally a target risk on a small VM. The
ROS_AUTOMATIC_DISCOVERY_RANGE variable restricts discovery to the host for the test;
use a separate ROS_DOMAIN_ID from other local work when appropriate.

## Later Ubuntu Commands

After build, source ROS and ~/handpilot/install/setup.bash, then from ~/handpilot:

```bash
colcon test --executor sequential
colcon test-result --verbose
```

Focused examples after a relevant change:

```bash
colcon test --packages-select handpilot_core --event-handlers console_direct+
colcon test --packages-select handpilot_teleop --event-handlers console_direct+
colcon test --packages-select handpilot_control --event-handlers console_direct+
colcon test-result --verbose
```

Run only the intended command and inspect its actual result. Test source changes
may need a rebuild. `colcon test` alone can exit without making failed assertions
obvious; inspect test-result, and CI also requests --return-code-on-test-failure.
An empty result set is not a pass. Record package counts and first failing assertions.

## Manual Acceptance Gates

1. Complete email metadata, inspect source, resolve dependencies, build all six
   packages with sequential executor/two jobs on Ubuntu 24.04 ARM64.
2. Confirm each test suite is discovered and run, including real process shutdown.
3. Launch normally: one joint-state publisher; correct names, finite state, expected
   DISENGAGED startup. Compare tool TF with achieved FK and shared lengths.
4. In interactive SSH, exercise e/direction, pulse expiration, Space, q, Ctrl-C,
   process termination, restart/session switch, stale-input HOLD, and explicit reset.
5. Check both normal and exception terminal cleanup. SIGKILL cannot run cleanup;
   document that limitation rather than expecting impossible restoration.
6. Exercise boundaries and joint limits; inspect requested/achieved discrepancy and
   stable HOLD. Verify recovery messages alone never resume motion.
7. Record and inspect a bag, then separately view output and conduct input-only
   replay. Verify actual static TF/model capture. Optional Foxglove is a separate gate.
8. Record real evidence and remaining gaps. A future public CI run on x86_64 is an
   additional check, never a replacement for target/interactive validation.

## Explicit Coverage Gaps

Terminal termios restoration, signal delivery, OS autorepeat, delayed asynchronous
service responses, generated-model parsing, URDF/FK agreement through TF, ROS clock
jumps, transport-delayed samples, and optional bridge/bag compatibility still need
manual or additional focused automated tests. Unit tests do not prove physical
safety. There are no dynamics, collision, camera, hardware, or performance tests.
The source inspector is a separate hygiene aid, not the ROS build/test gate.
