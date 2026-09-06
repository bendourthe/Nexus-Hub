# Decision Note - Does `gpt-6-astra` enter the model map, and at which tier?

**Plan**: `docs/releases/v4/v4.7/plans/v4.7.0-adoption-gpt-6-astra-prompting.md`, sub-task 1.1 (T037); executed inside the main plan's sub-task 1.2 refresh
**Date**: 2026-09-05
**Pages fetched**: `https://developers.openai.com/api/docs/models` and `https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra`, both on 2026-09-05

## Outcome

**Mapped at `frontier`.** Both pages describe general availability today, so the map's own rule (a tier value must name a model the user's account can reach) admits the id. `gpt-5.6-sol` moves to `strong`, `gpt-5.6-terra` takes `standard` alone, `gpt-5.6-luna` stays `fast`.

## Quoted evidence

- Models catalog, 2026-09-05: `gpt-6-astra` is listed among the flagship models as "Our most capable model, built for the hardest end-to-end work". The page carries no sentence about trusted access, a rollout program, or API access "in the coming days"; the summarized fetch reported "no statements about gpt-6-astra's availability, trusted access, rollout timing, or API access restrictions", and the model is "presented as currently available in the flagship models section".
- Model guide, 2026-09-05: the page "contains no explicit statements about availability, access restrictions, or rollout status".
- For contrast, the comparison recorded on 2026-09-04 that the catalog then "described a trusted-access rollout with API access 'in the coming days'". That sentence is gone one day later, which is the re-check condition the plan named.

## Why the ordering is the vendor's, not a judgment

The plan allowed moving `gpt-5.6-sol` to `strong` only if the vendor's own description supports the ordering. The catalog's descriptions on 2026-09-05 are: `gpt-6-astra` "Our most capable model"; `gpt-5.6-sol` "Flagship model for complex professional work"; `gpt-5.6-terra` "GPT-5.6 model that balances intelligence and cost"; `gpt-5.6-luna` "GPT-5.6 model optimized for cost-sensitive workloads". Most capable, then flagship, then balanced, then cost-optimized is a strict ordering in the vendor's words, so the four tiers now hold four distinct ids and `gpt-5.6-terra` no longer doubles as `strong` and `standard`.

## Where the decision lives

- `catalog/skills/ai-development/model-routing/references/last-known-model-map.json`: OpenAI cells updated, `verified_as_of` 2026-09-05, note `refresh_2026_09_05_v470`, and the `deliberately_unmapped` note records the 2026-09-04 exclusion and today's admission. `model-map.py validate` result is quoted in the Phase 1 history.
- `docs/releases/v4/v4.8/plans/v4.8.0-adoption-agentic-loops-and-coding-agent-practice.md`: its map is merged and historical, so a one-sentence note under the map cites this file rather than editing the cell (amendment sub-task 1.2).
- `docs/releases/v4/v4.4/plans/v4.4.6-guide-learning-experience.md` places `gpt-6-astra` at frontier; that map now agrees with this decision, and the file lives only on the concurrent guide branch, so it is not edited from this branch (recorded in `known-gaps.md`).

## Human check

A Codex user with a real `gpt-6-astra` entitlement should confirm the id resolves on their account; the map's rule is about reachability, and a documentation page is the best available proxy, not proof.
