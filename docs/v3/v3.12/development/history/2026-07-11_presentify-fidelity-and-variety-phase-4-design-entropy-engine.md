# Session History - presentify-fidelity-and-variety Phase 4: Design-entropy engine and run history

**Date**: 2026-07-11
**Plan**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md`
**Phase**: 4 of 6 (non-final)
**Model**: Fable 5, high effort per the plan's recommendation (no routing delta)

## What was done

- **4.1 Sampler** (`scripts/design_seed.py`, new, stdlib-only): axis pools (12 hue families x light/dark bases with curated hexes + 2 accents each; 8 moods; 8 system-stack type voices; 10 described layout signatures; 4 motion personalities; 8 signature moves; 3 spacing rhythms); preset subsets (corporate / creative / technical / surprise); `os.urandom` default seed with `--seed` reproduction; candidate rolling with the 2-of-{hue, layout, voice} rejection against the last 3 history entries, single pool-widening retry, and max-distance pick; the dark+amber+mono attractor guard (unreachable under named presets; 5% deliberate odds under surprise only); `--commit BRIEF` appends used briefs to `~/.nexus-hub/state/presentify-design-history.json` (cap 40, corrupt-file fresh-start recovery); brief output with concrete palette hexes, CSS stacks, layout/move descriptions, and a one-line summary embedding the seed.
- **4.2 Roll-then-adapt wiring**: `references/interactive-features.md` design flow gained the roll step (usage, no-silent-re-roll, `--commit`, no-Python manual fallback: vary hue family + layout signature away from the last run and say so); the "generate candidates" brainstorm reframed as "adapt the brief"; the token record now includes seed + summary. SKILL.md: roll bullet in the design step, the "I have good taste, I don't need the roll" rationalization row, two verification items (seed/summary/token-brief consistency; history advanced). `catalog/commands/presentify.md`: the design-menu section states same-preset reruns still differ.
- **4.3 Verification** (`verify_design_seed.py`, committed to the fixture kit; temp-dir histories only).

## Test results

10/10 PASS: (1) five sequential committed technical rolls never share 2+ of {hue family, layout signature, type voice} against their trailing window; (2) the five runs span 4+ hue families; (3) `--seed 42` twice yields identical briefs; (4) seed 43 differs; (5) history capped at exactly 40 after 45 commits; (6) corrupt history file -> stderr warning + fresh roll, exit 0; (7) 60 seeded technical rolls stay inside the preset's mood/voice subsets; (8) both light and dark bases appear across the sample; (9) 240 seeded rolls across technical/corporate/creative never produce the dark+amber-ember+mono-technical attractor; (10) every brief carries hex palette, CSS type stacks, and a summary. Ruff clean (autofix + format applied); bundle audit 0 errors; unicode 0 errors.

## Deviations

- None.

## Known-gaps delta

- No new gaps. Header updated (Phase 4 complete). DF-1/2/3, WN-1/2/3, MT-1 unchanged.

## Environment notes

- Installer-neutral: the new script lives in the skill bundle's auto-copied `scripts/` directory (AGENTS.md distribution table row 1); no installer edit, no `.ps1` sibling needed (single cross-platform `.py`).

## Next steps

- Phase 5: coverage-reconciliation + data-fidelity verification wiring, the end-to-end worked example replaying the PDF-from-PowerPoint failure case, the two-run same-preset divergence proof (now mechanically backed by this phase's engine), and registration/CHANGELOG sync.
