# Control Specification

Status: This document specifies the intended behavior of the simulated controller.
Implementation conformance, build success, and runtime behavior were not
verified for this specification.

## Coordinates And Defaults

Kinematic simulation only. Base frame `base_link`, XY plane, both joint axes
+Z. Joint order is always `shoulder_joint`, `elbow_joint`. Lengths are 0.30 m
and 0.25 m. Initial joint angles are [0.4, 1.0] rad, away from full extension.
Each joint is limited to [-2.8, 2.8] rad; default speed limit is 0.8 rad/s.
Cartesian velocity magnitude is limited to 0.12 m/s, not independently per axis.
Timer default 50 Hz, command timeout 0.25 s, maximum integration dt 0.10 s.
These are suggested, unmeasured, unvalidated values, not hard real-time guarantees.

All numerical configuration must be finite. Supported link lengths are 1e-4..10 m,
joint speed limits (0,100] rad/s, Cartesian speed limit (0,10] m/s, max_dt (0,1] s,
and timeout >0 s. Lower joint bounds must be below upper bounds, with initial
joints inside them. Adapter timer rate must be 1..500 Hz and period <= max_dt.
Invalid configuration fails startup rather than exposing a resettable running node.

## State Transitions

Events are processed serially in executor delivery order; there is no guaranteed
cross-topic/service ordering. For each event, fault/time/input validity gates run
before its ordinary transition. No command reception engages motion.

| Event | DISENGAGED | ENGAGED | HOLD | FAULT |
| --- | --- | --- | --- | --- |
| Startup | Initial state | N/A | N/A | N/A |
| Engage with fresh accepted command | ENGAGED | ENGAGED (idempotent) | ENGAGED | Refused |
| Engage without fresh command | Refused | HOLD, refused | Refused | Refused |
| Disengage service | HOLD | HOLD | HOLD | FAULT, refused |
| Valid active command, same session | Store freshness only | Store velocity | Store freshness only | Ignore |
| Valid inactive heartbeat | Stay | HOLD | Stay | Ignore |
| New source/session | Bind source, stay | HOLD and bind source | Bind source, stay | Ignore |
| Duplicate/out-of-order sequence | Reject, stay | HOLD, reject | Reject, stay | Ignore |
| Stale command at timer | Stay | HOLD | Stay | Stay |
| Non-positive/excessive finite dt | Stay, clear target | HOLD | Stay, clear target | Stay |
| Non-finite time/input, invalid frame, malformed source | FAULT | FAULT | FAULT | Stay |
| Unreachable integrated target | Stay | ENGAGED, reject step | Stay | Stay |
| Reset with valid current state/config | Refused | Refused | Refused | DISENGAGED |
| Reset with invalid state/config | Refused | Refused | Refused | FAULT, refused |

FAULT is latched. Reset clears the session, sequence history, velocity, and
command age; a fresh command and a separate explicit engage are then required.
Disengage is not fault reset. Repeated engage while already engaged does not
clear a pending active command. Engagement from a stopped state synchronizes
the target to FK and clears velocity: a subsequent directional command is needed.
A fresh inactive heartbeat is sufficient to authorize the engage request, but
the next inactive heartbeat stops engagement again. Keyboard `e` opens a 0.35 s
active-zero window and requests engagement asynchronously; then press a direction.
Active-zero commands preserve exact joint positions, without an IK round trip.
Reset clears input history but leaves diagnostic events latched until publication.

## Motion And Constraints

FK: x = L1 cos(q1) + L2 cos(q1+q2), y = L1 sin(q1) + L2 sin(q1+q2).
IK evaluates both signs of acos(cos(q2)). Cosine overshoot up to 1e-10 may
be clamped; anything further outside [-1,1] fails. The radial workspace is
[abs(L1-L2), L1+L2], including the inner boundary. Joint limits further
restrict reachable points. Equivalent angles are enumerated within hard joint
bounds, then the candidate with smallest ordinary joint-space distance wins.
Do not use wrapped distance across a hard stop. Interpolation never wraps.
Supported configured angle bounds must lie within [-2*pi, 2*pi].

Each engaged timer tick forms requested = achieved FK + bounded velocity * dt.
Only a valid IK result can update joints. Each actual joint update is clamped
to its own max_speed * dt. The next target is always the new achieved FK,
including after a rejected or rate-limited step. This deliberately discards
tracking error (anti-windup), trading exact Cartesian paths for bounded motion.
Requested position in status describes the last bounded Cartesian attempt;
achieved describes the simulated joints. There is no Cartesian path guarantee
near singularities or under joint rate limiting. HOLD/FAULT clear pending motion
and synchronize both positions. No target accumulates while stopped.

## Time, Sessions, And Recovery

The core receives explicit steady-clock seconds; it never reads a clock.
The adapter computes timer dt and receiver arrival time from one steady clock.
ROS time is used only in published headers. Header time from a sender is not
compared with receiver time. Command age is receiver now minus last accepted
arrival, or unavailable. Invalid/repeated messages do not refresh freshness.
Stale means age > timeout. Excessive dt is rejected, not integrated or subdivided.
Non-finite time or a time reversal faults; finite zero/negative timer dt holds.
Fresh arrival after a stale gap also forces HOLD before refreshing the stored age,
so a late message cannot conceal a timeout between timer callbacks.

Source IDs identify a process session, not just a device name. Teleop uses a new
UUID on every start. Sequence must strictly increase within that session, with
no uint64 wraparound. A session change binds the new source but stops any
engagement and discards its first velocity. Switching back also counts as a
change. This is one-source operation, not authenticated arbitration: competing
sources will interrupt operation. Stop all but the intended publisher before
explicit re-engagement. Reset forgets the binding. Receiver arrival cannot prove
that an input was not delayed in transport; QoS reduces backlog, not this risk.

## Limits Of The Stop Model

HOLD means simulated joint positions stop changing. These are not measured
hardware states. No dynamics, collision checking, hardware feedback, certified
safety, or physical emergency stop is implemented. A stopped VM cannot publish
a stop message; there is no physical actuator in this project.
