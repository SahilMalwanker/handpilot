# Future Camera Integration

PLANNED ONLY. There is no webcam capture, hand tracking, fake input adapter,
camera ROS publisher, inference dependency, or camera transport implementation.
Keyboard v0.1 requires none of these.

## Proposed Boundary

A future Mac-side adapter would capture the webcam locally, map an explicitly
calibrated gesture to a bounded Cartesian velocity in base_link, and publish
the existing TeleopCommand contract. It must not publish absolute pixel coordinates
as meters, absolute target positions as velocities, or write simulated joint state.
Confidence loss must produce inactive/zero input. Terminal keys and camera gestures
are alternative sources, not simultaneous controllers.

Each adapter process creates a new source/session ID and monotonically increasing
sequence. Header ROS time remains observational; it cannot be substituted for
receiver-side freshness across Mac/VM clocks. Reconnect, source change, tracking
loss, and fault recovery must not auto-engage. Explicit engagement intent must be
designed and tested separately from detecting a hand. Reset stays a separate service.

## Transport Decision Still Open

Possible options: a genuine ROS 2 adapter with compatible message bindings, or
Mac capture plus a real rosbridge JSON/WebSocket client talking to an optional
rosbridge_server in Ubuntu. Foxglove Bridge is a different protocol and must not
be silently substituted. No transport is advertised as implemented or verified.

Evaluate ARM64 binary availability, message schema support, ROS/DDS versus WebSocket
latency, queue limits, reconnect handling, and access controls before selection.
Prefer local loopback/SSH-tunneled connectivity where suitable; a source ID is not
authentication. Receiver arrival cannot distinguish fresh intent from transport delay.
An age/acknowledgment protocol would need explicit clock-domain and security design.

## Acceptance Milestones

1. Document camera orientation, axes, calibration, units, confidence threshold,
   privacy/storage defaults, and explicit enable/stop gesture behavior.
2. Test pure mapping offline with synthetic inputs: no image/model downloads or
   camera required for those unit tests. Do not call this a working camera adapter.
3. Implement one actual capture/transport path after approval, with resource cleanup
   and bounded queues. Verify dependencies and memory on Mac and VM separately.
4. Measure real capture-to-receiver latency/jitter and loss behavior; record methods
   and results rather than inventing them.
5. Test frozen video, lost tracking, disconnection, delayed frames, process restart,
   competing sources, invalid values, and explicit re-engagement after every stop.

Do not store personal footage by default. Review data rights, model licensing,
privacy, network exposure, and dependency size before publication.
