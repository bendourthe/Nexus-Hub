# Distribution Handbook Attribution Stream Review

This source review covers the explicit fallback-hook stream forwarding in the PR #528 candidate at revision 27340401a7c61e59153d7038ddaa4ec03d6541da. It supplements the retained distribution content review and preserves the existing build and browser artifacts for unchanged handbook bytes.

## Source Comparison

The attribution helper has canonical LF SHA-256 66d64f0f49ea6cb12e95c85f2cc12d0c0fdccdd238a458f20f5bb8b6090cef7f. Removing exactly one addition, stdout=sys.stdout and stderr=sys.stderr on the subprocess.run call in hook_run, reconstructs the previously reviewed canonical hash 70fd7de79ec97cfb73c70c468a88932e16a4e1c27027ab1278f4e32ac34ac4ba. No other helper statement changes. Command construction, CREATE_NO_WINDOW, input=payload, check=False and propagation of the original hook's return code remain unchanged.

The explicit streams forward an existing hook's stdout and stderr through the current Python streams when its Windows child is hidden. This preserves the hook's diagnostics; it introduces no new process launch or identity override. The retained source explains that the Windows policy hides console children and preserves output, and that human identity and existing hooks are preserved. Those claims remain accurate in the reading and presentation views. No authored source, composition, model or HTML change is needed for this delta. The other 25 declared distribution inputs match the previous receipt.

## Existing Runtime Evidence

The retained merged-flow proof at %TEMP%/nexus-v4140-native-hook-budget-oct17/merged-console-verification-178659ef/verified-merged-flows.json has SHA-256 b271597112c7bc33e328b218c88c129893c9eb6ffc251465f88b1954004363db. Its 116 passing cases include the existing-hook regression that asserts both stdout and stderr markers while retaining the original hook failure and rollback checks. That proof also records the isolated Claude/minimal workspace installer and desktop observation. It does not establish whole-matrix qualification, real-home adoption or native authorization. This review starts no additional test or installer.

## Output Provenance

The handbook remains 105c97b8d3f46b2c2b97211a84259f72e5ed478bfd3349f925a706eabd3e61d1. All retained authoring inputs and all six dependencies in the build report, including assets/theme.json, match that report. The fresh canonical builder --check exited 0 in 1.633 seconds without a timeout and reported this same output hash. The retained terminal under %TEMP%/nexus-v4140-native-hook-budget-oct17/kernel-recovery-e53539b9/distribution-build-readonly.terminal.json has raw SHA-256 1884b70f12dc88b2242f5b4a8f2324fa28fee5f2bc2d4b1ac39a134cfbbe16f2; its stderr log has raw SHA-256 9b5aedbe61d73a8918af031c000b2fc4209fb597969e1077f324f5937681e405. This was a read-only reproduction check, not regeneration of the handbook or its build report.

The build artifact remains fdff266e42a7eb9003d0c1fc26e96fc12fbf65a17e65be74b45eeaf184a23822. The browser artifact remains canonical LF SHA-256 7101fb8f85a3391ce129d828ead2e44075cd07895e1cc05ed991495beefd6737 and retains its original Chromium 153.0.8010.12 scope, measurements and limitations. No new browser inspection is claimed. The previous content review, windows-runner-handbook-review.md, remains in the review chain at canonical LF SHA-256 b2f5c3451ea6c3f754517eef70df0a3c0c54417365bfb5c9d2413c1f5e9a9d33. No full-suite, CI pass or release completion is claimed by this attestation.
