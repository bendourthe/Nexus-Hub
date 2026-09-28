# Phase 5 evidence - IDE training workbench

**Date**: 2026-08-29

Maintainer fixtures: `guides/website/example/training-scenes.json`. The guide inlines a verified copy in `#nh-training-scenes` with `</script>` encoded. Training is one `wb-` workbench updated by `applyState(scene, beat)` using `textContent`. Eight scenes. URL: `#training/<scene>?beat=n` with `replaceState` for beats. No autoplay, no fullscreen, no cinematic engine. Browser QA remains DF-1.

`node --check` on the extracted workbench controller passed. Focused tests: 27 passed.
