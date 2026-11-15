# Distribution Handbook Verification - Codex Memories levers

**Covers**: why the distribution handbook needs no content change for the v4.14.5 T007 and T008 change to `configs/platform-defaults.json`, and the evidence behind refreshing that input digest.

The change adds six entries to the Codex `omitted` map of `configs/platform-defaults.json` (the five Codex Memories keys and the legacy alias `memories.no_memories_if_mcp_or_web_search`), a `meta.omitted` rule, and a new `last_updated` date. `omitted` keys are never seeded, so no platform's installed settings change: `python scripts/sync_platform_defaults.py --check` reports every derived artifact in sync.

The handbook explains distribution, settings ownership, attributed identity, and verification boundaries. It does not mention omitted keys, Codex Memories, or the contents of `configs/platform-defaults.json`, and no claim it makes depends on them, so no handbook text or rendered output changes. Only the `configs/platform-defaults.json` input digest in `docs/handbooks/_sources/distribution/evidence.json` is refreshed, and this record becomes the content check's evidence. No new browser run is claimed; the existing rendered evidence still applies because the handbook output is unchanged.
