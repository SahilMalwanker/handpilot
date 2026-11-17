# Contributing

This source is an unexecuted learning implementation, not a validated robot
controller. No license has been chosen; resolve licensing and real maintainer
metadata before inviting public use or making licensing claims.

Read [CONTROL_SPEC](docs/CONTROL_SPEC.md) and [ROS_INTERFACES](docs/ROS_INTERFACES.md)
first. Work on one behavior at a time, add a focused test before changing it,
preserve units and hard-stop semantics, and keep the core ROS-independent.
Do not add plugins or heavyweight dependencies without a concrete learning need.

Author/inspect only on this Windows workstation. Human Ubuntu build/test commands
are in [TRANSFER_AND_SETUP](docs/TRANSFER_AND_SETUP.md). Any later execution must
be explicitly authorized on its actual target; do not reinterpret documentation
as workstation execution permission. Record exact commands, platform, revision,
and real results in [VALIDATION_STATUS](docs/VALIDATION_STATUS.md). NOT RUN is valid;
invented success is not. CI x86_64 is not ARM64 target validation.

Use C++17, standard library math, two-space C++ indentation, four-space Python,
UTF-8 text, LF, final newlines, and case-consistent paths. Keep source small;
exclude generated builds, caches, environment secrets, and private recordings.
Use console entry points, not executable bits inherited from ZIP files.

Reviews should cover failure paths, stop ordering, stale/repeated inputs, finite
math, actual joint speed limits, export targets, ROS manifests, and cleanup.
Choose one authoritative source copy and synchronize Mac/VM edits deliberately.
Use explicit staging paths and review staged content; never initialize or publish
Git here. See [PUBLISH_FROM_MAC](docs/PUBLISH_FROM_MAC.md).
