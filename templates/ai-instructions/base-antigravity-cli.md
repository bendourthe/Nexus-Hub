@base-antigravity-20.md

## Surface note: Antigravity CLI (standalone)

This file is a thin alias for `base-antigravity-20.md`. The Antigravity CLI and the Antigravity 2.0 desktop IDE share a backend and on-disk conventions per the 2026-05-21 Google Developers Blog announcement (legacy migration-source path `docs/archive/v2/v2.2/antigravity-cli-probe.md`), so the `Antigravity20Integration` in `scripts/lib/integrations/antigravity.py` covers both surfaces with a single class.

This wrapper exists as a placeholder for a hypothetical future split where Google diverges the CLI from the desktop. Until then, the Antigravity 2.0 integration is the canonical Antigravity CLI integration.

- Binary / invocation: `agy --help`, `agy -p '<prompt>'` (verified 2026-05-29; the CLI ships as `agy`, not `antigravity`)
- Migration timeline: non-enterprise Gemini CLI users transition to Antigravity CLI before 2026-06-18
