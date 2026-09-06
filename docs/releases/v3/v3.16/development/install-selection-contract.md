# Install-Selection Contract (v3.16.1)

**Status**: normative, locked for v3.16.1 Phase 5
**Date**: 2026-08-08
**Implemented by**: `scripts/lib/installer/selection.py` (Python), `scripts/installer.sh` (Bash, Phase 6.1), `scripts/installer.ps1` (PowerShell, Phase 6.2)
**Verified by**: `tests/fixtures/install-selection/cases.json` against all three implementations

This document defines what a Nexus-Hub install selects, in terms precise enough to implement three times and check against one fixture matrix. Where this document and an implementation disagree, this document is correct.

The baseline it builds on is [`selective-install-baseline.md`](selective-install-baseline.md).

## 1. Selectors

Three selector kinds, drawn from `data/bundles.json`:

| Selector | Flag (Bash) | Parameter (PowerShell) | Cardinality |
|---|---|---|---|
| Profile | `--profile <id>` | `-Profile <id>` | At most one |
| Module | `--modules <id>[,<id>...]`, repeatable | `-Modules <id>[,<id>...]` | Zero or more |
| Role bundle | `--bundles <id>[,<id>...]`, repeatable | `-Bundles <id>[,<id>...]` | Zero or more |

Rules:

1. **Comma-separated and repeatable are equivalent.** `--modules a,b` and `--modules a --modules b` produce identical results.
2. **Whitespace around a comma-separated element is stripped.** An empty element (`a,,b`) is an error, not a silently dropped item.
3. **Identifiers are matched exactly**, case-sensitively, against `id` fields in `data/bundles.json`. No prefix matching, no fuzzy matching, no case folding. A typo is an error, never a near-miss guess.
4. **At most one profile.** Two `--profile` flags is an error.

### 1.1 The no-selector default

**No selector of any kind means `full`.** This is the compatibility guarantee: an invocation with no `--profile`, `--modules`, or `--bundles` produces exactly the file set the pre-v3.16.1 installer produced, byte for byte, except for additive selection metadata written into the manifest.

### 1.2 `full` is exclusive

`--profile full` is valid alone. Combining it with any module or bundle selector is an error rather than a no-op union, because the combination always means the user misunderstood one of the two: either they think `full` is a base to add to, or they think the modules narrow it. Failing tells them which.

## 2. Resolution

Resolution is a pure function from (selectors, catalog, bundle metadata) to a **selection plan**. It performs no I/O beyond reading its inputs and writes nothing.

### 2.1 Order of operations

```
1. Parse selectors                     -> error on malformed input
2. Validate every id exists            -> error on unknown id
3. Check profile exclusivity           -> error on `full` + others
4. Expand each selector to skill ids
5. Union the expansions                -> deduplicate
6. Compute transitive dependency closure -> error on cycle or missing target
7. Derive eligible commands and agents
8. Attach always-present surfaces
9. Sort everything and compute the hash
10. Emit the plan
```

Steps 1 through 6 must all succeed before any caller writes a single file. This is the **fail-before-write** rule and it is the contract's most important property: an invalid selector must never leave a half-installed tree.

### 2.1a Selection entries are not uniform

This is the single easiest thing to get wrong, and getting it wrong fails silently.

| Entry kind | How it declares its skills |
|---|---|
| Module | A flat `skills` array |
| Role bundle | A flat `skills` array |
| Profile | **No `skills` array at all.** It COMPOSES, via `bundles`, `modules`, and `extra_skills` |
| The `full` profile | Marked `"all": true`. It does not list the catalog |

Expansion unions all four keys (`skills`, `extra_skills`, referenced `modules`, referenced `bundles`), so an entry may use any combination. References are followed with cycle protection; no profile references another profile today, but an unguarded expansion would not terminate if one ever did.

A resolver that reads only `skills` resolves **every real profile to the empty set**, which then surfaces as an "empty selection" user error rather than as the modeling bug it is. That failure mode is why `test_every_real_bundle_resolves` runs against the actual `data/bundles.json` rather than only against fixtures, and why the fixture profiles mirror the composed shape instead of a convenient flat one.

The `full` marker is authoritative because `"all": true` is what `data/bundles.json` actually uses; matching on the id `full` is a fallback for a catalog that omits the marker.

### 2.2 Union semantics

Multiple selectors **union**; they never intersect and never subtract. `--profile core --modules ai-engineering` installs everything in `core` plus everything in `ai-engineering`.

There is no precedence between selector kinds because union is commutative and associative. The result does not depend on the order the selectors were supplied, and a fixture asserts this.

### 2.3 Deduplication and ordering

- A skill named by two selectors appears once.
- A selector supplied twice is equivalent to supplying it once.
- Every list in the plan is sorted by ascending Unicode code point of the id.

Sorting is what makes the plan deterministic and therefore hashable and diffable. Two invocations with the same inputs must produce byte-identical plans, regardless of selector order or the iteration order of any map in any of the three implementations. This is not cosmetic: it is how Phase 6 proves Bash, PowerShell, and Python agree.

### 2.4 Transitive dependency closure

Skill-to-skill dependencies are declared in an optional `skill_dependencies` object in `data/bundles.json`:

```json
"skill_dependencies": {
  "<skill-id>": ["<required-skill-id>", "..."]
}
```

A skill with no entry has no dependencies. **As of v3.16.1 this object is absent, so the closure is the identity function on current data.** The mechanism is specified and tested now because adding it later would mean changing resolution semantics after three implementations exist.

Closure is a breadth-first expansion over the declared edges until no new skill is added. Each added skill records the **reason** it entered the plan: `selector:<kind>:<id>` for a directly-selected skill, or `dependency:<skill-id>` for one pulled in by closure. Reasons are what let a user answer "why is this skill installed", and the fixtures assert them exactly.

A `Related Skills` wiki-link is **not** a dependency. Those links are navigational cross-references and are deliberately not traversed; treating them as edges would expand almost any selection to the full catalog.

### 2.5 Cycle detection

A dependency cycle is an error, reported with the participating skill ids in the order encountered. Cycles cannot occur with current data (no edges exist), but an unchecked closure over a future cycle would not terminate, so detection is required, not optional.

### 2.6 Surface eligibility for commands and agents

Commands and agents declare their required skills in an optional `surface_requirements` object in `data/bundles.json`:

```json
"surface_requirements": {
  "commands": { "<command-name>": ["<skill-id>", "..."] },
  "agents":   { "<agent-name>":   ["<skill-id>", "..."] }
}
```

Eligibility rule:

- A command or agent **with** a declaration installs only when **every** skill it requires is in the resolved skill set.
- A command or agent **with no** declaration **always installs**.

The undeclared default is deliberate and is the safer of the two options. Defaulting undeclared surfaces to "excluded under a focused selection" would silently shrink every install the moment selection shipped, before any declaration existed. Defaulting to "included" preserves today's behavior exactly and lets Phase 7.1 add declarations incrementally, each one narrowing the surface by a known amount. The cost is that until Phase 7.1 lands, a focused install may include a command whose skills are absent; that is a visible, documented gap rather than an invisible regression.

An excluded command or agent records its reason: `excluded:missing-skills:<skill-id>[,<skill-id>...]`.

### 2.7 Always-present surfaces

These install under **every** selection, including the narrowest, and are never filtered:

- hooks (subject to the existing `hooks_supported` platform capability gate)
- rules
- templates and style guides
- settings and permission configs
- context and memory templates
- data indexes and instruction files
- platform install-time defaults (`configs/platform-defaults.json` seeding)

Rationale: these are policy infrastructure, not capability. A user narrowing their skill set is asking for fewer capabilities, never for fewer guardrails. Filtering a secret-scan hook out of a focused install would make the focused path less safe than the default path, which inverts the purpose.

### 2.8 Skill-index content

Under a focused selection, the `{{SKILL_INDEX}}` block rendered into instruction files lists **only the resolved skills**. An index advertising a skill the agent cannot load is worse than a shorter index: it produces confident references to absent capability. This is a content rule, not a file rule; the instruction file itself is always present.

## 3. Failure modes

Every failure is detected before any write. Exit codes are uniform across the three implementations.

| Condition | Exit code | Message must name |
|---|---|---|
| Unknown profile / module / bundle id | 2 | The unknown id and the selector kind |
| Malformed selector (empty element, duplicate `--profile`) | 2 | The offending argument |
| `full` combined with another selector | 2 | Both selectors |
| Selection resolves to zero skills | 2 | The selectors that produced the empty set |
| Selection expands to the entire catalog without `full` | 0 + warning | The count, and that `full` is the direct way to say this |
| Bundle references a skill with no catalog directory | 3 | The bundle id and the missing skill id |
| Dependency cycle | 3 | The skill ids in the cycle |
| `data/bundles.json` unreadable or malformed | 3 | The parse failure |

Exit code 2 means the **user's input** was wrong; 3 means the **catalog** is wrong. Separating them matters because a user can fix the first and cannot fix the second.

The full-catalog case is a warning rather than an error because the union genuinely resolved and refusing it would be obstructive. But an unintended full install is a real outcome (a user selecting several broad bundles and believing they narrowed the install), so it is surfaced rather than silent.

Note that an empty selection is an error while a full one is a warning. That asymmetry is intentional: an empty install is never what anyone wanted, whereas a full install is the default and therefore always a legitimate end state.

## 4. The selection manifest

Resolution emits a deterministic, serializable plan. It is recorded in the install manifest under the additive `selection` key, and rendered by `print-config` and the install summary.

```json
{
  "requested": {
    "profile": "core",
    "modules": ["ai-engineering"],
    "bundles": []
  },
  "resolved": {
    "skills": ["ai-agent-development", "eval-pipeline-audit", "..."],
    "commands": ["implement", "plan", "..."],
    "agents": ["code-reviewer", "..."]
  },
  "reasons": {
    "eval-pipeline-audit": "selector:module:ai-engineering",
    "prompt-engineering": "selector:module:ai-engineering"
  },
  "excluded": {
    "commands": {},
    "agents": {}
  },
  "always_present": ["hooks", "rules", "templates", "settings", "context", "memory", "indexes"],
  "catalog": {
    "skill_count": 271,
    "bundles_version": "1.4.0"
  },
  "warnings": [],
  "hash": "sha256:..."
}
```

### 4.1 Hash

The hash covers the **resolved outcome**, not the request:

```
canonical = JSON of {resolved, always_present, catalog} with
            sorted keys, sorted arrays, no whitespace, UTF-8
hash      = "sha256:" + hex(sha256(canonical))
```

Excluding `requested` from the hash is deliberate: two different ways of asking for the same set (`--modules a,b` versus `--modules a --modules b`, or a different selector order) must produce the same hash, because they produce the same install. Excluding `warnings` keeps the hash stable across advisory-message wording changes.

The hash is the cross-implementation equality check. Bash, PowerShell, and Python each compute it independently over their own resolution; a mismatch on any fixture is a parity failure.

### 4.2 Backward compatibility

`InstallManifest.from_dict` reads every key with a default, so a manifest written before v3.16.1 has no `selection` key and loads cleanly. **A manifest with no `selection` is interpreted as a full install**, which is what it was. No migration, no schema bump, no reader change.

## 5. Lifecycle behavior

| Operation | Behavior |
|---|---|
| `install` with selectors | Resolve, validate, write, record the plan |
| `install` with no selectors | Full. Record a plan whose `requested` is empty |
| `upgrade` with no selectors | **Reuse the recorded selection.** An upgrade never widens or narrows scope by accident |
| `upgrade` with selectors | Replace the recorded request, after showing the resolved delta |
| `repair` | Reinstall the recorded resolved scope plus always-present surfaces. Never the full catalog |
| `doctor` | Report content drift and selector drift separately (see below) |
| `print-config`, `check`, summaries | Report the recorded resolved set; never widen it |
| `teardown` | Manifest replay, already scope-correct |

**Selector drift** is the case where the recorded selectors still resolve, but to a different set than when recorded, because the catalog changed. A skill added to a module the user selected is not content drift and must not be reported as corruption; it is a legitimate difference between the recorded plan and a fresh resolution, and `doctor` names it as such so the user can choose to repair into the new set.

## 6. Compatibility requirements

1. **Byte-equivalent full install.** A no-selector install produces the same files with the same contents as the pre-v3.16.1 installer. The only permitted difference is the additive `selection` key in the manifest.
2. **No new dependency.** Resolution uses each path's existing tooling: Python stdlib, `jq`-or-native in Bash, `ConvertFrom-Json` in PowerShell. Python is never required by a legacy installer.
3. **Existing flags unchanged.** `--platforms`, `--workspace`, `--branch`, `--enterprise`, `--force`, `--yes`, `--strict-permissions`, `--print-config` keep their current behavior and compose with selectors.
4. **Selection is orthogonal to platform choice.** `--platforms` picks *where* to install; selectors pick *what*. Neither constrains the other.
5. **No outbound call, credential, or telemetry** is introduced by any part of this contract.

## 7. Verification

- [ ] Selector parsing accepts comma-separated and repeatable forms identically
- [ ] No selector resolves to the full catalog, byte-equivalent to the prior installer
- [ ] `full` combined with any other selector exits 2
- [ ] Unknown ids exit 2 and name the id; catalog defects exit 3 and name the defect
- [ ] Every list in the plan is sorted; two selector orderings produce identical hashes
- [ ] Every resolved skill carries a reason (`selector:...` or `dependency:...`)
- [ ] Closure terminates and reports cycles with the participating ids
- [ ] A command or agent with unsatisfied declared requirements is excluded with its reason; one with no declaration installs
- [ ] Hooks, rules, templates, settings, context, memory, and indexes are present under every selection
- [ ] The rendered skill index lists only resolved skills
- [ ] No write occurs on any failing input
- [ ] A manifest with no `selection` key loads and is treated as a full install
- [ ] Upgrade with no selector preserves the recorded selection; with a selector, replaces it after showing the delta
- [ ] Bash, PowerShell, and Python produce identical hashes for every fixture case
