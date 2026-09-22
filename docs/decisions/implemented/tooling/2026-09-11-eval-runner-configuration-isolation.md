# Decision: Eval runner configuration isolation

Status: implemented - Claude and Codex run with documented isolation flags and a required model pin, while Gemini and OpenCode fail closed until full isolation is documented

## Problem

The skill-eval loop compared candidate and baseline arms while inheriting the operator's globally installed Nexus-Hub catalog. The skill under test could therefore load in the baseline arm, producing a plausible comparison of the skill against itself. Isolation flags differ by CLI, and inventing an equivalent flag from a similar product would repeat a prior repository failure.

## Decision

Only fetched official vendor documentation can authorize an isolation or model-selection flag. The verified contract is:

| CLI | Configuration isolation | Model pin | Official source | Verified |
|---|---|---|---|---|
| `claude` | `--setting-sources ""` | `--model <model>` | [Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage) | 2026-09-21 |
| `gemini` | None documented; `-e none` disables extensions only and does not exclude the documented settings layers | `--model <model>` | [Gemini CLI configuration reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md) | 2026-09-21 |
| `codex` | `--ignore-user-config --ignore-rules --ephemeral` | `--model <model>` | [OpenAI Codex exec CLI source](https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs) | 2026-09-21 |
| `opencode` | None documented; `--pure` disables external plugins only | `--model <provider/model>` | [OpenCode CLI reference](https://dev.opencode.ai/docs/cli/) | 2026-09-21 |

The runtime emits commands only for Claude and Codex. Gemini and OpenCode fail with a named isolation error before a subprocess starts. Every provider-backed run requires one run-level model pin. An eval entry may repeat that value but may not replace it; a conflict is reported and the explicit run pin governs.

## Alternatives considered

- **Treat Gemini `-e none` as isolation.** Rejected because it disables extensions while the official reference separately documents user, project, system, environment, and command-line configuration layers.

- **Point OpenCode at an empty config file or use `--pure`.** Rejected because the vendor documents config paths and a plugin-only pure mode, not a flag that suppresses every ambient configuration source.

- **Allow unsupported runners with a warning.** Rejected because the resulting number remains plausible and incomparable, reproducing the defect this decision closes.

- **Let each eval entry select its own model.** Rejected because a paired run can then compare different models and costs. A single run-level pin is the invariant; a conflicting entry is an error.

- **Keep model selection optional.** Rejected because isolation removes saved model settings, leaving a release-dependent CLI default that varies across operators and time.

## Consequences

Claude and Codex evals become comparable across operators when their CLI versions, model pins, cases, trials, and rubric are also recorded. Gemini and OpenCode remain unavailable to provider-backed evals until their vendors document full configuration isolation. Historical paired results remain historical observations but cannot seed post-isolation gates. Future vendor changes require re-verifying this decision and updating the runtime, reference, tests, and known-gap ledger together.
