# Robot Model

Kinematic model only, with primitive URDF visuals and no external meshes. There
is no dynamics simulator or collision checker. Required URDF effort limits are
nominal parser metadata, not torque capability; there are no inertial claims.

| Frame/joint | Definition |
| --- | --- |
| base_link | Fixed planar origin, X/Y control plane |
| shoulder_joint | Revolute +Z at [0,0,0], q1 in rad |
| upper_arm_link | Extends L1 along local +X |
| elbow_joint | Revolute +Z at [L1,0,0] in upper_arm_link, q2 relative to shoulder |
| forearm_link | Extends L2 along its local +X |
| tool_fixed_joint/tool_link | Fixed at [L2,0,0] in forearm_link |

The visual boxes are centered at each link's half-length. Tool center, not the
surface of its decorative sphere, is the controlled endpoint. Both axes have
the same positive direction; the distal link angle is q1+q2, not q2 alone.

$$
\begin{aligned}
x &= L_1\cos q_1 + L_2\cos(q_1+q_2) \\
y &= L_1\sin q_1 + L_2\sin(q_1+q_2)
\end{aligned}
$$

$$
J = \begin{bmatrix}
-L_1\sin q_1-L_2\sin(q_1+q_2) & -L_2\sin(q_1+q_2) \\
L_1\cos q_1+L_2\cos(q_1+q_2) & L_2\cos(q_1+q_2)
\end{bmatrix}
$$

Defaults L1=0.30 m, L2=0.25 m give geometric radius 0.05..0.55 m; joint
limits [-2.8,2.8] rad make part of that annulus inaccessible. The exact inner
radius would require elbow magnitude pi, excluded by default hard bounds.
Initial [0.4,1.0] rad is away from the full-extension singularity. Analytic
Jacobian is taught/tested but v0.1 uses position IK, not Jacobian inversion.

Change lengths through bringup so Xacro and controller receive the same values:

```bash
ros2 launch handpilot_bringup handpilot.launch.py link1_length:=0.32 link2_length:=0.25
```

Human Ubuntu example, NOT RUN. Persistent defaults and joint bounds live in
src/handpilot_bringup/config/controller.yaml; standalone controller/core defaults
also exist and should be updated for a deliberate default-model change.
Bringup reads YAML joint bounds/speeds into Xacro. Directly launching a controller
with different parameters and an unrelated model bypasses that synchronization.

Inspect actual transform on Ubuntu:

```bash
ros2 run tf2_ros tf2_echo base_link tool_link
```

Compare translation with controller/status. No joint_state_publisher GUI is used;
the controller alone publishes positions. TF time follows ROS stamps even though
motion integration follows steady time. Model expansion and TF agreement NOT RUN.
