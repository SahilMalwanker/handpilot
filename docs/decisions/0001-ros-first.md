# ADR 0001: ROS First

Status: accepted design, implementation unexecuted.

Context: the learning goal is Linux robotics, C++, ROS packages, topics, services,
transforms, tests, and debugging on a small Ubuntu VM.

Decision: build a ROS-first vertical slice with a ROS-independent C++ library,
one ROS state-owning controller, terminal input, primitive model, and CLI tooling.
No browser frontend or Node.js application dependency. Optional viewers observe ROS.

Consequences: middleware/build concepts are visible and inspectable. Generated
message types and package metadata must actually validate on Jazzy. A viewer cannot
hide missing ROS functionality, and pure core tests can isolate math from DDS timing.
