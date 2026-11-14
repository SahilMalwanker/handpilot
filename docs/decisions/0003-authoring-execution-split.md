# ADR 0003: Separate Authoring And Execution

Status: accepted workstation constraint.

Context: files are authored in VS Code on Windows, while the actual ROS runtime is
Ubuntu Server 24.04 ARM64 in a 3 GB/two-vCPU UTM VM on an M2 Mac. An older learning
workspace already exists and must not be overwritten.

Decision: author/inspect files only here. No commands, installations, code execution,
CI, Git initialization, APIs, publication, or execution workarounds. Manually ZIP
the source, transfer to Mac, and copy to ~/handpilot in the VM. Keep ~/handpilot_ws.

Consequences: all execution fields start NOT RUN, with explicit metadata and API
blockers. Build from the directory containing src, use binary ROS dependencies,
limit compilation parallelism, and preserve one authoritative tested source copy.
Future x86_64 CI adds evidence but never replaces ARM64 or interactive validation.
