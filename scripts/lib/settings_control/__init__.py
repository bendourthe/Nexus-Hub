"""Nexus-Hub Settings engine: one catalog, one read side, one command-line front end.

`catalog.py` loads the admission catalog, `readers.py` snapshots the tool config
files, `resolve.py` turns a snapshot into one state per control and tool, and
`report.py` renders it. The package uses relative imports only, so it loads both
as `scripts.lib.settings_control` (tests) and as `settings_control` (the installed
CLI, which adds `scripts/lib` to `sys.path`).
"""
