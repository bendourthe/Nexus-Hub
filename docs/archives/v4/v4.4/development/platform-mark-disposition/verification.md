# v4.4 DF-1 Platform-Mark Disposition

The v4.4.0 ledger accurately recorded three text treatments at its release checkpoint. The later v4.4.1 rebuild fulfilled the named condition: ChatGPT, Gemini, and GitHub Copilot now appear with the other two approved marks in the shipped five-item Home rail. This record closes the stale carry-forward entry without rewriting its original observation or approving a new vendor asset.

## Approval and artifact

The [v4.4.1 asset ledger](../../../../../releases/v4/v4.4/development/guide-visual-and-arcade-rebuild/asset-provenance.md) records maintainer approval on 2026-09-01 and sanitized SHA-256 hashes for Claude, ChatGPT, Gemini, Cursor, and GitHub Copilot. It identifies the source and licensing or trademark treatment of each asset, including the two documented substitutions, and records review of a rendered both-theme contact sheet. The current [guide](../../../../../../guides/website/nexus-hub-guide.html) carries five marks; its Home rail labels the products, and the byte-identity tests resolve local symbol references before comparing the embedded geometry with the approved files.

## Fresh verification, 2026-09-24

- `python -m pytest -q tests/guides/test_v441_phase1_contract.py tests/guides/test_v441_phase2_home.py`: 47 passed. The suite verifies the five approved hashes, safe vector staging, visible Home geometry at four viewport widths, and rail layout. Two existing Python invalid-escape SyntaxWarnings appeared; no test failed.
- `python -m pytest -q tests/guides/test_nexus_hub_guide.py::test_home_lists_the_five_approved_platforms_from_ledger_bytes tests/guides/test_nexus_hub_guide.py::test_shared_platform_symbol_viewbox_change_fails_approval`: 2 passed. These resolve the embedded symbols to the approved asset bytes and prove that a symbol-styling mutation fails approval.
- `python -m pytest -q tests/guides/test_phase6_verification_sweep.py::test_all_pages_meet_contrast_and_overflow_matrix`: 1 passed. This exercises the current guide in Chromium across both themes and the release viewport matrix; it is a browser gate, not just a markup inspection.

No guide, asset, test, or distributed behavior changed in this follow-up. A future asset replacement requires new provenance and approval; this disposition only establishes that the v4.4.0 text-treatment condition was resolved by v4.4.1.
