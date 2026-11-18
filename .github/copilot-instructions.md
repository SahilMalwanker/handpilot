# HandPilot

ROS-first learning project: a two-link XY kinematic arm simulation, not hardware
control, dynamics, collision checking, or a safety-certified system.

On the authoring workstation, author and inspect files ONLY. Do not execute
shells, Python, C++, ROS, tests, linters, Node, installers, Docker, WSL, or CI.
Do not download binaries, initialize Git, publish, or access GitHub APIs.
Do not infer permission from an existing terminal or approved unrelated workflow.
Never initialize Git without explicit authorization. Never fabricate results.

The actual runtime is Ubuntu Server 24.04 ARM64, ROS 2 Jazzy, in a 3 GB/two-vCPU
UTM VM on an M2 Mac. New workspace is ~/handpilot, not ~/handpilot_ws.
Read docs/CONTROL_SPEC.md and docs/ROS_INTERFACES.md before changing behavior.

- interfaces owns generated message/service contracts.
- core owns deterministic C++17 math, constraints, and transitions, without ROS.
- control adapts clocks/messages and exclusively owns simulated joint state.
- teleop owns terminal cleanup and expiring velocity pulses, not joint state.
- description owns primitive Xacro geometry; bringup owns shared config/launch.

Human commands intended ONLY for the Ubuntu target, after manifest metadata is
completed: source /opt/ros/jazzy/setup.bash; cd ~/handpilot;
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y;
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon build --symlink-install --executor sequential;
source install/setup.bash; colcon test --executor sequential;
colcon test-result --verbose. Never sudo colcon or build ROS from source.

HOLD freezes simulated positions and clears pending input. Fresh messages never
automatically engage after a stop, session change, or fault. Fault reset is a
separate service. A watchdog is not a physical emergency stop. Update tests and
honest validation status with every behavioral change; do not choose a license
or invent a maintainer email. See docs/TRANSFER_AND_SETUP.md for metadata blockers.
