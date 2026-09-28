# Training layout follow-up verification

This archived record covers the bounded post-release repair of v4.4 guide findings BG-46 and BG-47. It is for maintainers checking the mobile Training heading and the fullscreen terminal's idle and completed states; it does not certify the separate reader-comprehension, native zoom, Linux browser, or full-profile gates.

The source scene and inline guide scene both say "Trace the damage". The shipped describe reply no longer contains the hostile test sentence, which is covered by test-local browser data in the separate BG-48 repair. The final guide SHA-256 at local verification is `c21fd8463b34613cdeec6e15004e95026306242c4cd79fc60ce5f4d84ecc2f9b`.

`NEXUS_REQUIRE_RENDER=1 python -m pytest tests/guides/test_v446_training_layout_followup.py tests/guides/test_v441_phase6_workspace.py -q` passed 23 browser tests. The new cases check 320 and 420 px in both themes for an isolated final heading word or horizontal overflow, and 1280x720, 1366x768, 1440x900, and 1920x1080 in both themes for a compact idle terminal, visible post-Run output, scroll access to the last reply line, and no horizontal overflow. The existing 0.88 desktop coverage floor now measures the completed-reply state; the compact idle state has its own gate. The first run exposed this state mismatch at 1920x1080 and 1440x900; the corrected test passed without reducing the floor.

The six screenshots below were captured from that guide hash with Chromium in reduced-motion mode and visually inspected. At 420 px the title has no isolated word; at 1440x900 the idle reply is compact, and after Run the reply text is complete with no observed collision in either theme. The remaining viewport cases have measured browser assertions, not screenshots.

| State | Light | Dark |
|---|---|---|
| Mobile 420x900 | [mobile-light.png](mobile-light.png) | [mobile-dark.png](mobile-dark.png) |
| Fullscreen idle 1440x900 | [idle-light.png](idle-light.png) | [idle-dark.png](idle-dark.png) |
| Fullscreen after Run 1440x900 | [after-light.png](after-light.png) | [after-dark.png](after-dark.png) |

Screenshot SHA-256 values, in the table's row order: `d9fee0a5fd4ead8910da7cff4e1b32616e3aaa12cb1c0417360adf118e26e692`, `93db9142745deb0796a7e105f1fb6d059cac222c2ccd116a3e0ca0216720c0c4`, `e43fd8c9df716a4f08d08832ed13cad340340c8815e2aa6c9e2c66231b1dbe0a`, `bd63b8395b8a7bfe63ee915301b77895477d6dae60a86e817a13f404c1a31ec3`, `68eb36e66a6931abcb022f11eaa0774c11959d44dbe087e02052b58a8de6ed9a`, `d28742b9479302f05ef72995af6a784412c4114c20b0b31411160450f5cf920e`.

Publication and post-merge validation remain separate gates. The larger v4.4 guide-learning-experience directory remains active because its manual and environment-dependent gaps are unresolved; only this completed evidence slice is archived.
