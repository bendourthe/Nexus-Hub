# Decision: Seed a Kimi behavioral default via a `.kimi/agent.yaml` companion file

Status: rejected - the file was never documented by the vendor; it was inferred from neighbouring platforms and had to be withdrawn in v3.15.0

## Problem

Nexus-Hub seeds per-platform behavioral defaults (reasoning effort, model pin, approval policy) at install time. Every supported platform needs its lever identified. For Kimi, no lever had been found.

## Proposal

Ship a `.kimi/agent.yaml` companion file carrying the platform's behavioral default, matching the shape used by neighbouring platforms that do document a config file.

## Alternatives considered

- **Record "no lever documented" and ship nothing for this platform.** Rejected at the time as an incomplete-looking roster. This was the correct answer and was not taken.
- **Ask users to configure it manually.** Considered unnecessary given the apparent similarity to other platforms.

## Risks

Stated at the time as low, on the reasoning that the file shape resembled other platforms and an unread config file is inert.

## Verdict

The file was **fabricated rather than found**. No fetched vendor document described it. It shipped, did nothing, and was removed in v3.15.0.

The risk assessment was wrong in a way worth naming: an invented config file is not inert. It is a false positive in the roster, it implies vendor support that does not exist, and where a platform later defines that same path with different semantics it becomes an active conflict. Pinning a value a user's account cannot reach breaks their tool rather than leaving it unconfigured.

The durable rule now enforced by `tests/validators/test_platform_defaults_levers.py`: a platform appears in `configs/platform-defaults.json` only when a **fetched official vendor document** names the lever, recorded with a `source_url` and a `verified` date, and only when `docs/policy/platform-defaults-levers.md` classifies it VERIFIED. Never seed from a blog post, a forum, an aggregator, or an analogy to a similar-looking platform.

**"No lever documented" is a valid and expected result.** An empty cell in the roster is information, not a gap to fill.

## Alternatives considered on re-proposal

If this is re-proposed, the question to answer first is not "does this file shape look right" but "which vendor document names it, and when was that document fetched". Absent that URL and date, the answer is unchanged.
