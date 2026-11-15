# Optional Foxglove Visualization

Keyboard mode needs no viewer, display, camera, or external network service.
Foxglove Bridge is optional and intentionally absent from required manifests.
Jazzy ARM64 availability, executable parameters, asset service behavior, and panel
compatibility have NOT been verified. No screenshots or layout JSON are claimed.

## Target Setup

User commands on Ubuntu only, after checking policy and availability:

```bash
apt-cache policy ros-jazzy-foxglove-bridge
```

If a suitable ARM64 candidate exists and installation is approved:

```bash
sudo apt install ros-jazzy-foxglove-bridge
source /opt/ros/jazzy/setup.bash
source ~/handpilot/install/setup.bash
ros2 launch handpilot_bringup visualization.launch.py
```

Run normal bringup separately. The optional launch only starts the bridge and
binds it to VM loopback at port 8765. It does not launch a desktop application or
another robot. Do not expose an unauthenticated bridge to an untrusted network.
User command on macOS, using the existing SSH alias:

```bash
ssh -N -L 8765:127.0.0.1:8765 ubuntu-ros2
```

Use an available Foxglove client on the Mac and open a Foxglove WebSocket connection
to `ws://localhost:8765`. Client distribution/sign-in requirements depend on the
chosen Foxglove version and are not prerequisites for this repository. No client
installation is automated. If port 8765 is in use, choose another bridge port and
match the tunnel/connection. Close the tunnel when done.

## Manual Panels

1. Add a raw-message panel for /controller/status. Inspect state, reason, requested
   and achieved positions, limiting/rejection, and command age.
2. Add a plot for the two /joint_states positions. These are simulated radians,
   not measured hardware feedback. Check HOLD as constant positions.
3. Add a 3D panel, fixed frame base_link. Enable /tf and /tf_static transforms.
4. Configure the panel's robot model/URDF source from /robot_description if the
   client supports that topic. Otherwise load the actual expanded URDF produced
   by Xacro on Ubuntu, transferring only that text file through an approved route.
5. Confirm the two link boxes and tool sphere appear, with tool translation
   matching achieved_position. A visible TF tree alone is not a model-render check.

Adjust topic paths for a namespace. Primitive visuals need no external meshes.
Panel names/schema can vary by client release; consult that version's documentation
instead of guessing layout JSON. Record the tested client/bridge versions later.

## Protocol Boundary

Foxglove Bridge uses the Foxglove protocol for observation/tooling. rosbridge uses
its own JSON protocol and is only a possible future transport for Mac camera input.
Their clients are not interchangeable. Neither is required by keyboard control.
The bridge may expose publishing/services; do not use that as proof of an
authenticated or safety-approved control interface.
