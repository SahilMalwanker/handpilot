# Source Inspection

Runs with 0 errors on the target (license TODO warnings remain). From ~/handpilot:

```bash
python3 scripts/inspect_source.py
python3 scripts/inspect_source.py --transfer
```

Standard library only. Reads required paths, file sizes, basic UTF-8/LF hygiene,
XML syntax, manifest names, unset email, and obvious generated/secret-file names.
Does not modify files. Returns nonzero for errors; license TODO is a warning.

Normal mode skips generated directories and .git, making it suitable after a
build or in future CI. Transfer mode rejects their presence: use it on a clean
source staging copy, not the active Git checkout or built workspace. Neither
mode is a secret scanner, package validator, Xacro expander, build, test runner,
or security guarantee. Review archive contents manually as well.

# README Media

`readme_media/` regenerates the images used by the top-level README.

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
python3 scripts/readme_media/record_demo.py docs/media/demo_session.csv
python3 scripts/readme_media/render_media.py docs/media/demo_session.csv docs/media
```

`record_demo.py` starts its own `controller_node` in a private namespace, plays a
fixed operator script and records every `controller/status` message to CSV.
`render_media.py` needs only Pillow: it draws `handpilot_demo.gif` from that
recording and computes the IK and pipeline SVGs. Each re-recording differs
slightly because VM scheduling differs. Keep each asset under 512 KiB.
