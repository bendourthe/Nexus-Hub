#!/usr/bin/env python3
"""verify_imagery.py - v3.13.0 presentify imagery-and-interactivity CI verifier.

Standalone (no pytest), fully OFFLINE and deterministic: it exercises the
pure-function logic and the safety invariants of the two Tier 2 / Tier 3 helper
scripts without any network call, GPU, or optional dependency. Exits non-zero on
the first failed check.

Coverage:
  Tier 2 (fetch_stock_media.py)
    - the free-for-commercial-use license filter (allow-list; nc/nd rejection);
    - the CC / blanket attribution requirement and the attribution-string builder;
    - accept_candidate (https guard, nc rejection, blanket-source acceptance);
    - the credits-manifest / asset shape (via embed_candidates with a stubbed
      download - no network);
    - the consent-default-offline INVARIANT: main() with no --consent returns the
      degrade code, writes an empty degraded manifest, and calls NO network
      function (asserted with a stubbed transport that fails if reached).
  Tier 3 (generate_local_image.py)
    - the model license registry is all free-for-commercial-use;
    - parse_size (valid + out-of-range);
    - the degrade path: main() with no local runtime returns the degrade code and
      writes a degraded manifest (no network);
    - the static invariant that the script imports NO network / hosted-API client.
  Both
    - neither script imports a network module at top level (network is lazy /
      absent).

Note: content->keyword derivation is an AGENT-side authoring step (the agent
passes --query), not a script pure-function, so it is out of scope for this
offline verifier by construction.
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

def _repo_root(start: Path) -> Path:
    """Walk up to the repository root instead of hand-counting parent depth.

    A fixed ``parents[N]`` silently breaks whenever the file moves a level, and
    the v4.0.0 docs migration moved this tree one level deeper. Anchoring on a
    marker that only the root carries makes the location irrelevant.
    """
    for candidate in [start, *start.parents]:
        if (candidate / "AGENTS.md").is_file() and (candidate / "catalog").is_dir():
            return candidate
    raise RuntimeError(f"repository root not found above {start}")

REPO_ROOT = _repo_root(Path(__file__).resolve().parent)
SCRIPTS = REPO_ROOT / "catalog/skills/specialized-domains/document-to-interactive-html/scripts"
FETCH = SCRIPTS / "fetch_stock_media.py"
GENERATE = SCRIPTS / "generate_local_image.py"

PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA"
    "60e6kgAAAABJRU5ErkJggg=="
)

_checks = 0
_fails = 0


def check(cond: bool, label: str) -> None:
    global _checks, _fails
    _checks += 1
    if not cond:
        _fails += 1
        print(f"FAIL: {label}", file=sys.stderr)
    else:
        print(f"  ok: {label}")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def top_level_imports(src: str) -> list[str]:
    """Import statements at column 0 (module top level), not lazy in-function ones."""
    return [ln for ln in src.splitlines() if re.match(r"(import|from)\s", ln)]


def verify_tier2(tmp: Path) -> None:
    fsm = load_module(FETCH, "fsm_verify")

    # License filter (allow-list; nc/nd rejection).
    for code in ("cc0", "pdm", "by", "by-sa"):
        check(fsm.is_commercial_cc(code) is True, f"license '{code}' is free-for-commercial")
    for code in ("by-nc", "by-nc-sa", "by-nd", "by-nc-nd", "", "xx"):
        check(fsm.is_commercial_cc(code) is False, f"license '{code or 'empty'}' is rejected")

    # Attribution requirement + builder (no raw URL in the visible string).
    check(fsm.cc_requires_attribution("by") is True, "CC-BY requires attribution")
    check(fsm.cc_requires_attribution("cc0") is False, "CC0 needs no attribution")
    attr = fsm.build_attribution("Towers at dusk", "Jane Doe", "CC BY 4.0", "Openverse")
    check(attr == '"Towers at dusk" by Jane Doe, CC BY 4.0, via Openverse', "attribution string format")
    check("http" not in attr, "attribution string carries no raw URL")

    # accept_candidate: https guard, nc rejection, blanket-source acceptance.
    check(fsm.accept_candidate({"url": "http://x/y.png", "license": "by", "cc": True})[0] is False,
          "non-https asset rejected")
    ok_nc, reason = fsm.accept_candidate({"url": "https://x/y.png", "license": "by-nc", "cc": True})
    check(ok_nc is False and "free-for-commercial" in reason, "nc candidate rejected with reason")
    check(fsm.accept_candidate({"url": "https://x/y.jpg", "license": "pexels", "cc": False})[0] is True,
          "blanket-license (Pexels) candidate accepted")
    check(fsm.accept_candidate({"url": "https://x/y.jpg", "license": "mystery", "cc": False})[0] is False,
          "unknown non-CC source license rejected")

    # Credits-manifest / asset shape via embed_candidates with a stubbed download.
    fsm._http_get_bytes = lambda url, max_bytes: (PNG_1x1, "image/png")
    cand = {"source": "Openverse", "url": "https://x/y.png", "title": "Cooling towers",
            "author": "Jane Doe", "license": "by", "license_version": "4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "landing": "https://openverse.org/image/1", "width": 12, "height": 8, "cc": True}
    notes: list[str] = []
    assets = fsm.embed_candidates([cand], 1, 2_000_000, notes)
    check(len(assets) == 1, "embed_candidates embeds an accepted candidate")
    a = assets[0]
    check(a["data_uri"].startswith("data:image/png;base64,"), "asset is a base64 data: URI")
    check(set(a) >= {"data_uri", "alt", "width", "height", "provenance"}, "asset shape has required keys")
    p = a["provenance"]
    check(p["tier"] == "stock" and p["source"] == "Openverse", "provenance tier + source")
    check(p["license"] == "CC BY 4.0", "CC-BY license label built")
    check(p["attribution"].startswith('"Cooling towers" by Jane Doe'), "provenance attribution string")

    ncc = dict(cand, license="by-nc", url="https://x/z.png")
    notes2: list[str] = []
    check(fsm.embed_candidates([ncc], 1, 2_000_000, notes2) == [], "non-commercial candidate not embedded")

    # Consent-default-offline invariant with a stubbed transport that fails if reached.
    def boom(*args, **kwargs):
        raise AssertionError("network reached without --consent")

    fsm._http_get_json = boom
    fsm._http_get_bytes = boom
    out = tmp / "no_consent.json"
    rc = fsm.main(["--query", "cooling towers", "-o", str(out)])
    check(rc == fsm.EXIT_DEGRADE, "no --consent -> degrade exit code")
    man = json.loads(out.read_text(encoding="utf-8"))
    check(man.get("degraded") is True and man.get("assets") == [], "no --consent -> empty degraded manifest")

    # No top-level network import (lazy inside functions only).
    top = top_level_imports(FETCH.read_text(encoding="utf-8"))
    net_top = [ln for ln in top if re.search(r"\b(requests|urllib)\b", ln)]
    check(not net_top, "fetch_stock_media has no top-level network import")


def verify_tier3(tmp: Path) -> None:
    gli = load_module(GENERATE, "gli_verify")

    check(all(m["license"] in gli.COMMERCIAL_LICENSES for m in gli.MODELS.values()),
          "all Tier-3 models carry a free-for-commercial-use license")
    check(gli.parse_size("800x600") == (800, 600), "parse_size parses WxH")
    bad = False
    try:
        gli.parse_size("10x10")
    except ValueError:
        bad = True
    check(bad, "parse_size rejects an out-of-range size")

    # Degrade path: no local runtime + no configured CLI -> degrade, no network.
    os.environ.pop("NEXUS_LOCAL_IMAGE_CMD", None)
    out = tmp / "ai.json"
    rc = gli.main(["--prompt", "clinical lab, cool minimal palette", "-o", str(out)])
    check(rc == gli.EXIT_DEGRADE, "no local runtime -> degrade exit code")
    man = json.loads(out.read_text(encoding="utf-8"))
    check(man.get("degraded") is True, "no local runtime -> degraded manifest")

    # Static invariant: no network / hosted-API client import anywhere.
    src = GENERATE.read_text(encoding="utf-8")
    forbidden = ["requests", "urllib", "httpx", "http.client", "aiohttp", "socket",
                 "websocket", "openai", "replicate", "boto3"]
    imp = top_level_imports(src) + [ln for ln in src.splitlines() if re.match(r"\s+(import|from)\s", ln)]
    hits = [f for ln in imp for f in forbidden if re.search(r"\b" + re.escape(f) + r"\b", ln)]
    check(not hits, f"generate_local_image imports no network/hosted client (found: {hits})")


def main() -> int:
    print("verify_imagery: Tier 2 / Tier 3 offline pure-function + invariant checks")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        verify_tier2(tmp)
        verify_tier3(tmp)
    print(f"\nverify_imagery: {_checks} checks, {_fails} failure(s).")
    return 1 if _fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
