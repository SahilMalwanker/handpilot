# Project

HandPilot teaches Linux robotics through one understandable vertical slice:
keyboard input -> ROS message -> pure C++ controller -> simulated joints -> TF.
The target learner has already run ROS talker/listener and built a starter C++
package, and now needs to explain an entire system rather than accumulate snippets.

v0.1 source includes two-link XY FK/IK/Jacobian, bounded velocity integration,
latched stop/fault states, ROS status/services, terminal input, a primitive model,
launch files, and tests. It builds and its 46 automated tests pass on the Ubuntu
24.04 ARM64 target; see [VALIDATION_STATUS](VALIDATION_STATUS.md). Nothing is
measured for performance or physically validated.

Non-goals: dynamics, collision checking, physical actuators, certification, camera
inference, a decorative frontend, plugin frameworks, Node.js runtime, external
meshes, Gazebo, Isaac Sim, MoveIt, Linux desktop, cloud, or databases.

## Resolved Specification Choices

- Separate `std_srvs/Trigger` reset, avoiding another custom interface file.
- Startup DISENGAGED; explicit stop and inactive input lead to latched HOLD.
- New source/session binds only while not faulted, never auto-engages.
- Invalid finite dt holds; non-finite input/time faults; invalid startup config throws.
- Achieved-position anti-windup instead of indefinitely integrating an unreachable target.
- Keyboard `e` emits a short active-zero pulse before the async engage request.
- Status events are latched until the next status publish; joints are simulated.
- Licensed under Apache-2.0 (LICENSE at the repository root).
- ROS format-3 manifests require a maintainer email, but none was supplied and
  fabrication is prohibited. Empty emails deliberately leave a pre-build blocker.
  The user must supply a real contact in all six manifests. No legal identity is invented.
- Optional bridge is not in the required dependency graph; its launch needs a
  separately installed package. No fake layout or transport is shipped.
- No extra implementation files beyond the requested tree were needed.

The authoring workstation and execution target are separate. Preserve the existing
~/handpilot_ws; this source builds from ~/handpilot. First release acceptance is
defined in [TEST_PLAN](TEST_PLAN.md), not by the volume of generated code.
