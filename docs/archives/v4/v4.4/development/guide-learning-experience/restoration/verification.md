# v4.4.5 restoration and corrected visual scope

Status: v4.4.5 restored in the working tree at the user's direction. The v4.4.6 content/structure redesign is rejected and superseded, not an approved product baseline. Its prior evidence and commits remain historical. No new visual changes have been applied on top of the restored guide.

## Restoration evidence

Baseline: bdd57cee4eb776304a09e862c1d956534db59e1e, the v4.4.5 closeout. The guide is byte-identical to that revision: 396424 bytes, SHA-256 68f017bcac2a7c58278ce3ad7642f5860279784707e3ef4ee5fef15c8d39ec7d. Canonical Training data and the maintainer README also match byte for byte. All 59 baseline guide/test files match after normalizing Git checkout line endings. See restoration.json and baseline-tree-parity.json.

Home, Foundations, and Training were opened in desktop/light and mobile/dark views: six cases, zero page errors and horizontal-overflow cases. All six screenshots were actually inspected; they establish restoration and visible top-section layout, not a clean design verdict or proof about all offscreen animation states. The restored guide suite completed with 340 passed, one optional skip and four inherited Python escape-sequence warnings in 333.01s; see guide-tests.txt. Browser execution was required with NEXUS_REQUIRE_RENDER=1.

## Corrected scope

Preserve v4.4.5's sections, order, headings, explanations, examples, and teaching coverage. Do not merge sections, replace the page with a new learning outline, move existing content into hidden disclosures, or pursue a page-wide word-count reduction. The user's request is refinement of specific visuals, not replacement of the guide's content.

Work on one named existing illustration or animation at a time. Prioritize Foundations animation lag and the existing model, tokens, context, platform, and harness figures according to the user's chosen areas. Home work should improve its existing illustrations and readability within the current structure. Training should retain its existing walkthrough and receive only targeted requested visual refinements. Any copy change must be small, local, and necessary to the selected illustration.

Before each visual edit, retain the current section screenshot and its text/heading inventory. After the edit, compare the same scene at 1440x900 and 420x900 in both themes, inspect the relevant breakpoint seams, and check natural wrapping, label fit, spacing, alignment, contrast, and animation states. Check reduced motion and visible/offscreen behavior where animation changes. Preserve the baseline section inventory and substantive text; tests must protect that preservation rather than be rewritten to permit deleted teaching material.

Measure animation work before changing its scheduling. A lag fix should remove unnecessary work while retaining the illustration's intended explanation. Do not conflate less visible content with better performance.

## Current disposition

The previous three-fix v4.4.6 temporary candidate and its approval request are superseded. The seven-phase content-rebuild plan must not resume. Further visual refinement will use the restored v4.4.5 file and this corrected scope. The user has been asked which existing areas to prioritize; no additional redesign is inferred from the restoration request. Unrelated planning files remain untouched, and Git history has not been rewritten.
