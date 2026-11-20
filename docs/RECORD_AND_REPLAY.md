# Record And Replay

Ubuntu commands after successful build. All three procedures below were run on
the ARM64 target; results are in VALIDATION_STATUS. rosbag2 is an optional operation
tool, not a core dependency. If absent, check/install the Jazzy binary package
`ros-jazzy-rosbag2` on the target. Recordings are ignored and can consume VM disk.

## Record A Live Session

Source ROS and ~/handpilot/install/setup.bash. From ~/handpilot, with bringup and
teleop in their separate terminals:

```bash
mkdir -p recordings
ros2 bag record -o recordings/session01 \
  /teleop/command /controller/status /joint_states /tf /tf_static /robot_description
```

Choose a new output path for each session. Start recording before engaging.
Stop the recorder with Ctrl-C so metadata is finalized. Inspect without playback:

```bash
ros2 bag info recordings/session01
```

Confirm the actual topics and message counts. On Jazzy, transient-local
/tf_static and /robot_description were captured (one message each) and were
received by a late-joining subscriber during playback without a QoS override file.

## View Recorded Output

Stop the live controller, teleop, and robot_state_publisher. Keep only the optional
visualization bridge, then play the output topics:

```bash
ros2 bag play recordings/session01 --topics \
  /controller/status /joint_states /tf /tf_static /robot_description
```

This displays recorded state, not a new simulation. Do not run a second TF or
joint-state authority alongside these output topics. If a viewer fails to obtain
the model/static transforms, inspect bag contents and subscriber durability;
do not silently substitute live outputs and call the replay coherent.

## Replay Input Into A New Controller

This is a different experiment. Start a fresh controller (and optionally its model),
stop teleop, and play ONLY input:

```bash
ros2 bag play recordings/session01 --topics /teleop/command
```

Playback alone cannot engage the controller. A separate explicit SetEngaged call
must succeed while a fresh input is present. Playback inactive messages still
cause HOLD. Source/session and sequence checks still apply. Avoid looping:
sequences restart at the loop boundary and are rejected within the same session.
Reset is not available as a general replay restart; stop/restart the experiment.

Do not replay /joint_states alongside the live controller or treat two publishers
as one coherent state. Do not replay old status as if it describes the new controller.

## Why This Is Not Deterministic Reproduction

The listed topic recording does not capture engagement/reset service events as
core state events. Receiver-side monotonic arrivals, callback order, timer dt,
pauses, drops, scheduling, and explicit services all affect evolution. Sender ROS
timestamps do not determine watchdog age. `--clock` changes ROS observation time,
not the core's steady integration or receiver freshness. Changing playback rate
therefore changes behavior. A bag is evidence for inspection, not a deterministic
simulation trace or proof that replay reproduces the original trajectory.

A future core replay harness must capture accepted/rejected inputs, explicit
engage/reset events, initial configuration and state, supplied time/dt, and event
ordering, then drive a virtual clock with versioned expectations. It is planned,
not implemented. Review recordings for private information before sharing them.
