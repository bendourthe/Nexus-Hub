# Handbooks

These living handbooks explain Nexus-Hub's catalog and installation code for maintainers and users tracing how a capability reaches their assistant.

- [Catalog overview](overview.html): authoring, validation, delivery and evidence.
- [Installation and ownership](distribution.html): platform shapes, naming, managed files and verification.

Both include a complete reading view and Presentation Mode. `handbooks.json` maps their retained models, editable Markdown, design files, code dependencies, builder commands and review evidence. Edit mapped inputs under `_sources/`, then use each entry's build and check command from the repository root. Generated HTML is never hand-edited. The map is authoritative; topic layouts and existing Markdown/HTML pairs remain supported without migration.

Run `python scripts/check_release_preconditions.py --handbooks` after refreshing code claims and final browser evidence. Missing or stale sources, output or evidence block completion. At release close, snapshot the map, rebuild inputs and verified outputs for the version they describe; keep this living tree in place. See the [mapped-source decision](../decisions/implemented/architecture/2026-09-09-mapped-handbook-sources-and-candidate-freshness.md).
