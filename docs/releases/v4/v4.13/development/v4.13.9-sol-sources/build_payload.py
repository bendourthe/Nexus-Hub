"""Build and check the v4.13.9 T405 verified payload for gpt-6.1-sol (evidence only).

Every quote must appear in the saved page text (whitespace-collapsed), be 300
characters or fewer, and pass a mechanical rejection of agent-directed
imperatives, tool-call syntax, and URLs off the allowlist. A failing quote stops
the build; nothing is paraphrased from memory.

Usage: python build_payload.py   (writes payload.json and astra-delta.md here)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUIDE = "https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra"
MODELS = "https://developers.openai.com/api/docs/models"
TEXT = {GUIDE: (HERE / "latest-model.txt"), MODELS: (HERE / "models.txt")}
VERIFIED = "2026-10-01"
MAX_QUOTE = 300
_REJECT = re.compile(
    r"\byou should\b|\byour job\b|\bignore (all|previous|prior)\b|<\s*(function|tool)|\"tool_use\"|"
    r"https?://(?!developers\.openai\.com)",
    re.I,
)


def _collapse(s: str) -> str:
    return " ".join(s.split())


def check_quote(quote: str, url: str) -> None:
    if len(quote) > MAX_QUOTE:
        raise SystemExit(f"quote over {MAX_QUOTE} chars: {quote[:60]}...")
    if _REJECT.search(quote):
        raise SystemExit(f"quote rejected by the imperative/tool/URL filter: {quote[:80]}")
    if _collapse(quote) not in _collapse(TEXT[url].read_text(encoding="utf-8")):
        raise SystemExit(f"quote not found in saved text for {url}: {quote[:80]}")


def claim(text: str, url: str, quotes: list[str], evidence_scope: str, extra: str = "") -> dict:
    for q in quotes:
        check_quote(q, url)
    note = "; ".join(f'Quote: "{q}"' for q in quotes)
    if extra:
        note = f"{note}. {extra}" if note else extra
    return {
        "claim": text,
        "source_url": url,
        "confidence": "high" if evidence_scope == "model" else "medium",
        "scope": "model-specific",
        "evidence_scope": evidence_scope,
        "note": f"{note} Verified {VERIFIED}." if note else f"Verified {VERIFIED}.",
    }


CLAIMS = [
    claim("Reasoning effort accepts low, medium (the default), high, xhigh, and max.",
          GUIDE, ["Set reasoning.effort to low, medium (default), high, xhigh, or max."], "model"),
    claim("The none and minimal reasoning efforts are not supported; callers that used none should start with low.",
          GUIDE, ["The none and minimal reasoning efforts are not supported.",
                  "GPT-6 Astra and GPT-6.1 Sol do not support none; use low instead."], "model"),
    claim("Tool calling requires the Responses API; Chat Completions supports requests without tools.",
          GUIDE, ["Use the Responses API for tool calling. Chat Completions supports requests without tools."], "model"),
    claim("When reasoning effort is not none, remove temperature, top_p, and top_logprobs, and on Chat Completions also remove logprobs.",
          GUIDE, ["When reasoning effort is not none, remove temperature, top_p, and top_logprobs. For Chat Completions, also remove logprobs."],
          "model-family", "Stated in the migration checklist that opens with setting model to gpt-6-astra, gpt-6.1-sol, or gpt-6-luna."),
    claim("When migrating from GPT-5.5 or earlier, replace prompt_cache_retention with prompt_cache_options.ttl set to 30m.",
          GUIDE, ['When migrating from GPT-5.5 or earlier, replace prompt_cache_retention with prompt_cache_options.ttl set to "30m".'],
          "model-family", "Same migration checklist as above."),
    claim("When an application changes reasoning effort between responses, use configuration_update items in standard single-agent requests and keep request-level effort unchanged to preserve the cached prefix.",
          GUIDE, ["If your application changes effort between responses, use configuration_update items in standard, single-agent requests. Keep request-level reasoning.effort unchanged to preserve the prompt prefix for caching."],
          "model-family", "Same migration checklist as above."),
    claim("The vendor positions it for complex coding, computer use, and professional work when near-Astra performance at a lower cost is wanted, and tells callers to compare it with Astra on their own tasks.",
          GUIDE, ["Use GPT-6.1 Sol for complex coding, computer use, and professional work when you want near-Astra performance at a lower cost.",
                  "Compare it with Astra on your tasks to assess the tradeoff between quality and cost."], "model"),
    claim("Callers already on gpt-6-sol are directed to the migration guidance before switching to GPT-6.1 Sol.",
          GUIDE, ["If you already use gpt-6-sol, review the migration guidance before switching to GPT-6.1 Sol."], "model"),
    claim("The models catalog lists it at 2 US dollars per million input tokens and 10 per million output tokens, one fifth of gpt-6-astra's listed 10 and 50.",
          MODELS, ["$2 / Input MTok", "$10 / Output MTok", "Near-Astra performance for complex work at a lower cost."], "model",
          "Astra's row on the same page lists $10 / Input MTok and $50 / Output MTok. The page states the prices, not a benchmark."),
    claim("The models catalog lists a 1.05M-token context window, 128K maximum output tokens, an April 30, 2026 knowledge cutoff, and Functions, Web search, File search, and Computer use tools, the same values as gpt-6-astra's row.",
          MODELS, ["Near-Astra performance for complex work at a lower cost."], "model",
          "Row values read from the saved models.txt lines following 'Model ID gpt-6.1-sol': Max output 128K tokens; Context window 1.05M; Knowledge cutoff Apr 30, 2026."),
    claim("The guide's prompting best practices address behavior observed with GPT-6 Astra, and the vendor says to evaluate them with the chosen model; none is stated as measured on GPT-6.1 Sol.",
          GUIDE, ["They address behavior observed with GPT-6 Astra; evaluate them with your chosen model and workload."], "model-family"),
    claim("The guide's delegation prompt tells the model to parallelize work by delegating tasks to another agent whenever it could save time or improve quality.",
          GUIDE, [], "model-family",
          "Quote withheld: it is an imperative addressed to an agent. Recorded and deliberately NOT adopted into any shared body: the catalog's agent-orchestration-primitives overrides it with the named-problem escalation gate, as for gpt-6-astra."),
]

ASTRA_DELTA = [
    ("Start at low instead of none or minimal; none unsupported", "same", "stated for GPT-6.1 Sol by name"),
    ("configuration_update for effort changes between responses", "same", "migration checklist covering gpt-6.1-sol"),
    ("Tool calling requires the Responses API", "same", "stated for GPT-6.1 Sol by name"),
    ("Async tools via async: true and the original call_id", "not stated for Sol", "the What's new section names the GPT-6 family only"),
    ("Remove temperature, top_p, and top_logprobs", "same", "migration checklist covering gpt-6.1-sol"),
    ("Fast mode has no latency SLA and is unavailable with EU residency", "not stated for Sol", "the page names GPT-6 Astra, GPT-6 Sol, and GPT-6 Luna, not GPT-6.1 Sol"),
    ("Replace prompt_cache_retention with prompt_cache_options.ttl 30m", "same", "migration checklist covering gpt-6.1-sol"),
    ("Treat action-phrased prompts as instructions to act", "not stated for Sol", "Astra-observed behavior; vendor says to evaluate per model"),
    ("User instructions take precedence over skill guidelines", "not stated for Sol", "Astra-observed behavior; vendor says to evaluate per model"),
    ("Do not write tests for reversible, low-impact changes", "not stated for Sol", "Astra-observed behavior; vendor says to evaluate per model"),
    ("Parallelize by delegating to another agent", "same prompt, not adopted", "family prompt; overridden by agent-orchestration-primitives"),
    ("Release date and most-capable positioning", "different", "Sol is positioned as near-Astra at lower cost; no release date on these pages"),
]


def codex_roster() -> list[str]:
    """The platform's own live enumeration, recorded verbatim (research-runbook Step 1)."""
    script = HERE.parents[5] / "catalog/skills/ai-development/model-routing/scripts/enumerate-models.sh"
    out = subprocess.run(["bash", str(script), "codex"], capture_output=True, text=True, encoding="utf-8", timeout=120, check=True).stdout
    return [m["slug"] for m in json.loads(out)["models"]]


def main() -> int:
    payload = {
        "platform": "codex",
        "roster_source": "api",
        "verified_at": VERIFIED,
        "roster": codex_roster(),
        "models": {"gpt-6.1-sol": CLAIMS},
    }
    (HERE / "payload.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in ASTRA_DELTA)
    (HERE / "astra-delta.md").write_text(
        "# GPT-6.1 Sol against the gpt-6-astra profile\n\n"
        "One row per recorded gpt-6-astra claim, read from the pages saved on 2026-10-01.\n\n"
        "| gpt-6-astra claim | For GPT-6.1 Sol | Evidence |\n|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )
    print(f"payload: {len(CLAIMS)} claims, roster {payload['roster']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
