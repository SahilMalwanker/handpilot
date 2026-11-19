---
description: "Diagnose supplied Ubuntu compiler or test output with minimal source changes."
agent: agent
---

Use the actual output supplied by the user. Ask for missing first-error context,
command, architecture, Jazzy environment, and overlay paths when they determine
the diagnosis. Separate primary failure from downstream errors. Check nearby
targets/manifests/generated names; propose and author the smallest justified fix
and its focused Ubuntu recheck command. Do not run commands here, install tools,
guess successful results, or suppress failing tests. Record unresolved assumptions.
