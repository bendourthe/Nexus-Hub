# Distribution Handbook Runner Review

This source review covers the Windows console-policy initialization added to the integration runner and its effect on the distribution handbook. It supplements the retained shared-budget content review and preserves the original build and browser evidence for unchanged handbook bytes.

## Source comparison

The reviewed runner SHA-256 is 4a39c230e4ada03a523dece54556c2e102fac6287069194128feda6b9b669320. Removing exactly the import of install_no_window_default, its invocation and the two separating blank lines at current lines 34-37 reconstructs SHA-256 03f2c090a6401552d215e0fb1c1556f9137d07e6db6a3e1f63c0bc316beddbbe, the runner named in the previous receipt. No other runner statement changes in that comparison.

The existing route paragraph already explains that both installers distribute nexus_process.py, whose Windows subprocess default hides console children and preserves output. The added runner initialization applies that same policy before platform adapter imports. The unchanged helper, SHA-256 682df4e0a79bbd5304cd6985eda7d23a93ddc711b61d28c146a106bd25992c7c, applies the default on Windows and returns without applying it on other hosts. It rejects detachment/new-console flags, adds CREATE_NO_WINDOW and preserves stream forwarding. The runner's platform/scope routing, adapter file shapes, ownership decisions and verification messages are unchanged by this four-line insertion.

The retained explanation therefore remains accurate in both views. No source paragraph, model, composition fragment or HTML change is needed for this delta. The previous content review at checker-budget-handbook-review.md remains part of the review chain; its SHA-256 is 262fe40390e5cef4db704c7a1794c76791dc7f876049ebd8d896980f7b5c074c. All other declared distribution inputs retain the hashes in the previous receipt.

## Existing runtime evidence

The retained observed-installer-1792854367384 packet binds this exact runner in plan.json and post-bindings.json, with SHA-256 36eca99c441c3fc502f550dc0d14d13a70b28a3e469b5a2e684c30a706f87f44 and a94eb86555b84b1d8354f1fa8a8ef3bb46c9986246ef9e098c7ff7e9dd7b26d8 respectively. Its qualification.json SHA-256 is ee729ca55593735bd36f6b98b52dab773d6840015a4b6c459d6437001637415b. The retained focused test selection returned 6 passed and 1 skipped; the explicit-target private Claude installation returned exit 0. Their result receipts have SHA-256 1380f2e2ef8b1eacebb1a10c930e8605bd193793b3c4b409523b80bc6a315f4c and 27e1d57e736cc03ffd3099386a13cbb6b6d9a49ae420b0858bc3cc9158fadcab. This is existing isolated Windows evidence, not a new execution or proof of global runtime adoption.

## Retained output provenance

The current output remains 105c97b8d3f46b2c2b97211a84259f72e5ed478bfd3349f925a706eabd3e61d1. All retained authoring inputs and six builder dependencies, including assets/theme.json, match the recorded build. The build artifact remains fdff266e42a7eb9003d0c1fc26e96fc12fbf65a17e65be74b45eeaf184a23822. The browser artifact remains 7101fb8f85a3391ce129d828ead2e44075cd07895e1cc05ed991495beefd6737 and retains its original Chromium 153.0.8010.12 scope, measurements and limitations. Neither artifact was rewritten or newly generated for this review. This source-only semantic review does not claim a new browser inspection, build execution, full-suite pass or release completion.
