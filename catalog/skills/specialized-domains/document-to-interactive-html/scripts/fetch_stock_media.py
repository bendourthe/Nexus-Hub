#!/usr/bin/env python3
"""
fetch_stock_media.py - Opt-in, consent-gated fetch of license-free stock media
for the document-to-interactive-html skill (Tier 2 imagery).

This script ships as a Tier-3 bundled resource: the authoring stage invokes it
via the shell ONLY when the user has chosen the `stock` imagery tier AND
consented to the build-time network use. It turns content-derived keywords into
license-verified, base64-embedded assets plus a credits manifest, so the final
HTML still opens offline with zero external requests (every asset is inlined as
a data: URI at build time; nothing external is referenced from the output).

CONSENT GATE (the load-bearing invariant): this script performs NO network call
unless `--consent` is passed. Without it, it prints a one-line notice, writes an
empty degraded manifest, and exits with the documented degrade code (3); the
authoring stage then stays on Tier 1 (procedural visuals). The network modules
(requests / urllib) are imported lazily inside the fetch path, which is only
reached after the consent check - so "no consent => no network" holds by
construction.

COMMERCIAL-USE SAFETY: every candidate is checked against a small allow-list of
free-for-commercial-use licenses (CC0, Public Domain Mark, CC-BY, CC-BY-SA, plus
the blanket no-attribution licenses of Pexels / Coverr / Mixkit). Anything
carrying a NonCommercial (nc) or NoDerivatives (nd) term is rejected. CC-BY /
CC-BY-SA assets get a built attribution string; CC0 / PD and the blanket-license
sources need no attribution but are still credited for auditability.

SOURCES: Openverse (default, keyless - a CC / public-domain aggregator) and
Wikimedia Commons (keyless) are fully implemented for images. Pexels is
supported when a key is present - PEXELS_API_KEY in the environment, or
~/.nexus-hub/config/media.env (written by `nexus-hub setup-media`); never
hardcoded, resolved by _resolve_pexels_key(); absent key => that source is
skipped. Coverr / Mixkit are accepted on the CLI
for interface parity but have no keyless search API, so they degrade with a
note (see references/interactive-features.md, "Tier 2 - license-free stock").

GRACEFUL DEGRADE: the script never raises on a missing library, missing key,
network error, or zero results. It prints a hint to stderr, writes an empty
manifest with a degrade note, and exits with code 3.

Usage:
    python fetch_stock_media.py --query "cooling towers dusk" --consent -o assets.json
    python fetch_stock_media.py --query "microscope lab" --count 4 --license cc0 --consent -o out.json
    python fetch_stock_media.py --query "city skyline" --source wikimedia --consent -o out.json

Exit codes:
    0  success: at least one license-verified asset was embedded.
    2  usage error (bad arguments).
    3  degrade: no --consent, missing dependency, network error, or zero
       results. The authoring stage falls back to Tier 1. The manifest (if a
       path was given) is written with {"degraded": true, "reason": ...}.

All diagnostics go to stderr; the manifest is written to --out (and echoed to
stdout when no --out is given). Ordering is deterministic given a fixed API
response (live results naturally vary run to run).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_DEGRADE = 3

DEFAULT_MAX_BYTES = 2_000_000
DEFAULT_COUNT = 3
HTTP_TIMEOUT = 20
USER_AGENT = "nexus-hub-presentify/1.0 (local build-time media fetch)"

OPENVERSE_IMAGES = "https://api.openverse.org/v1/images/"
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
PEXELS_IMAGES = "https://api.pexels.com/v1/search"
PEXELS_VIDEOS = "https://api.pexels.com/videos/search"

# Free-for-commercial-use Creative Commons / public-domain license codes
# (lowercase, Openverse-style). Allow-list, so an unknown code fails safe.
COMMERCIAL_CC = {"cc0", "pdm", "by", "by-sa"}
# CC codes that do NOT require attribution (still credited for auditability).
NO_ATTRIBUTION_CC = {"cc0", "pdm"}
# Blanket-license sources: commercial use allowed, no per-asset attribution
# required (but still credited). value = (human label, requires_attribution).
BLANKET_LICENSE = {
    "pexels": ("Pexels License", False),
    "coverr": ("Coverr License", False),
    "mixkit": ("Mixkit License", False),
}
MIME_BY_EXT = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml",
    ".mp4": "video/mp4", ".webm": "video/webm",
}


def log(msg: str) -> None:
    """Write a diagnostic line to stderr (stdout stays reserved for output)."""
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------
# License logic (the commercial-use gate)
# --------------------------------------------------------------------------

def normalize_license(code: str | None) -> str:
    """Lowercase and trim a license code; '' for a missing value."""
    return (code or "").strip().lower()


def is_commercial_cc(code: str) -> bool:
    """True when a CC/PD license code permits commercial use with no nc/nd term."""
    code = normalize_license(code)
    if not code:
        return False
    parts = code.split("-")
    if "nc" in parts or "nd" in parts:
        return False
    return code in COMMERCIAL_CC


def cc_requires_attribution(code: str) -> bool:
    """True when a commercial CC license still requires attribution (BY / BY-SA)."""
    return normalize_license(code) not in NO_ATTRIBUTION_CC


def cc_license_label(code: str, version: str | None = None) -> str:
    """Human-readable label for a CC/PD code, e.g. 'CC BY-SA 4.0', 'CC0'."""
    code = normalize_license(code)
    ver = (version or "").strip()
    if code == "cc0":
        return "CC0" + (f" {ver}" if ver else "")
    if code == "pdm":
        return "Public Domain Mark" + (f" {ver}" if ver else "")
    return "CC " + code.upper() + (f" {ver}" if ver else "")


def build_cc_license_url(code: str, version: str | None) -> str:
    """Best-effort canonical license URL (used in the manifest / adjacent comment)."""
    code = normalize_license(code)
    ver = (version or "4.0").strip()
    if code == "cc0":
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    if code == "pdm":
        return "https://creativecommons.org/publicdomain/mark/1.0/"
    return f"https://creativecommons.org/licenses/{code}/{ver}/"


def build_attribution(title: str, author: str, license_label: str, source: str) -> str:
    """Build a human-readable attribution string (no raw URL, so the visible
    credits stay clean under the offline URL self-check; URLs live in the
    adjacent HTML comment / manifest)."""
    title = title.strip() or "Untitled"
    author = author.strip() or "Unknown author"
    return f'"{title}" by {author}, {license_label}, via {source}'


# --------------------------------------------------------------------------
# Network layer (lazy imports; only reached after the consent check)
# --------------------------------------------------------------------------

def _http_get_json(url: str, params: dict[str, str], headers: dict[str, str]) -> Any:
    """GET JSON via requests when available, else stdlib urllib. Raises on error."""
    try:
        import requests  # noqa: PLC0415  (lazy: optional dependency)

        resp = requests.get(url, params=params, headers=headers, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except ImportError:
        import urllib.parse  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        full = url + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(full, headers=headers)  # noqa: S310 (https-only, validated)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))


def _http_get_bytes(url: str, max_bytes: int) -> tuple[bytes, str]:
    """GET raw bytes (capped at max_bytes) plus the content-type. Raises on error
    or when the payload exceeds max_bytes."""
    headers = {"User-Agent": USER_AGENT}
    try:
        import requests  # noqa: PLC0415

        with requests.get(url, headers=headers, timeout=HTTP_TIMEOUT, stream=True) as resp:
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
            buf = bytearray()
            for chunk in resp.iter_content(8192):
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    raise ValueError(f"asset exceeds --max-bytes ({max_bytes})")
            return bytes(buf), ctype
    except ImportError:
        import urllib.request  # noqa: PLC0415

        req = urllib.request.Request(url, headers=headers)  # noqa: S310 (https validated)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"asset exceeds --max-bytes ({max_bytes})")
            return data, ctype


def is_safe_https(url: str) -> bool:
    """Reject non-https / hostless URLs before fetching (SSRF guard)."""
    from urllib.parse import urlparse  # noqa: PLC0415

    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.netloc)


def guess_mime(url: str, content_type: str) -> str:
    """Prefer the server content-type; fall back to the URL extension."""
    if content_type.startswith(("image/", "video/")):
        return content_type
    ext = Path(urlpath(url)).suffix.lower()
    return MIME_BY_EXT.get(ext, "application/octet-stream")


def urlpath(url: str) -> str:
    from urllib.parse import urlparse  # noqa: PLC0415

    return urlparse(url).path


def to_data_uri(data: bytes, mime: str) -> str:
    """Base64-encode bytes into a self-contained data: URI."""
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


# --------------------------------------------------------------------------
# Source queries -> list of candidate dicts (not yet downloaded)
# --------------------------------------------------------------------------

def query_openverse(query: str, license_mode: str, count: int) -> list[dict[str, Any]]:
    """Query Openverse images. Keyless. Returns license-annotated candidates."""
    params = {"q": query, "page_size": str(max(count * 4, 8))}
    if license_mode == "cc0":
        params["license"] = "cc0,pdm"
    else:
        params["license_type"] = "commercial"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = _http_get_json(OPENVERSE_IMAGES, params, headers)
    out: list[dict[str, Any]] = []
    for item in data.get("results", []):
        out.append({
            "source": "Openverse",
            "url": item.get("url", ""),
            "title": item.get("title", "") or "",
            "author": item.get("creator", "") or "",
            "license": normalize_license(item.get("license")),
            "license_version": str(item.get("license_version") or ""),
            "license_url": item.get("license_url", "") or "",
            "landing": item.get("foreign_landing_url", "") or "",
            "width": item.get("width"),
            "height": item.get("height"),
            "cc": True,
        })
    return out


def query_wikimedia(query: str, count: int) -> list[dict[str, Any]]:
    """Query Wikimedia Commons files. Keyless. Reads per-file license metadata."""
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": str(max(count * 4, 8)),
        "prop": "imageinfo", "iiprop": "url|size|extmetadata",
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    data = _http_get_json(WIKIMEDIA_API, params, headers)
    pages = (data.get("query") or {}).get("pages") or {}
    out: list[dict[str, Any]] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        code = normalize_license(_meta(meta, "License"))
        out.append({
            "source": "Wikimedia Commons",
            "url": info.get("url", "") or "",
            "title": page.get("title", "") or "",
            "author": _strip_html(_meta(meta, "Artist")),
            "license": code,
            "license_version": "",
            "license_url": _meta(meta, "LicenseUrl"),
            "landing": info.get("descriptionurl", "") or "",
            "width": info.get("width"),
            "height": info.get("height"),
            "cc": True,
        })
    return out


def query_pexels(query: str, kind: str, count: int, api_key: str) -> list[dict[str, Any]]:
    """Query Pexels images or videos. Requires PEXELS_API_KEY. Blanket license."""
    headers = {"User-Agent": USER_AGENT, "Authorization": api_key}
    params = {"query": query, "per_page": str(max(count * 2, 5))}
    out: list[dict[str, Any]] = []
    if kind == "video":
        data = _http_get_json(PEXELS_VIDEOS, params, headers)
        for item in data.get("videos", []):
            files = sorted(item.get("video_files", []), key=lambda f: f.get("width") or 0)
            if not files:
                continue
            best = files[len(files) // 2]  # a mid-size rendition, deterministic
            out.append(_pexels_candidate(best.get("link", ""), item, kind))
    else:
        data = _http_get_json(PEXELS_IMAGES, params, headers)
        for item in data.get("photos", []):
            src = item.get("src") or {}
            out.append(_pexels_candidate(src.get("large") or src.get("original") or "", item, kind))
    return [c for c in out if c["url"]]


def _pexels_candidate(url: str, item: dict[str, Any], kind: str) -> dict[str, Any]:
    author = item.get("photographer") or item.get("user", {}).get("name") or ""
    return {
        "source": "Pexels",
        "url": url,
        "title": item.get("alt") or ("Pexels " + kind),
        "author": author,
        "license": "pexels",
        "license_version": "",
        "license_url": "https://www.pexels.com/license/",
        "landing": item.get("url", "") or "",
        "width": item.get("width"),
        "height": item.get("height"),
        "cc": False,
    }


def _meta(extmetadata: dict[str, Any], key: str) -> str:
    node = extmetadata.get(key)
    if isinstance(node, dict):
        return str(node.get("value", "") or "")
    return ""


def _strip_html(text: str) -> str:
    """Crude tag strip for Wikimedia's HTML-bearing Artist field."""
    import re  # noqa: PLC0415

    return re.sub(r"<[^>]+>", "", text or "").strip()


# --------------------------------------------------------------------------
# Filter, download, embed
# --------------------------------------------------------------------------

def accept_candidate(cand: dict[str, Any]) -> tuple[bool, str]:
    """Return (accepted, reason). Enforces the free-for-commercial-use gate."""
    if not cand.get("url"):
        return False, "no asset URL"
    if not is_safe_https(cand["url"]):
        return False, "asset URL is not https"
    if cand.get("cc"):
        if not is_commercial_cc(cand["license"]):
            return False, f"license '{cand['license'] or 'unknown'}' is not free-for-commercial-use"
        return True, ""
    # blanket-license source (Pexels / Coverr / Mixkit)
    if cand["license"] in BLANKET_LICENSE:
        return True, ""
    return False, f"unrecognized license for source {cand.get('source')}"


def build_provenance(cand: dict[str, Any]) -> dict[str, Any]:
    """Assemble the credit-entry provenance per the Phase 1 credits convention."""
    if cand.get("cc"):
        label = cc_license_label(cand["license"], cand.get("license_version"))
        needs_attr = cc_requires_attribution(cand["license"])
        license_url = cand.get("license_url") or build_cc_license_url(
            cand["license"], cand.get("license_version"))
    else:
        label, needs_attr = BLANKET_LICENSE[cand["license"]]
        license_url = cand.get("license_url", "")
    prov: dict[str, Any] = {
        "tier": "stock",
        "source": cand["source"],
        "url": cand.get("landing") or cand["url"],
        "asset_url": cand["url"],
        "license": label,
        "license_url": license_url,
        "author": cand.get("author", ""),
        "title": cand.get("title", ""),
    }
    if needs_attr:
        prov["attribution"] = build_attribution(
            cand.get("title", ""), cand.get("author", ""), label, cand["source"])
    else:
        # still credited for auditability, no attribution legally required
        prov["attribution"] = f"{label}, via {cand['source']}"
    return prov


def embed_candidates(
    candidates: list[dict[str, Any]], count: int, max_bytes: int, notes: list[str],
) -> list[dict[str, Any]]:
    """Filter to free-for-commercial licenses, download within the size cap, and
    base64-embed. Deterministic given a fixed candidate order."""
    assets: list[dict[str, Any]] = []
    for cand in candidates:
        if len(assets) >= count:
            break
        ok, reason = accept_candidate(cand)
        if not ok:
            notes.append(f"skipped ({cand.get('source', '?')}): {reason}")
            continue
        try:
            data, ctype = _http_get_bytes(cand["url"], max_bytes)
        except Exception as exc:  # noqa: BLE001 (any fetch failure -> skip, never fatal)
            notes.append(f"skipped ({cand['source']}): download failed - {exc}")
            continue
        mime = guess_mime(cand["url"], ctype)
        assets.append({
            "data_uri": to_data_uri(data, mime),
            "alt": cand.get("title", "") or "stock media",
            "width": cand.get("width"),
            "height": cand.get("height"),
            "provenance": build_provenance(cand),
        })
    return assets


# --------------------------------------------------------------------------
# Manifest / degrade / CLI
# --------------------------------------------------------------------------

def write_manifest(out_path: str | None, manifest: dict[str, Any]) -> None:
    text = json.dumps(manifest, indent=2, ensure_ascii=True)
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8")
    else:
        print(text)


def degrade(out_path: str | None, reason: str, **extra: Any) -> int:
    """Write an empty degraded manifest, log the reason, and return the degrade code."""
    log(f"[fetch_stock_media] degrade: {reason}")
    manifest = {"assets": [], "degraded": True, "reason": reason}
    manifest.update(extra)
    write_manifest(out_path, manifest)
    return EXIT_DEGRADE


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consent-gated fetch of license-free, commercial-use stock media (Tier 2).")
    parser.add_argument("--query", required=True, help="content-derived search keywords")
    parser.add_argument("--kind", choices=["image", "video"], default="image")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--license", choices=["cc0", "commercial"], default="commercial",
                        help="cc0 restricts to CC0 / public-domain; commercial allows CC-BY / BY-SA too")
    parser.add_argument("--source", choices=["openverse", "wikimedia", "pexels", "coverr", "mixkit"],
                        default="openverse")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--consent", action="store_true",
                        help="REQUIRED to perform any network call; without it the script degrades")
    parser.add_argument("-o", "--out", default=None, help="manifest output path (stdout if omitted)")
    return parser.parse_args(argv)


def _resolve_pexels_key() -> str | None:
    """Resolve the Pexels API key: the environment first, then the persisted
    config file (`~/.nexus-hub/config/media.env`), else None.

    The env var wins so a shell / CI override always takes precedence. The config
    file is the bring-your-own-key fallback written by `nexus-hub setup-media`
    (simple `KEY=VALUE` lines; blanks and `#` comments ignored). This function
    NEVER logs or prints the value - any diagnostic that references the key must
    mask it (length or last-4 only). A missing / unreadable file or an absent key
    all yield None, so the video / Pexels path degrades to Tier 1 exactly as
    before, with no network call.
    """
    env = os.environ.get("PEXELS_API_KEY", "").strip()
    if env:
        return env
    config = Path.home() / ".nexus-hub" / "config" / "media.env"
    try:
        for raw in config.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            if name.strip() == "PEXELS_API_KEY":
                value = value.strip().strip('"').strip("'")
                if value:
                    return value
    except OSError:
        pass
    return None


def run_source(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Dispatch to the chosen source. Returns candidates (may be empty)."""
    if args.source == "openverse":
        if args.kind == "video":
            raise LookupError("Openverse has no video endpoint; use --source pexels for video")
        return query_openverse(args.query, args.license, args.count)
    if args.source == "wikimedia":
        if args.kind == "video":
            raise LookupError("Wikimedia video is out of scope; use --source pexels for video")
        return query_wikimedia(args.query, args.count)
    if args.source == "pexels":
        api_key = _resolve_pexels_key()
        if not api_key:
            raise LookupError(
                "PEXELS_API_KEY not found (environment or ~/.nexus-hub/config/media.env); "
                "source skipped. Run `nexus-hub setup-media` to store a free key.")
        return query_pexels(args.query, args.kind, args.count, api_key)
    # coverr / mixkit: no keyless search API in this helper
    raise LookupError(
        f"source '{args.source}' has no keyless search API in this helper; "
        "prefer openverse / wikimedia, or configure pexels")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.count < 1:
        log("[fetch_stock_media] --count must be >= 1")
        return EXIT_USAGE

    # CONSENT GATE: return before importing or calling any network code.
    if not args.consent:
        return degrade(
            args.out,
            "no --consent flag; no network performed, staying on Tier 1 (procedural)",
            query=args.query, source=args.source)

    notes: list[str] = []
    try:
        candidates = run_source(args)
    except Exception as exc:  # noqa: BLE001 (any query failure -> degrade, never fatal)
        return degrade(args.out, f"source query failed - {exc}",
                       query=args.query, source=args.source)

    if not candidates:
        return degrade(args.out, "zero results for the query",
                       query=args.query, source=args.source)

    assets = embed_candidates(candidates, args.count, args.max_bytes, notes)
    if not assets:
        return degrade(args.out, "no candidate passed the free-for-commercial-use filter",
                       query=args.query, source=args.source, notes=notes)

    manifest = {
        "assets": assets,
        "degraded": False,
        "query": args.query,
        "source": args.source,
        "requested": args.count,
        "returned": len(assets),
        "notes": notes,
    }
    write_manifest(args.out, manifest)
    log(f"[fetch_stock_media] embedded {len(assets)} asset(s) from {args.source}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
