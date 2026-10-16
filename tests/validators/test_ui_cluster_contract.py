"""Keep design-system measurement ownership singular across the UI cluster."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLUSTER = ROOT / "catalog/skills/developer-experience"


def test_design_contract_has_one_owner_and_complete_handoffs():
    names = ("interface-review", "hallmark-design", "layout-and-spacing", "color-systems")
    bodies = {name: (CLUSTER / name / "SKILL.md").read_text(encoding="utf-8") for name in names}
    owner = bodies["interface-review"]
    assert re.search(
        r"^\| Design-system lint execution and coverage \| `interface-review` \| .+ \|$",
        owner,
        re.MULTILINE,
    ), "register the machine-check concern in the canonical ownership table"
    reference = CLUSTER / "interface-review/references/design-system-contract.md"
    assert reference.is_file()
    assert "references/design-system-contract.md" in owner
    for name, body in bodies.items():
        assert "[[multi-agent-code-review]]" in body, name
        verification = body.split("## Verification", 1)[1].split("## Related Skills", 1)[0]
        if name == "interface-review":
            assert "npm exec --no -- stylelint" in verification
        else:
            assert "Design-system lint: hand off to `interface-review`" in body, name
            assert "npm exec --no -- stylelint" not in verification, name
    text = reference.read_text(encoding="utf-8")
    config = json.loads(re.search(r"```json\n(.*?)\n```", text, re.DOTALL).group(1))
    assert config["rules"]["declaration-property-value-allowed-list"][1]["message"]
    assert "States" in text and "Defers" in text
    for name in ("web-typography", "interface-copy", "accessibility-engineering"):
        assert f"Not wired: `{name}`" in text
    assert "ui-component-generation" in text
    assert "theme-tokens" in text and "brand-styling" in text
    assert "Rejected alternative" in text
