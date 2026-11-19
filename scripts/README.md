# Source Inspection

Authored, NOT RUN. Later on Ubuntu, from ~/handpilot:

```bash
python3 scripts/inspect_source.py
python3 scripts/inspect_source.py --transfer
```

Standard library only. Reads required paths, file sizes, basic UTF-8/LF hygiene,
XML syntax, manifest names, unset email, and obvious generated/secret-file names.
Does not modify files. Returns nonzero for errors; license TODO is a warning.
The initial unset maintainer emails are known errors, not passing results.

Normal mode skips generated directories and .git, making it suitable after a
build or in future CI. Transfer mode rejects their presence: use it on a clean
source staging copy, not the active Git checkout or built workspace. Neither
mode is a secret scanner, package validator, Xacro expander, build, test runner,
or security guarantee. Review archive contents manually as well.
