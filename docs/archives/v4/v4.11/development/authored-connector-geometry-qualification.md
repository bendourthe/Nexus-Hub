# Authored connector geometry qualification

**Scope**: This v4.11 MT-10 qualification uses the retained `report-final/pilot.html` from the Phase 6 native attempts. It tests actual authored process diagrams, not the distribution handbook's navigation icons or a synthetic fixture.

The pilot contains 25 SVGs. Zero-indexed SVGs 7 and 8 are the horizontal and vertical process diagrams; SVGs 17 and 18 repeat those layouts. Each has four labeled boxes, three straight connector paths, a curved return path, and a marker definition. The horizontal straight paths use `M` and `H`; the vertical paths use `M` and `V`. Both return paths use `C`. The source artifact remains unchanged.

Running `check_svg_label_occlusion` and `check_svg_connector_routing` on each of those four isolated SVG blocks returned `unchecked`, with `checked_svgs: 0` and the reason `carries geometry this check cannot decide`. The whole pilot page also returned `unchecked` for both checks, with zero checked SVGs. This is expected under the declared envelope: `_GEOM_UNSUPPORTED_RE` rejects any `<path>` before coordinate work. It is not evidence of a clear diagram or of a routing defect.

From the repository root, this PowerShell command reproduces the isolated result without modifying the pilot:

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, 'catalog/skills/specialized-domains/document-to-interactive-html/scripts')
import visual_qa_score as scorer
html = Path('docs/releases/v4/v4.11/development/interactive-handbooks/phase-6-native-attempts/report-final/pilot.html').read_text(encoding='utf-8')
blocks = scorer._svg_blocks(html)
for index in (7, 8, 17, 18):
    for name, check in (('occlusion', scorer.check_svg_label_occlusion), ('routing', scorer.check_svg_connector_routing)):
        result = check(blocks[index])
        print(index, name, result['status'], result['coverage']['checked_svgs'])
'@ | python -
```

The command prints eight `unchecked 0` results, one for each diagram and check.

The result qualifies MT-10 against a real authored connector artifact and narrows the remaining design choice. Parsing exact `M`/`L`/`H`/`V` segments alone would still leave these SVGs partly undecidable because the same diagrams contain cubic return paths. A future implementation needs an explicit partial-coverage contract or exact treatment of the full path geometry, with a negative crossing fixture and no curve approximation. Until then, retain `unchecked` rather than emitting a confident pass for an incomplete diagram.
