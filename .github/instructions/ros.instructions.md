---
description: "Use when editing ROS contracts, nodes, models, launch, or package metadata."
applyTo: "src/handpilot_interfaces/**,src/handpilot_control/**,src/handpilot_teleop/**,src/handpilot_description/**,src/handpilot_bringup/**"
---

Target Jazzy and record unverified API assumptions. Match generated message
fields, package dependencies, installed resources, executable names, and docs.
Use relative names and a single-threaded executor. Never block callbacks on
service responses. Separate receiver steady time from ROS header stamps.
Explain QoS; commands keep only the newest sample. Preserve terminal cleanup
and finite-duration pulses. Keep Xacro geometry and control configuration aligned.
Only the controller publishes live simulated joints. No fake camera adapters.
