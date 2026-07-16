# Skill-Activation Rules Convention

A `skill-rules.json` file is a declarative, project-local ruleset that maps prompt keywords and edited file paths to Nexus-Hub skills. Two opt-in hooks read it: `skill-activation-suggest.py` (on prompt submit) suggests a skill when the prompt matches, and `skill-guard.py` (before an Edit/Write) suggests a skill when the edited file matches. It is a **deterministic backstop** to the model-judgment triggering that skill descriptions drive, aimed at the under-triggering the AGENTS.md description-style section acknowledges. It does not replace description-based triggering; it catches the narrow, project-specific cases where the model would otherwise skip a relevant skill.

The template is [`catalog/hooks/skill-rules.example.json`](../hooks/skill-rules.example.json) (installed at `~/.nexus-hub/hooks/skill-rules.example.json`). Copy it to your project's `.claude/skill-rules.json` and tailor it.

## Fail-open and opt-in by design

This convention inverts the fail-closed posture of the pattern it adapts. Nexus-Hub's hook philosophy is advisory-first:

- Both hooks are **suggest-only by default**. They print a suggestion and exit 0; they never block.
- A rule blocks an edit **only when both** its `enforcement` is `block` **and** the environment sets `NEXUS_SKILL_GUARD_BLOCK=1`. Absent the flag, a `block` rule still only suggests.
- Both hooks **fail open**: any parse error, a missing rules file, or any internal exception exits 0 without blocking.
- Both hooks are **no-ops when `skill-rules.json` is absent**, so installing them changes nothing until a project opts in by creating the file.
- Both honor the standard opt-outs: `NEXUS_DISABLED_HOOKS=skill-activation-suggest,skill-guard` disables by name, and `NEXUS_HOOK_PROFILE=minimal` skips all advisory hooks.

## Where the rules file lives

The hooks look for the active rules file in this order and use the first found:

1. the path in the `NEXUS_SKILL_RULES` environment variable (explicit override),
2. `.claude/skill-rules.json` (relative to the working directory),
3. `skill-rules.json` (repo root),
4. `.nexus-hub/skill-rules.json`.

If none exists, the hooks are silent no-ops.

## Schema

```json
{
  "version": 1,
  "rules": [
    {
      "skill": "security-review",
      "enforcement": "suggest",
      "promptTriggers": {
        "keywords": ["auth", "login", "password"],
        "intentPatterns": ["\\b(add|change).{0,24}\\bauth\\b"]
      },
      "fileTriggers": {
        "pathPatterns": ["*/auth/*", "*auth*"],
        "pathExclusions": ["*.test.*", "*/tests/*"],
        "contentPatterns": ["password", "api[_-]?key"]
      },
      "skipConditions": {
        "skillAlreadyUsed": true,
        "env": "NEXUS_SKIP_SECURITY_REVIEW"
      },
      "message": "Editing auth code - consider loading security-review."
    }
  ]
}
```

Per-rule fields:

- **`skill`** (required): the Nexus-Hub skill name to suggest.
- **`enforcement`**: `suggest` (default) | `remind` | `block`. `suggest` and `remind` are advisory; `block` gates the edit only under `NEXUS_SKILL_GUARD_BLOCK=1`.
- **`promptTriggers`** (used by `skill-activation-suggest.py`): `keywords` (case-insensitive substrings matched against the submitted prompt) and `intentPatterns` (case-insensitive regular expressions). A rule fires when any keyword or any pattern matches.
- **`fileTriggers`** (used by `skill-guard.py`): `pathPatterns` (fnmatch-style globs matched against the edited path, normalized to forward slashes; note that `*` spans `/`), `pathExclusions` (globs that veto a match), and optional `contentPatterns` (regexes; when present, the new file content must also match at least one). A file trigger fires when a `pathPattern` matches, no `pathExclusion` matches, and (if `contentPatterns` is set) the content matches.
- **`skipConditions`**: `skillAlreadyUsed` (when true, the rule is skipped if the skill has already run this session, so the hook does not re-nag - requires `skill-tracker.py`) and `env` (the name of an environment variable that, when set to a non-empty value, skips this rule).
- **`message`**: the advisory text shown to the user or agent when the rule fires. Keep it one line and actionable.

## The optional usage tracker

`skill-tracker.py` (a PostToolUse hook on the `Skill` tool) records which skills have run this session to a small state file, so `skipConditions.skillAlreadyUsed` works and the hooks do not re-suggest a skill that is already loaded. It is optional: without it, `skillAlreadyUsed` conditions simply never trigger a skip (the hooks still suggest, they just do not dedupe across a session).

## Registration

Registering the hooks edits `catalog/hooks/settings.json` (an ask-first change in this repo). The activation hook goes under `UserPromptSubmit`; the guard goes under `PreToolUse` with an `Edit|MultiEdit|Write` matcher; the tracker goes under `PostToolUse` with a `Skill` matcher. All three are advisory and opt-out via `NEXUS_DISABLED_HOOKS`. The block-mode env flag (`NEXUS_SKILL_GUARD_BLOCK=1`) is strictly opt-in and off by default.

## Self-check for a project's rules file

- [ ] The file lives at one of the four discovery locations.
- [ ] Every rule names a real skill and a one-line, actionable `message`.
- [ ] `enforcement` is `suggest` unless the project deliberately wants a `block` rule (and knows it is inert without `NEXUS_SKILL_GUARD_BLOCK=1`).
- [ ] `pathExclusions` keep the file triggers from firing on tests and generated files.
- [ ] The list is short enough to stay useful; prefer a few high-value rules over an exhaustive map.
