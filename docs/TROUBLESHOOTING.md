# Troubleshooting

Use actual Ubuntu output. All scenarios below are diagnostic guidance, not observed
results. Record the first error, exact command, source identity, and environment.

| Symptom | Inspect | Likely next action |
| --- | --- | --- |
| Invalid maintainer email/package discovery | All six package.xml files | Supply a genuine email; do not fabricate metadata |
| Package not found | `pwd`; `ros2 pkg prefix handpilot_control` | Build from ~/handpilot; source ROS and this overlay |
| Builds starter code instead | `printenv AMENT_PREFIX_PATH` | Use fresh terminal without ~/handpilot_ws overlay |
| Generated message import missing | Interface build log and source order | Fix first interface failure; rebuild downstream packages |
| Exported core target missing | Installed core CMake exports | Verify Jazzy export namespace before changing linkage |
| Compiler killed/OOM | VM memory and first build log | One build job, sequential packages; no GUI stack |
| Service says fresh input required | Topic QoS, source/session, status age | Start teleop; retry e explicitly after discovery |
| e succeeds but no motion | Active pulse expiry and subsequent direction | Press a direction within pulse window; adjust tuning deliberately |
| HOLD after key pause | Status reason | Expected inactive expiry; e then fresh direction |
| HOLD despite recovered messages | State-machine contract | Expected latch; explicit engagement needed |
| FAULT after malformed command | Frame base_link, finite velocities, inactive zero | Correct publisher, call reset, send fresh input, explicitly engage |
| Sequence rejected | Duplicate publisher or reused session | Stop competing sources; restart intended source with new UUID |
| Source changes repeatedly | `ros2 topic info /teleop/command --verbose` | Keep one publisher; no arbitration is implemented |
| Invalid integration interval | Timer configuration, VM pauses | Check max_dt/rate and scheduling; do not remove gap handling |
| Joints unchanged at boundary | Requested versus achieved, rejected flag | Expected unreachable step rejection; reverse input |
| Model dimensions wrong | Launch overrides/YAML vs standalone model | Launch shared configuration, not independent mismatched defaults |
| TF tree absent | joint_states names/stamps, robot_state_publisher log | Check namespace/remaps and model parse errors |
| Keyboard says interactive terminal required | stdin TTY and SSH session | Use separate interactive SSH terminal, not launch redirection |
| Terminal settings remain unusual | How process ended | SIGKILL cannot clean up; manually run `stty sane` |
| Optional bridge missing | `apt-cache policy ros-jazzy-foxglove-bridge` | Verify ARM64 candidate; keyboard mode does not need it |
| Bag replay does not reproduce motion | Active topics, services, receiver timing | Read RECORD_AND_REPLAY; output viewing is not input reproduction |
| Tests time out | launch log, localhost DDS discovery, VM load | Inspect actual process failure before widening timeouts |

Do not use sudo colcon, repeatedly initialize rosdep, source partial builds in
.bashrc, disable failing assertions, or treat an empty test result set as a pass.
No watchdog can make a stopped VM execute callbacks. No hardware is controlled.
