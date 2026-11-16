# Learning Through HandPilot

Commands and exercises are for later Ubuntu use after a successful build, NOT RUN
here. Source the ROS underlay and this workspace overlay in every run terminal.
Predict outcomes first, inspect source, execute one experiment, then explain the
result. Copilot output is a starting hypothesis, not a substitute for understanding.

## Linux Paths And Processes

Meaning: paths locate files; processes are running programs with independent PIDs,
environments, and lifetimes. ~/handpilot is separate from ~/handpilot_ws.
Where: docs/TRANSFER_AND_SETUP.md and control/src/main.cpp.
Inspect: `pwd` and, separately, `pgrep -af keyboard_node`.
Exercise: locate a specific teleop PID, terminate only that process, then inspect HOLD.
Question: why does killing teleop not also kill the controller?

## CMake And Exported Libraries

Meaning: CMake declares targets and usage requirements; exports let another package
consume compiled code and includes without copying source.
Where: src/handpilot_core/CMakeLists.txt and src/handpilot_control/CMakeLists.txt.
Inspect: `find install/handpilot_core -name '*Export*.cmake' -o -name '*export*.cmake'`.
Exercise: trace handpilot_core::handpilot_core from export to target_link_libraries.
Question: why is C++17 a PUBLIC requirement on the core target?

## Ament And Colcon

Meaning: ament integrates individual ROS packages; colcon orders/builds/tests the
workspace dependency graph. They are not another name for the C++ compiler.
Where: every CMakeLists.txt/package.xml and teleop setup metadata.
Inspect: `colcon list`.
Exercise: build only core, then build packages through control using --packages-up-to.
Question: what differs between package-level concurrency and compiler-job concurrency?

## ROS Packages And Generated Types

Meaning: a package declares its name, dependencies, resources, and build type;
rosidl turns interface source into language-specific bindings.
Where: src/handpilot_interfaces/msg and srv, plus its CMakeLists.txt.
Inspect: `ros2 interface show handpilot_interfaces/msg/ControllerStatus`.
Exercise: locate the generated C++ header under install without editing it.
Question: why must you rebuild consumers after changing a message contract?

## Topics

Meaning: typed asynchronous streams; sending is not proof of receipt or engagement.
Where: ControllerNode subscriptions/publishers and keyboard_node.py publisher.
Inspect: `ros2 topic info /teleop/command --verbose`.
Exercise: identify publisher count and ensure only the intended source is active.
Question: why must JointState have exactly one authoritative live publisher?

## Services

Meaning: explicit request/response actions, used here for engagement and reset.
Where: SetEngaged.srv, controller node services, teleop call_async.
Inspect: `ros2 service list -t`.
Exercise: call reset while DISENGAGED and explain the refusal; then inspect a real fault reset.
Question: why must engage not silently reset FAULT?

## Parameters

Meaning: named configuration values, here fixed at startup to avoid live model drift.
Where: controller.yaml, ControllerNode declarations, and launch overrides.
Inspect: `ros2 param dump /handpilot_controller`.
Exercise: change a link length through the launch argument and compare model/achieved tool state.
Question: what becomes inconsistent if only the URDF length changes?

## QoS

Meaning: delivery, queue, and durability policies negotiated by ROS middleware.
Where: command KEEP_LAST(1)/BEST_EFFORT/VOLATILE declarations in both adapters.
Inspect: `ros2 topic info /teleop/command --verbose`.
Exercise: predict incompatible subscription behavior, then inspect policy values before altering them.
Question: why can RELIABLE plus a large command queue be undesirable for teleoperation?

## Header Time Versus Steady Time

Meaning: ROS stamps describe observations; elapsed integration/watchdog time uses
a single local monotonic clock, which is not comparable to another machine's clock.
Where: ControllerNode::steady_seconds/tick and Controller::receive/step.
Inspect: `ros2 topic echo /controller/status --once`.
Exercise: calculate command_age from a core test's supplied arrival/now values.
Question: why cannot a recent receiver arrival prove a command was not delayed in transit?

## JointState

Meaning: named joint arrays with positions, optional velocities/efforts, and a stamp.
Here they represent simulated state, not encoder readings.
Where: controller_node.cpp publish method.
Inspect: `ros2 topic echo /joint_states --once`.
Exercise: compare the two velocity values against the configured 0.8 rad/s bounds.
Question: why publish actual joint updates rather than the unconstrained IK request?

## URDF And TF

Meaning: URDF describes the kinematic tree; TF provides time-stamped transforms
computed from that tree and joints.
Where: planar_arm.urdf.xacro and bringup's robot_state_publisher node.
Inspect: `ros2 run tf2_ros tf2_echo base_link tool_link`.
Exercise: change L1 consistently, rebuild if required, and compare tool TF with core FK.
Question: why is elbow_joint's origin [L1,0,0], while its visual is centered at L2/2?

## Forward And Inverse Kinematics

Meaning: FK maps joints to a tool point; IK asks for valid joints reaching a point.
Multiple IK branches and unreachable points are normal, not numerical exceptions.
Where: planar_arm.cpp, inverse_kinematics.cpp, and test_kinematics.cpp.
Inspect: `colcon test --packages-select handpilot_core --event-handlers console_direct+`.
Exercise: add a test for an outward target beyond 0.55 m and an inward one below 0.05 m.
Question: why does radial reachability not imply reachability under hard joint limits?

## Jacobians

Meaning: the local derivative mapping joint rates to Cartesian velocity; it is
configuration dependent and can be singular. v0.1 teaches it but uses analytic IK.
Where: planar_arm.cpp jacobian and central-difference test.
Inspect: `sed -n '/JacobianMatchesCentralDifferences/,$p' src/handpilot_core/test/test_kinematics.cpp`.
Exercise: vary finite-difference epsilon and explain cancellation versus truncation error.
Question: what happens to the Jacobian rank at full extension?

## Rate Limits And Anti-Windup

Meaning: constrain actual joint displacement per elapsed time, then discard the
unachieved target residual so delayed motion does not accumulate.
Where: constraints.cpp rate_limit and controller.cpp step.
Inspect: `ros2 topic echo /controller/status` while exercising a boundary.
Exercise: deliberately request unreachable +X velocity from a full-extension test pose;
add a core assertion before changing the behavior. Reverse input and inspect recovery.
Question: why might joint-limited motion deviate from a straight Cartesian path?

## State Machines And Watchdogs

Meaning: explicit states restrict transitions; stale receiver input stops engagement
but fresh input alone must not restart it.
Where: docs/CONTROL_SPEC.md, Controller class, and test_controller.cpp.
Inspect: `ros2 topic echo /controller/status` after stopping teleop.
Exercise: explain the impact of 0.10 s versus 0.50 s timeout, then test a reviewed setting.
Then stop teleop and use status.reason and command_age to explain why HOLD occurred.
Question: why is a software watchdog in a VM not a physical emergency stop?

## Unit Versus Integration Tests

Meaning: units isolate deterministic math/transitions; integration checks real process,
middleware, generated types, and lifecycle behavior. Neither replaces all manual tests.
Where: core/test, teleop/test, control/test/test_controller_integration.py.
Inspect: `colcon test-result --verbose` after actually running tests.
Exercise: add one failing behavioral test before changing a stop transition, then fix the source.
Question: what can a core test prove that a wall-clock integration test cannot prove as precisely?

## Rosbag And Reproduction

Meaning: recordings preserve selected topic observations, not automatically every
state event or the receiver's original timing.
Where: docs/RECORD_AND_REPLAY.md and ignored recordings/.
Inspect: `ros2 bag info recordings/session01` after creating a real recording.
Exercise: view output with live publishers stopped, then separately replay only input.
Question: where would engagement/reset events and virtual time come from in a deterministic harness?

## A Useful Learning Loop

Write the expected transition/units first. Point to the code that owns it. Add one
assertion. On the authorized Ubuntu target, run the narrow check, inspect a failure
or result, and write your own explanation. Ask Copilot to challenge that explanation,
not to replace evidence with more generated code. Keep unknowns visible.
