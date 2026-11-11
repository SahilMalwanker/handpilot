# Optional Visualization

No layout JSON is shipped: schema compatibility has not been verified.
The optional launch starts only `foxglove_bridge`, bound to VM loopback.
It does not start a desktop, browser, or second controller. Install the bridge
separately only after checking ARM64 availability; it is intentionally not a
mandatory package dependency. In the source tree follow
[manual panel setup](../../../docs/VISUALIZATION.md). The installed package copy
does not include the repository-level docs; consult the source README there.

Inspect `/joint_states`, `/tf`, `/tf_static`, `/robot_description`, and
`/controller/status`. Adjust paths for a namespace. Use `base_link` as the 3D
fixed frame; primitive visuals require no mesh downloads. A frame alone does not
prove that the robot model loaded: check the link geometry and tool position.
