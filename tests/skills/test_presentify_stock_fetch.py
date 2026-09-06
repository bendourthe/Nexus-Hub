"""v3.15.4 Phase 4: reliable stock/mix imagery integration.

Covers the enforcement layer the integration behavior rests on, in
`scripts/fetch_stock_media.py`:

- The load-bearing CONSENT gate: no `--consent` means no network and a degraded
  manifest (exit 3), so the run stays on Tier 1 (procedural).
- The free-for-commercial-use license allow-list: CC0 / PD / BY / BY-SA and the
  blanket sources pass; any NonCommercial / NoDerivatives term is rejected.
- Degrade-with-a-reason: every zero-integration path writes a `reason`, so the
  integration gate never sees "zero-integration with no reason" silently.
- A consented run integrates and credits a base64-embedded asset (offline).

The network functions are monkeypatched, so these tests make NO real network
call and need no `requests` dependency (they run in both the deps-light ci.yml
tests job and the presentify-extractor workflow). The helper is loaded by path
via importlib, matching test_media_key_setup.py.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_FETCH_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "fetch_stock_media.py"
)

# A 1x1 PNG, so the mocked download returns real decodable image bytes.
_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch = _load(_FETCH_PATH, "fetch_stock_media_p4")


def _openverse_response(license_code: str) -> dict:
    return {
        "results": [
            {
                "url": "https://example.org/photo.png",
                "title": "Cooling towers at dusk",
                "creator": "Jane Doe",
                "license": license_code,
                "license_version": "4.0",
                "license_url": "",
                "foreign_landing_url": "https://example.org/landing",
                "width": 1,
                "height": 1,
            }
        ]
    }


def _mock_network(monkeypatch, response: dict) -> None:
    monkeypatch.setattr(fetch, "_http_get_json", lambda url, params, headers: response)
    monkeypatch.setattr(
        fetch, "_http_get_bytes", lambda url, max_bytes: (_PNG_BYTES, "image/png")
    )


# --- consent gate (load-bearing) --------------------------------------------


def test_no_consent_no_network_degrades(tmp_path, monkeypatch):
    # Any network call would be a bug: fail loudly if one is attempted.
    def _boom(*args, **kwargs):
        raise AssertionError("network called without --consent")

    monkeypatch.setattr(fetch, "_http_get_json", _boom)
    monkeypatch.setattr(fetch, "_http_get_bytes", _boom)
    out = tmp_path / "m.json"
    rc = fetch.main(["--query", "cooling towers", "-o", str(out)])
    assert rc == fetch.EXIT_DEGRADE
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["degraded"] is True
    assert manifest["assets"] == []
    assert "consent" in manifest["reason"].lower()


# --- consented happy path (integrate + credit + offline) --------------------


def test_consented_openverse_integrates_and_credits(tmp_path, monkeypatch):
    _mock_network(monkeypatch, _openverse_response("cc0"))
    out = tmp_path / "m.json"
    rc = fetch.main(["--query", "cooling towers", "--consent", "-o", str(out)])
    assert rc == fetch.EXIT_OK
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["degraded"] is False
    assert len(manifest["assets"]) == 1
    asset = manifest["assets"][0]
    # Offline: the asset is base64-embedded, not a hotlink.
    assert asset["data_uri"].startswith("data:image/png;base64,")
    prov = asset["provenance"]
    assert prov["source"] == "Openverse"
    assert prov["license"].startswith("CC0")  # "CC0" or "CC0 4.0"
    assert prov["tier"] == "stock"


# --- license allow-list (fails safe) ----------------------------------------


def test_license_allow_list_rejects_noncommercial(tmp_path, monkeypatch):
    _mock_network(monkeypatch, _openverse_response("by-nc"))
    out = tmp_path / "m.json"
    rc = fetch.main(["--query", "cooling towers", "--consent", "-o", str(out)])
    # An NC asset is rejected; the run degrades WITH a recorded reason.
    assert rc == fetch.EXIT_DEGRADE
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["assets"] == []
    assert manifest["reason"], "a zero-integration run must record a reason"
    assert "commercial" in manifest["reason"].lower()


@pytest.mark.parametrize(
    ("code", "allowed"),
    [
        ("cc0", True),
        ("pdm", True),
        ("by", True),
        ("by-sa", True),
        ("by-nc", False),
        ("by-nd", False),
        ("by-nc-sa", False),
        ("", False),
        ("unknown", False),
    ],
)
def test_is_commercial_cc(code, allowed):
    assert fetch.is_commercial_cc(code) is allowed


def test_accept_candidate_rejects_nc():
    cand = {
        "url": "https://example.org/x.jpg",
        "license": "by-nc",
        "source": "Openverse",
        "cc": True,
    }
    ok, reason = fetch.accept_candidate(cand)
    assert ok is False
    assert "commercial" in reason.lower()


# --- degrade always carries a reason (feeds the integration gate) -----------


def test_zero_results_degrades_with_reason(tmp_path, monkeypatch):
    _mock_network(monkeypatch, {"results": []})
    out = tmp_path / "m.json"
    rc = fetch.main(["--query", "no such thing", "--consent", "-o", str(out)])
    assert rc == fetch.EXIT_DEGRADE
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["assets"] == []
    # The gate relies on this: zero integration is NEVER silent.
    assert manifest["reason"], "degrade manifest must record a reason"
