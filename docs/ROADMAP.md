# Roadmap

## Authored v0.1 Slice

All requested package, test, launch, configuration, instruction, and documentation
files have source content. FK/IK/Jacobian, constraints, explicit control states,
session-aware freshness, keyboard pulses, simulated JointState/status, Xacro,
robot_state_publisher launch, and optional bridge launch are authored.
This is not a claim of compiled or working runtime behavior. All execution NOT RUN.

## Immediate Remaining Work

1. Supply real maintainer emails in six manifests. Choose a license before publication
   and replace TODO consistently; no license selection was made during authoring.
2. Transfer source to ~/handpilot without overwriting edited work or changing ~/handpilot_ws.
3. Run source inspection, rosdep, sequential build, unit tests, launch integration,
   and test-result on Ubuntu 24.04 ARM64. Resolve actual first failures using logs.
4. Verify generated/exported APIs, terminal expiry/cleanup, service ordering,
   source restart, VM gaps, frame/model/FK agreement, and exact run commands.
5. Record target evidence. Inspect and run future public CI only after user publication
   approval; record x86_64 evidence separately. No workflow was triggered here.
6. Verify optional Foxglove and bag capture/replay separately; do not block keyboard
   learning on a missing ARM64 bridge or viewer.

## After Baseline Validation

- Add focused automated tests for pseudo-terminal cleanup and async stop ordering,
  model/FK comparison via TF, clock jumps, and configurable joint-limit edge cases.
- Add a deterministic core event/replay harness with explicit virtual time and
  state-service events. Ordinary bag playback is not that harness.
- Compare position IK tracking with a Jacobian-based controller using declared
  metrics, constraints, and real measurements. Do not publish invented benchmarks.
- Implement a real Mac camera adapter only after the mapping/transport design and
  privacy/dependency review in CAMERA_INTEGRATION_PLAN are accepted.
- Evaluate an expanded model, explicit source arbitration, and multi-arm frame
  prefixes only when the learning goal justifies the additional complexity.

Hardware control, dynamics, collision checking, safety certification, Gazebo,
MoveIt, and cloud services are outside v0.1. Do not silently introduce them while
fixing an unrelated build failure. Each milestone needs acceptance tests and
separate authored/compiled/tested/measured status.
