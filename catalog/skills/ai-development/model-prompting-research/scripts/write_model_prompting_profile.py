#!/usr/bin/env python3
"""Deterministic planner and writer for the per-model prompting profile layer.

The research half of `model-prompting-research` is agent work: search the web,
read primary sources, judge and refute claims. But the two ends of that pipeline
must NOT be agent work, because both are exactly the kind of mechanical step an
LLM does inconsistently:

  * `plan`  - decide WHICH models still need research (the fan-out work-list).
  * `write` - merge verified claims into the profile layer, schema-valid by
              construction, and regenerate the Markdown mirrors.

Keeping these deterministic buys three things. The work-list is reproducible, so
the same roster always fans out the same way. The written layer always satisfies
`scripts/verify_model_prompting_profiles.py`, so the research run cannot leave a
malformed index behind. And a run that stops early (a budget cap, a kill switch,
an offline stage) still writes a VALID partial layer, because each write is a
complete merge rather than a half-finished edit.

The workflow template (`assets/research-workflow.js`) has no filesystem access,
so the CALLER runs `plan` first and passes the work-list in as workflow args,
then runs `write` per model as claims survive verification. That is the
"scope-first" shape the agent-orchestration-primitives reference template
recommends.

This script makes NO network call. It never invents, edits, or re-scopes a
claim: it validates what it is given and refuses the whole write on anything
malformed, so a bad research result fails loudly instead of silently degrading
the layer.

Usage:
    python write_model_prompting_profile.py plan --roster claude-opus-5 claude-sonnet-5
    python write_model_prompting_profile.py plan --only claude-opus-5
    python write_model_prompting_profile.py write --input verified.json
    python write_model_prompting_profile.py write --input verified.json --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

SKILL_NAME = "model-prompting-research"
INDEX_REL = Path("assets") / "profiles-index.json"
PROFILES_REL = Path("references") / "models"
#: Generated index linking every mirror, so none is an orphan bundled file.
#: Lives at the references/ ROOT rather than inside models/, because the
#: orphan audit accepts a reference from SKILL.md or any references/*.md and
#: does not descend into subdirectories.
MIRROR_INDEX_REL = Path("references") / "model-profiles.md"

SCHEMA_VERSION = "1.2.0"
ALLOWED_ROSTER_SOURCES = ("api", "picker", "config", "manual")
ALLOWED_CONFIDENCE = ("high", "medium", "low", "unverified")
ALLOWED_SCOPE = ("model-specific", "model-agnostic-candidate")
CLAIM_REQUIRED_KEYS = ("claim", "source_url", "confidence", "scope")
CLAIM_OPTIONAL_KEYS = ("note", "evidence_scope")
ALLOWED_EVIDENCE_SCOPE = ("model", "model-family", "provider-plan", "cited-page")

# A claim that has not survived the adversarial-verify pass must never be
# presented as actionable guidance. The writer accepts it (so a partial or
# low-confidence research result is still recorded honestly) but the planner
# treats a model whose claims are ALL unverified as still needing research.
UNVERIFIED = "unverified"

# WN-29 input rules. A claim is text built from fetched page content, so every field the
# layer renders into Markdown or a file name is untrusted. These constants and helpers
# are duplicated, on purpose, from the repo-level `scripts/verify_model_prompting_profiles.py`:
# this script ships inside the skill bundle and cannot import it, so the writer refuses
# a payload by the same rules the structural gate would apply afterward. Keep the two in
# step; `references/schema.md` ("Input rules") is the contract.
#: Exact hostnames a `source_url` may use (https only, matched after URL parsing, so
#: `ai.google.dev.evil.com` and `ai.google.dev@evil.com` both fail). The first five
#: are the v4.14.3 DoD 1 list; the rest are the vendor hosts the shipped layer already
#: cites. A new vendor host is a deliberate edit here and in the validator.
ALLOWED_SOURCE_HOSTS = frozenset(
    {
        "ai.google.dev",
        "aistudio.google.com",
        "blog.google",
        "cloud.google.com",
        "docs.cloud.google.com",
        "cursor.com",
        "deploymentsafety.openai.com",
        "developers.openai.com",
        "platform.claude.com",
        "www.anthropic.com",
    }
)
#: Platform ids the layer profiles. A model profiled for any other platform is refused.
KNOWN_PLATFORMS = frozenset({"antigravity", "claude-code", "codex", "cursor", "gemini", "openai"})
#: A model id becomes a file name (`references/models/<id>.md`), so it is a closed set of
#: characters: no separator, no space, no upper case (case-folding file systems).
MODEL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}")
_WINDOWS_RESERVED_RE = re.compile(r"(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)")
MAX_TEXT_CHARS = 1000
MAX_URL_CHARS = 2048
MAX_ROSTER_ENTRY_CHARS = 128
# Control, format (zero-width and bidi overrides), and line or paragraph separators.
_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})
# A quoted span ('CRITICAL: You MUST ...') cites example wording the guidance tells a
# reader to REMOVE, so a second-person directive inside one is not an instruction. The
# delimiters must sit on word boundaries so a contraction cannot hide text between two
# apostrophes.
_QUOTED_SPAN_RE = re.compile(r"""(?<!\w)(['"])[^'"\n]{1,160}\1(?!\w)""")
# Injection signatures are tested on the FULL text, quotes included, so quoting cannot hide them.
_INJECTION_RES = (
    re.compile(
        r"\b(?:ignore|disregard|forget|override)\b[^.\n]{0,40}\b"
        r"(?:instructions?|prompts?|rules?|directions?|guidelines?|context)\b",
        re.IGNORECASE,
    ),
    re.compile(r"(?<![\w-])(?:system|assistant|developer)\s*:", re.IGNORECASE),
    re.compile(r"\b(?:new|updated|real)\s+instructions?\b", re.IGNORECASE),
)
_SECOND_PERSON_RE = re.compile(
    r"\byou\s+(?:must|should|shall|will|need\s+to|are\s+now|are\s+to)\b", re.IGNORECASE
)
_LINK_RE = re.compile(r"\]\s*[(\[]")
# GitHub-flavored Markdown autolinks a bare URL, a `www.` address, and an email shape, so
# none of them may ride in claim or note text unless it is a plain allowlisted https URL.
_URL_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://\S*")
_WWW_RE = re.compile(r"(?<![\w.-])www\.", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_UNSAFE_URL_CHARS_RE = re.compile(r"""[\s\x00-\x1f\x7f<>()"'\\`|]""")


def has_unsafe_characters(value: str) -> bool:
    """True when `value` carries a control, format, or line-separator character."""
    return any(unicodedata.category(char) in _UNSAFE_CATEGORIES for char in value)


def model_id_problem(model_id: object) -> str | None:
    """Why a model id cannot be a safe file stem, or None when it can."""
    if not isinstance(model_id, str) or not MODEL_ID_RE.fullmatch(model_id):
        return "must match [a-z0-9][a-z0-9._-]{0,79} (no path separator, space, or upper case)"
    if _WINDOWS_RESERVED_RE.match(model_id):
        return "is a reserved Windows device name"
    return None


def embedded_link_problem(text: str) -> str | None:
    """Why a bare URL, `www.` address, or email shape in text is refused, or None.

    A URL-scheme token is allowed only as `https` with no credentials or port and an exact
    hostname on ALLOWED_SOURCE_HOSTS (trailing sentence punctuation is ignored).
    """
    for match in _URL_TOKEN_RE.finditer(text):
        token = match.group().rstrip(".,;:!?)]}'\"")
        try:
            parts = urlsplit(token)
            port = parts.port
        except ValueError:
            return "contains a URL that cannot be parsed"
        if (
            parts.scheme != "https"
            or parts.username is not None
            or parts.password is not None
            or port is not None
            or parts.hostname not in ALLOWED_SOURCE_HOSTS
        ):
            return (
                "contains a URL that is not a plain https link (no credentials or port) "
                "on an allowlisted host"
            )
    remainder = _URL_TOKEN_RE.sub(" ", text)
    if _WWW_RE.search(remainder):
        return "contains a www. address, which Markdown autolinks"
    if _EMAIL_RE.search(remainder):
        return "contains an email address, which Markdown autolinks"
    return None


def claim_text_problem(text: str) -> str | None:
    """Why free-form claim or note text cannot be rendered safely, or None when it can.

    The text lands in a Markdown table cell of the generated mirror and is read by
    agents, so it must be one plain paraphrase: bounded, one line, no table character,
    no HTML, no Markdown link, and no directive addressed to the reader.
    """
    if len(text) > MAX_TEXT_CHARS:
        return f"is longer than {MAX_TEXT_CHARS} characters"
    if has_unsafe_characters(text):
        return "contains a control, newline, zero-width, or line-separator character"
    if "|" in text:
        return "contains '|', which breaks the Markdown table"
    if "<" in text:
        return "contains '<', so HTML and autolinks are not allowed"
    if _LINK_RE.search(text):
        return "contains a Markdown link"
    if problem := embedded_link_problem(text):
        return problem
    if any(pattern.search(text) for pattern in _INJECTION_RES):
        return "contains an instruction-override or role-label directive"
    if _SECOND_PERSON_RE.search(_QUOTED_SPAN_RE.sub(" ", text)):
        return "contains a second-person directive (paraphrase it instead)"
    return None


def source_url_problem(url: str) -> str | None:
    """Why a source URL is not an allowlisted https primary source, or None when it is."""
    if len(url) > MAX_URL_CHARS:
        return f"is longer than {MAX_URL_CHARS} characters"
    if _UNSAFE_URL_CHARS_RE.search(url) or has_unsafe_characters(url):
        return "contains whitespace, a control character, or a character unsafe in a link"
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return "is not a parseable URL"
    if parts.scheme != "https":
        return "must use https"
    if parts.username is not None or parts.password is not None:
        return "must not carry credentials (user@host)"
    if port not in (None, 443):
        return "must not name a non-default port"
    if parts.hostname not in ALLOWED_SOURCE_HOSTS:
        return f"host {parts.hostname!r} is not an allowlisted primary-source host"
    return None


def roster_entry_problem(entry: str) -> str | None:
    """A roster entry is not a file name, so the rule is only bounded with no control char."""
    if len(entry) > MAX_ROSTER_ENTRY_CHARS or has_unsafe_characters(entry):
        return f"must be at most {MAX_ROSTER_ENTRY_CHARS} characters with no control character"
    return None


def platform_problem(value: object) -> str | None:
    """Why a platform name is refused, or None when it is a known platform."""
    if not isinstance(value, str) or value not in KNOWN_PLATFORMS:
        return f"must be a known platform {sorted(KNOWN_PLATFORMS)}, got {str(value)[:40]!r}"
    return None


class WriteError(Exception):
    """A malformed input that must abort the whole write."""


def roster_hash(roster: list[str]) -> str:
    """The canonical roster hash, identical to the repo-level validator's."""
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def default_bundle() -> Path:
    """This script lives in the bundle's scripts/ dir, so the bundle is its parent."""
    return Path(__file__).resolve().parents[1]


def load_index(bundle: Path) -> dict:
    """Load the existing index, or return an empty skeleton when absent."""
    path = bundle / INDEX_REL
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "meta": {}, "models": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise WriteError(f"existing index is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteError("existing index does not contain a JSON object")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("meta", {})
    data.setdefault("models", {})
    return data


# ---------------------------------------------------------------------------
# plan: which models still need research
# ---------------------------------------------------------------------------


def plan_targets(
    roster: list[str],
    models: dict,
    only: str | None = None,
    refresh_all: bool = False,
) -> dict:
    """Compute the research work-list. Pure; no I/O.

    A model needs research when it has no profile, when its profile carries no
    claims, or when every claim it carries is still `unverified` (a seed that no
    verify pass has confirmed). `--only` narrows to one model for the scope-first
    calibration run; `--refresh-all` re-researches the whole roster.
    """
    roster = sorted({m.strip() for m in roster if m and m.strip()})
    if only:
        only = only.strip()
        targets = [only] if only else []
        return {
            "targets": targets,
            "reason": "explicit --only (scope-first calibration)",
            "roster": roster,
            "in_roster": only in roster,
        }

    targets: list[str] = []
    for model_id in roster:
        entry = models.get(model_id)
        if not isinstance(entry, dict):
            targets.append(model_id)
            continue
        claims = entry.get("claims")
        if not isinstance(claims, list) or not claims:
            targets.append(model_id)
            continue
        if refresh_all or all(
            isinstance(c, dict) and c.get("confidence") == UNVERIFIED for c in claims
        ):
            targets.append(model_id)

    return {
        "targets": targets,
        "reason": "refresh-all" if refresh_all else "unprofiled or wholly-unverified",
        "roster": roster,
        "in_roster": True,
    }


# ---------------------------------------------------------------------------
# write: merge verified claims into the layer
# ---------------------------------------------------------------------------


def _validate_claim(model_id: str, position: int, claim: object) -> dict:
    """Validate and normalize one incoming claim. Raises WriteError."""
    where = f"models['{model_id}'].claims[{position}]"
    if not isinstance(claim, dict):
        raise WriteError(f"{where} must be an object")

    unknown = set(claim) - set(CLAIM_REQUIRED_KEYS) - set(CLAIM_OPTIONAL_KEYS)
    if unknown:
        raise WriteError(f"{where} has unknown key(s): {', '.join(sorted(unknown))}")
    for key in CLAIM_REQUIRED_KEYS:
        if key not in claim:
            raise WriteError(f"{where} is missing required key '{key}'")

    text = claim["claim"]
    if not isinstance(text, str) or not text.strip():
        raise WriteError(f"{where}.claim must be a non-empty string")
    if problem := claim_text_problem(text.strip()):
        raise WriteError(f"{where}.claim {problem}")
    url = claim["source_url"]
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise WriteError(
            f"{where}.source_url must be an http(s) URL to a primary source, got {str(url)[:80]!r}"
        )
    if problem := source_url_problem(url.strip()):
        raise WriteError(f"{where}.source_url {problem}, got {url[:80]!r}")
    if claim["confidence"] not in ALLOWED_CONFIDENCE:
        raise WriteError(
            f"{where}.confidence must be one of {list(ALLOWED_CONFIDENCE)}, "
            f"got {claim['confidence']!r}"
        )
    if claim["scope"] not in ALLOWED_SCOPE:
        raise WriteError(
            f"{where}.scope must be one of {list(ALLOWED_SCOPE)}, got {claim['scope']!r}"
        )

    normalized = {
        "claim": text.strip(),
        "source_url": url.strip(),
        "confidence": claim["confidence"],
        "scope": claim["scope"],
    }
    note = claim.get("note")
    if note is not None:
        if not isinstance(note, str):
            raise WriteError(f"{where}.note must be a string when present")
        if problem := claim_text_problem(note.strip()):
            raise WriteError(f"{where}.note {problem}")
        normalized["note"] = note.strip()
    evidence_scope = claim.get("evidence_scope")
    if evidence_scope is not None:
        if evidence_scope not in ALLOWED_EVIDENCE_SCOPE:
            raise WriteError(
                f"{where}.evidence_scope must be one of {list(ALLOWED_EVIDENCE_SCOPE)}, "
                f"got {evidence_scope!r}"
            )
        normalized["evidence_scope"] = evidence_scope
    return normalized


def _render_mirror(model_id: str, entry: dict, roster_source: str) -> str:
    """Render the human-readable Markdown mirror for one model entry."""
    rows = []
    for claim in entry["claims"]:
        # Pipes would break the table; the source is a URL so it cannot contain one
        # unescaped, but claim text is free-form and must be escaped.
        text = claim["claim"].replace("|", "\\|")
        note = claim.get("note", "")
        suffix = f" {note.replace('|', chr(92) + '|')}" if note else ""
        evidence = f"`{claim['evidence_scope']}`" if "evidence_scope" in claim else "not recorded"
        rows.append(
            f"| {text}{suffix} | `{claim['confidence']}` | `{claim['scope']}` | "
            f"{evidence} | "
            f"[source]({claim['source_url']}) |"
        )
    table = "\n".join(rows)

    return f"""# Prompting Profile: {model_id}

**Platform**: {entry["platform"]}
**Last verified**: {entry["last_verified"]}
**Roster provenance**: `{roster_source}`

This file mirrors the `models["{model_id}"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Evidence scope | Primary source |
|---|---|---|---|---|
{table}

## Does not apply to shared bodies

This file is retrieved by the model named in the H1. A claim's evidence can cover a model family, a provider plan, or only a cited-page negative result rather than this variant alone. Claims must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
"""


def merge(index: dict, payload: dict) -> tuple[dict, list[str]]:
    """Merge a verified-research payload into the index. Pure; raises WriteError.

    Returns the updated index and the list of model ids that were written.
    """
    if not isinstance(payload, dict):
        raise WriteError("payload must be a JSON object")
    for key in ("platform", "verified_at", "models"):
        if key not in payload:
            raise WriteError(f"payload is missing required key '{key}'")

    platform = payload["platform"]
    if not isinstance(platform, str) or not platform.strip():
        raise WriteError("payload.platform must be a non-empty string")
    if problem := platform_problem(platform):
        raise WriteError(f"payload.platform {problem}")
    verified_at = payload["verified_at"]
    if not isinstance(verified_at, str) or len(verified_at) != 10:
        raise WriteError("payload.verified_at must be a YYYY-MM-DD string")

    incoming = payload["models"]
    if not isinstance(incoming, dict) or not incoming:
        raise WriteError("payload.models must be a non-empty object")
    # A model id becomes a file name, so it is checked before anything else is trusted.
    for model_id in incoming:
        if problem := model_id_problem(model_id):
            raise WriteError(f"models key {str(model_id)[:80]!r} {problem}")

    claim_only = "roster" not in payload
    if claim_only:
        if "roster_source" in payload:
            raise WriteError("payload.roster_source requires a roster")
        if index["meta"].get("platform") == platform:
            recorded = index["meta"].get("roster")
        else:
            entry = next(
                (e for e in index["meta"].get("platforms", []) if e.get("platform") == platform),
                None,
            )
            recorded = entry.get("roster") if entry else None
        if not isinstance(recorded, list) or not recorded:
            raise WriteError(f"no recorded roster for {platform}; supply a live roster")
        unknown = sorted(set(incoming) - set(recorded))
        if unknown:
            raise WriteError(f"model(s) not in the recorded roster for {platform}: {', '.join(unknown)}")
    else:
        roster_source = payload.get("roster_source", "manual")
        if roster_source not in ALLOWED_ROSTER_SOURCES:
            raise WriteError(
                f"payload.roster_source must be one of {list(ALLOWED_ROSTER_SOURCES)}, "
                f"got {roster_source!r}"
            )
        roster = payload["roster"]
        if not isinstance(roster, list) or not roster or any(
            not isinstance(model_id, str) or not model_id.strip() for model_id in roster
        ):
            raise WriteError("payload.roster must be a non-empty array of model ids")
        roster = sorted({model_id.strip() for model_id in roster})
        if problem := next(filter(None, map(roster_entry_problem, roster)), None):
            raise WriteError(f"payload.roster entries {problem}")
        unknown = sorted(set(incoming) - set(roster))
        if unknown:
            raise WriteError(
                f"model(s) not in the supplied live roster for {platform}: {', '.join(unknown)}"
            )

    # Validate EVERY model before the index is touched, so one bad claim cannot leave a
    # half-merged index in memory for a caller to write.
    validated: dict[str, list[dict]] = {}
    for model_id in sorted(incoming):
        claims = incoming[model_id]
        if not isinstance(claims, list) or not claims:
            raise WriteError(f"models['{model_id}'] must be a non-empty array of claims")
        validated[model_id] = [_validate_claim(model_id, i, c) for i, c in enumerate(claims)]

    written: list[str] = []
    for model_id, normalized in validated.items():
        index["models"][model_id] = {
            "platform": platform,
            "last_verified": verified_at,
            "claims": normalized,
        }
        written.append(model_id)

    if claim_only:
        # Per-model research does not verify the whole roster. Keep its original
        # date, source, and hash until a complete live enumeration is supplied.
        index["schema_version"] = SCHEMA_VERSION
        return index, written

    # A roster-bearing payload explicitly refreshes the platform roster.
    index["schema_version"] = SCHEMA_VERSION
    legacy_platform = index["meta"].get("platform")
    if legacy_platform in (None, platform):
        # Historical profiles remain available, but only the supplied live roster
        # establishes current membership and freshness.
        # Single-platform layer, or a write for the layer's primary platform: the
        # legacy keys stay the source of truth (schema 1.0.0 behavior).
        index["meta"] = {
            **index["meta"],
            "last_verified": verified_at,
            "platform": platform,
            "roster_source": roster_source,
            "roster": roster,
            "roster_hash": roster_hash(roster),
        }
        return index, written

    # v4.7.0 (schema 1.1.0): a write for ANOTHER platform lands in the optional
    # meta.platforms array, so the primary platform's roster is never rewritten by
    # research on a different vendor's models.
    entries = [e for e in index["meta"].get("platforms", []) if isinstance(e, dict)]
    entry = {
        "platform": platform,
        "roster_source": roster_source,
        "roster": roster,
        "roster_hash": roster_hash(roster),
        "last_verified": verified_at,
    }
    index["meta"]["platforms"] = [e for e in entries if e.get("platform") != platform] + [entry]
    return index, written


def platform_roster_source(index: dict, platform: str) -> str:
    """The roster provenance for a platform: its meta.platforms entry, else the legacy meta."""
    for entry in index.get("meta", {}).get("platforms", []) or []:
        if isinstance(entry, dict) and entry.get("platform") == platform:
            return str(entry.get("roster_source", "manual"))
    return str(index.get("meta", {}).get("roster_source", "manual"))


def build_outputs(bundle: Path, index: dict, written: list[str]) -> dict[Path, str]:
    """Render every file a write will produce, keyed by target path. Touches no file.

    Raises WriteError before anything exists on disk when a model id is not a safe file
    stem or a mirror path would resolve outside `references/models/`, so a refused
    payload cannot leave a partial layer behind.
    """
    mirrors = bundle / PROFILES_REL
    mirrors_root = mirrors.resolve()
    for model_id in index.get("models", {}):
        if problem := model_id_problem(model_id):
            raise WriteError(f"models key {str(model_id)[:80]!r} {problem}")

    outputs: dict[Path, str] = {
        bundle / INDEX_REL: json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    }
    for model_id in written:
        mirror = mirrors / f"{model_id}.md"
        # resolve() follows a symlinked target too, so a link planted in models/ cannot
        # redirect a mirror write out of the directory either.
        if mirror.resolve().parent != mirrors_root:
            raise WriteError(f"mirror path for {model_id!r} resolves outside {PROFILES_REL.as_posix()}/")
        entry = index["models"][model_id]
        roster_source = platform_roster_source(index, str(entry.get("platform", "")))
        outputs[mirror] = _render_mirror(model_id, entry, roster_source)
    outputs[bundle / MIRROR_INDEX_REL] = _mirror_index_text(index)
    return outputs


def commit_outputs(outputs: dict[Path, str]) -> list[Path]:
    """Write every output all-or-nothing: stage beside each target, then swap in.

    Each file is first written to a temporary sibling, so a disk or permission failure
    while staging changes no target. The swap uses `os.replace` (atomic per file); if a
    swap fails part way, every file already replaced is restored and every file created
    is removed before the error propagates, so the layer is never left half-written.
    """
    created_dirs: list[Path] = []
    staged: list[tuple[Path, Path]] = []
    originals: dict[Path, bytes | None] = {}
    swapped: list[Path] = []
    try:
        for target in outputs:
            missing = [p for p in (target.parent, *target.parent.parents) if not p.exists()]
            target.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(missing)
        for target, text in outputs.items():
            temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            staged.append((temp, target))
            temp.write_text(text, encoding="utf-8", newline="\n")
        for temp, target in staged:
            originals[target] = target.read_bytes() if target.is_file() else None
            os.replace(temp, target)
            swapped.append(target)
    except BaseException:
        for target in reversed(swapped):
            original = originals[target]
            if original is None:
                target.unlink(missing_ok=True)
            else:
                target.write_bytes(original)
        for temp, _ in staged:
            temp.unlink(missing_ok=True)
        for directory in sorted(set(created_dirs), key=lambda p: len(p.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return list(outputs)


def write_layer(bundle: Path, index: dict, written: list[str]) -> list[Path]:
    """Persist the index and regenerate a Markdown mirror per written model, all-or-nothing."""
    return commit_outputs(build_outputs(bundle, index, written))


def _mirror_index_text(index: dict) -> str:
    """Render the index that links every per-model mirror.

    Without this, each mirror this writer emits is an ORPHAN bundled file: the
    `AGENTS.md` rule is that every file beside a SKILL.md must be referenced
    from it, and `scripts/validate_skills.py --bundles-only` warns per
    unreferenced file. Before this index existed the warning count grew by one
    per profiled model (1 after the first OpenAI profile, 11 after the v4.8.0
    roster sweep), and an orphan bundled file is not cosmetic: the agent never
    loads a Tier-3 reference nothing points at, so the mirrors were being
    generated and then never read.

    Generated rather than hand-maintained on purpose. A list in SKILL.md would
    need editing on every write, which is exactly the drift that produced the
    orphans; regenerating it here keeps it correct by construction.
    """
    models = index.get("models", {})
    lines = [
        "# Per-Model Profile Mirrors",
        "",
        "GENERATED by `scripts/write_model_prompting_profile.py`. Do not hand-edit:",
        "the next write regenerates it.",
        "",
        "`assets/profiles-index.json` is authoritative. Each file below is a",
        "human-readable mirror of one model's entry, read on demand as a Tier-3",
        "reference. This index exists so no mirror is an orphan bundled file.",
        "",
        "Each file is retrieved by model ID; its Evidence scope column describes",
        "what the cited source covers. No claim may be copied into a shared catalog body.",
        "",
    ]
    if models:
        lines.append(f"{len(models)} profiled model(s):")
        lines.append("")
        for model_id in sorted(models):
            entry = models[model_id]
            claims = entry.get("claims", [])
            verified = entry.get("last_verified", "unknown")
            lines.append(
                f"- [{model_id}](models/{model_id}.md) - {len(claims)} claim(s), "
                f"verified {verified}"
            )
    else:
        lines.append("No model is profiled yet.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="write-model-prompting-profile",
        description="Plan the research work-list, or merge verified claims into the layer.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Path to the skill bundle (defaults to this script's parent directory).",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_plan = sub.add_parser("plan", help="Print the models that still need research.")
    p_plan.add_argument("--roster", nargs="*", default=None, help="The LIVE model roster.")
    p_plan.add_argument(
        "--platform",
        help="Plan against the recorded roster of this platform (a meta.platforms entry); default is the legacy meta roster.",
    )
    p_plan.add_argument("--only", help="Narrow to one model (scope-first calibration).")
    p_plan.add_argument(
        "--refresh-all", action="store_true", help="Re-research every rostered model."
    )

    p_write = sub.add_parser("write", help="Merge a verified-research payload.")
    p_write.add_argument("--input", type=Path, required=True, help="Payload JSON file, or - for stdin.")
    p_write.add_argument("--dry-run", action="store_true", help="Validate without writing.")
    p_write.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)
    bundle = args.bundle or default_bundle()

    try:
        index = load_index(bundle)
    except WriteError as exc:
        print(f"[profile-write] ERROR: {exc}", file=sys.stderr)
        return 1

    if args.mode == "plan":
        roster = args.roster if args.roster else index["meta"].get("roster", [])
        if not args.roster and args.platform:
            roster = next(
                (
                    e.get("roster", [])
                    for e in index["meta"].get("platforms", []) or []
                    if isinstance(e, dict) and e.get("platform") == args.platform
                ),
                [],
            )
        if not isinstance(roster, list):
            roster = []
        result = plan_targets(
            [str(m) for m in roster], index["models"], args.only, args.refresh_all
        )
        print(json.dumps(result, indent=2))
        return 0

    # PowerShell 5.1 prefixes piped UTF-8 with a BOM while Python's redirected
    # stdin may still decode through a Windows code page. Decode the bytes here.
    raw = (
        sys.stdin.buffer.read().decode("utf-8-sig")
        if str(args.input) == "-"
        else args.input.read_text(encoding="utf-8-sig")
    )
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        print(f"[profile-write] ERROR: payload is not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        index, written = merge(index, payload)
        outputs = build_outputs(bundle, index, written)
    except WriteError as exc:
        print(f"[profile-write] ERROR: {exc}", file=sys.stderr)
        print("  Nothing was written; fix the payload and re-run.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[profile-write] DRY RUN: would write {len(written)} model(s): {', '.join(written)}")
        return 0

    try:
        paths = commit_outputs(outputs)
    except OSError as exc:
        print(f"[profile-write] ERROR: could not write the layer: {exc}", file=sys.stderr)
        print("  Every file was restored; nothing was changed.", file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"[profile-write] wrote {len(written)} model(s): {', '.join(written)}")
        for path in paths:
            print(f"  {path}")
        unprofiled = [m for m in index["meta"]["roster"] if m not in index["models"]]
        if unprofiled:
            print(f"  UNVERIFIED (rostered, no profile): {', '.join(unprofiled)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
