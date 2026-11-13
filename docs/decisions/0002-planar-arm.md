# ADR 0002: Two-Link Planar Arm

Status: accepted design, numerical/runtime validation NOT RUN.

Context: a small model should still teach multiple IK solutions, singularities,
inner and outer workspace boundaries, limits, state machines, and transforms.

Decision: two +Z revolute joints, 0.30/0.25 m links, XY tool position, analytic
FK/Jacobian/position IK, hard position and actual speed constraints. Initial pose
is away from full extension. Select nearest valid equivalent angles without
wrapping across a hard stop; discard unachieved target error each tick.

Consequences: no Eigen is required. The arm is intentionally kinematic only.
Joint rate limits can distort Cartesian paths; no dynamics, collision checking,
hardware feedback, or safety guarantee is inferred from the model.
