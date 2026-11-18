---
description: "Use when editing deterministic kinematics, constraints, or controller logic."
applyTo: "src/handpilot_core/**"
---

Keep C++17 core APIs independent of ROS, clocks, files, environment, and network.
Use explicit supplied steady seconds, meters, radians, and named state transitions.
Maintain finite outputs, inner workspace bounds, both IK branches, hard joint
limits without wrapped shortcuts, rate bounds, and achieved-state anti-windup.
Add focused tests with supplied times and justified tolerances before changing
behavior. Preserve reusable exported includes/targets. Do not execute locally.
