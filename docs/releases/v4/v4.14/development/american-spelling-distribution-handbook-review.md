# Distribution Handbook Spelling Verification

**Covers**: why the distribution handbook needs no content change for the American-spelling conversion, and the evidence behind refreshing its `scripts/installer.sh` input digest.

The American-spelling conversion changes one mapped distribution input. In `scripts/installer.sh`, the comment above the top-level section banner helper reads `the bash analog of the` instead of `the bash analogue of the`. `git diff -U0 -- scripts/installer.sh scripts/installer.ps1 install.sh install.ps1` shows exactly that one line, and the line count is unchanged, so no installer line citation moves.

The handbook explains distribution, settings ownership, attributed identity, and verification boundaries. No handbook text quotes that comment or describes the banner helper (`git grep -i -E 'analog|write_subsection_banner' -- docs/handbooks` returns nothing), so no handbook text or rendered output changes. Only the `scripts/installer.sh` input digest in `docs/handbooks/_sources/distribution/evidence.json` is refreshed, and this record becomes the content check's evidence. No new browser run is claimed; the existing rendered evidence still applies because the handbook output is unchanged.
