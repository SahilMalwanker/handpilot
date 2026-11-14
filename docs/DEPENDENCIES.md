# Dependencies And API Assumptions

## Required Runtime/Build

Ubuntu 24.04 ARM64, ROS 2 Jazzy binary ros-base and ros-dev-tools. Standard library
C++17 math; no Eigen for a two-link analytic solution. Python 3 supplied by Ubuntu
for rclpy/launch/teleop. No Node.js project dependency or application frontend.

| Package | Important dependencies |
| --- | --- |
| interfaces | ament_cmake, rosidl_default_generators/runtime, std_msgs |
| core | ament_cmake; ament_cmake_gtest for tests; no rclcpp |
| control | rclcpp, rcl_interfaces, core, interfaces, sensor_msgs, std_srvs |
| control tests | launch_testing_ament_cmake, launch_testing, launch_ros, launch, rclpy, pytest |
| teleop | ament_python, setuptools, rclpy, rcl_interfaces, interfaces, std_srvs; pytest |
| description | ament_cmake, xacro |
| bringup | ament_cmake, ament_index_python, launch, launch_ros, Python YAML, control, description, teleop, robot_state_publisher, xacro |

Use rosdep from ~/handpilot after supplying real manifest email metadata. Keep
parallelism at two jobs and sequential packages initially. Neither memory nor
runtime cost has been measured. No dependencies are vendored/downloaded here.
Optional target tools: rosbag2 for recordings, tf2_ros CLI for TF inspection,
foxglove_bridge for visualization. No optional camera/rosbridge package is installed.

If recording/TF tools are absent, human Ubuntu binary-install example, NOT RUN:

```bash
sudo apt install ros-jazzy-rosbag2 ros-jazzy-tf2-ros
```

The target Ubuntu Python baseline is 3.12; generated rclpy bindings must come from
the same Jazzy underlay rather than an unrelated pip or Windows interpreter.

## Documentation Consultation

The following official Jazzy pages were requested on 2026-10-19 but returned an
anti-bot interstitial, so their API contents were NOT verified:

- https://docs.ros.org/en/jazzy/How-To-Guides/Ament-CMake-Documentation.html
- https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Testing/Integration.html
- https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

Readable action documentation was consulted (web pages only, not GitHub APIs):

- https://github.com/ros-tooling/setup-ros/tree/v0.7
- https://github.com/actions/checkout/tree/v4

Those pages document the selected tags, `persist-credentials: false`, read-only
contents permission, and setup-ros development-tool setup. Tags are mutable;
review/pin verified commit IDs before adopting a supply-chain policy. No hashes
were invented. These citations establish intended usage, not a successful workflow.

## Unverified Compatibility Checks

- Jazzy ament_export_targets default namespace must expose
  `handpilot_core::handpilot_core` to the downstream control package.
- rosidl bounded string/fixed arrays and generated C++/Python field assignments
  must compile/import with the installed Jazzy generator versions.
- rclcpp read-only descriptors, create_wall_timer, QoS, service callback signatures,
  and steady-time behavior must be built and exercised on target.
- launch_testing injected context, add_launch_test, pytest discovery, process
  shutdown/exit assertions, and local DDS discovery need real integration execution.
- rclpy async service ordering, shutdown handling, terminal cleanup, and console
  entry-point installation need interactive SSH testing.
- `rclpy.signals.SignalHandlerOptions.SIGTERM` passed to `rclpy.init` must leave
  SIGINT as Python KeyboardInterrupt on Jazzy, enabling the Ctrl-C stop request.
- launch substitutions, YAML wildcard parameters, Xacro evaluation and model/TF
  agreement need actual expansion and launch. Foxglove package/parameters and
  rosbag transient-local playback compatibility are optional separate checks.

## Future CI

.github/workflows/ci.yml is authored only, NOT RUN. Ubuntu 24.04 hosted runner
normally means x86_64, not this ARM64 VM. The documented setup-ros option
`required-ros-distributions` installs a desktop variant, so it is deliberately not
used. Default action mode prepares tools/repositories; an explicit apt step installs
binary ros-jazzy-ros-base and ros-dev-tools. It does not compile ROS from source.
Bare-host apt mirrors can be flaky per upstream documentation. Current package
availability and action interaction with Ubuntu 24.04 remain unverified.

The first source-inspection step intentionally rejects unset maintainer emails.
No user-provided secrets, deployment, artifact publication, GUI, camera, or Docker
are used. GitHub's standard action implementations use hosted action tooling;
this does not introduce a Node.js runtime/build step into HandPilot. No action has
run here. CI cannot replace ARM64, SSH terminal, model, and timing validation.
