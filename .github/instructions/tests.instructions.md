---
description: "Use when authoring numerical unit or ROS integration tests."
applyTo: "src/**/test/**"
---

Assert observable behavior, not implementation presence or unconditional success.
Use supplied time for core tests, numerical tolerances, bounded waits for ROS,
and explicit launch process shutdown assertions. No camera, display, downloads,
physical robot, or external network services. Document coverage gaps. All tests
remain NOT RUN until an authorized target execution supplies evidence.
