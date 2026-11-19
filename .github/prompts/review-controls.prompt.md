---
description: "Review HandPilot math, state transitions, limits, freshness, and recovery."
agent: agent
---

Perform a read-only controls review against docs/CONTROL_SPEC.md and ROS_INTERFACES.md.
Trace FK/IK/Jacobian conventions, angle equivalents versus hard stops, inner
workspace reachability, finite values, actual joint rate bounds, target anti-windup,
source/session changes, rejection freshness, dt gaps, and reset/engage separation.
Check terminal expiry and stop ordering. Present concrete findings by severity
with file references, counterexamples, and missing tests. Label static reasoning
as such. Do not change files or run code unless separately authorized.
