# Phase 6 scratch-home re-proof (v4.14.6, T042)

Driver output for the final-phase build installed by the real Windows installer into a scratch home, and the CLI-driven re-proof of every shipped control. Method and the reading of each result are in `../v4.14.6-last-phase-evidence.md` (section Tier 3 deep pass). Drivers: `phase-6-scratch-home-driver.ps1.txt` and `phase-6-reproof-driver.py.txt` in this folder. Scratch root C:/nh6 (home C:/nh6/home).

## Installer and host stages (first pass)

```text
=== stage baseline 11:58:01
baseline written

=== stage install1 11:59:01
installer run1 : exit 0 timedOut=False in 281s

=== stage observe 12:03:42
list-extensions:
nexus-hub.claude-usage-monitor@0.10.0
nexus-hub.codex-usage-monitor@0.2.11
nexus-hub.copilot-usage-monitor@0.1.0
nexus-hub.nexus-hub-settings@0.1.0

cli show exit 0

=== stage host 12:03:45
host trusted : exit 0 timedOut=False out=True
host untrusted : exit 0 timedOut=False out=True

=== done 12:04:06
```

## Re-proof (installed CLI, real tools, no model request)

```text
=== prove: installed CLI, scratch home C:\nh6\home
baseline files: {"claude settings.json": "6719012acb1ef34c", "codex config.toml": "ee6f290df031c81b", "ownership record": "406e9052d7c5782d", "guardrails.json": "absent"}
PASS  effort set low (both tools): exit 0
PASS  show reports the legacy variable: state=overridden-by layer=env CLAUDE_CODE_EFFORT_LEVEL (settings.json env block)
PASS  override wins in the real tool: /effort status with the env block present -> high (modelSettings is low)
PASS  remove-override needs a person: exit 3, no file changed, message: nexus-hub settings: refused: this change removes a setting you did not choose and needs a person: ru
PASS  Claude effort low per current model: {'claude-fable-5-1': 'low', 'claude-opus-5-5': 'low', 'claude-sonnet-5-5': 'low', 'claude-haiku-5-5': 'low'}
PASS  Claude top-level key covers an older model: claude-opus-5 -> low
PASS  Claude effort high per current model: {'claude-fable-5-1': 'high', 'claude-opus-5-5': 'high', 'claude-sonnet-5-5': 'high', 'claude-haiku-5-5': 'high'}
PASS  Codex effort key: config.toml model_reasoning_effort = 'high'
PASS  Claude model: init model -> claude-sonnet-5-5
PASS  Codex model: codex doctor model -> gpt-5.6-sol
PASS  Copilot CLI model is Not-Settable: exit 4, no file changed
PASS  posture ask: claude permissionMode=default; codex approval=on-request sandbox=workspace-write
PASS  full-auto refused inside an agent session: exit 3, no file changed: nexus-hub settings: refused: CLAUDECODE is set, so an agent session is running this command. A change that lowers a safe
PASS  full-auto refused without a terminal: exit 3, no file changed: nexus-hub settings: refused: this change lowers a safety barrier and needs a person: run it in an interactive terminal (
      dry-run exit 0; planned writes: { "schema_version": 1, "action": "set", "control": "posture", "value": "full-auto", "tool": null, "dry_run": true, "confirmation": { "required": true, "kind": null }, "results": [ { "tool": "claude", "write": "claude.posture", "file": "~/.c
      catalog value for full-auto: claude defaultMode='bypassPermissions'; codex='never'
PASS  full-auto values are honored by the tools (stand-in on copies): claude permissionMode=bypassPermissions; codex approval=never sandbox=workspace-write
PASS  posture accept-edits: claude permissionMode=acceptEdits; codex approval=on-request sandbox=workspace-write
PASS  attribution off writes both keys: settings.json attribution = {'commit': '', 'pr': ''}
NOT RE-RUN: the tool-side attribution observation (W08) needs a paid model request; the Phase 1 proof stands and this pass spent nothing.
PASS  git-guardrails on blocks the bypass flag: guardrails.json { "block_git_bypass_flags": true }; hook exit 2 (BLOCKED: 'git commit --no-verify -m x' skips git hooks or commit signing (--no-verify skips git hooks). The op); benign command exit 0
PASS  git-guardrails off refused without a terminal: exit 3, no file changed
PASS  hook allows the flag when the switch is off (stand-in on a copy): hook exit 0
states after set: effort/claude=overridden-by:high; effort/codex=in-effect:high; model/claude=in-effect:claude-sonnet-5-5; model/codex=in-effect:gpt-5.6-sol; posture/claude=in-effect:accept-edits; posture/claude=not-settable:None; posture/codex=in-effect:ask/accept-edits; attribution/claude=in-effect:off; attribution/codex=not-settable:None; git_guardrails/internal=in-effect:on
files after set: {"claude settings.json": "37457f1c93ee2e6b", "codex config.toml": "48100edda063da41", "ownership record": "eb361f06c18a1514", "guardrails.json": "5a6857d0bf9721aa"}
RESULT: PASS
exit=0
```

## Reset to the baseline

```text
=== reset
PASS  reset effort: exit 0 
PASS  reset model: exit 0 
PASS  reset posture: exit 0 
PASS  reset attribution: exit 0 
PASS  reset git_guardrails: exit 0 
PASS  claude settings.json byte-identical after reset: before set 6719012acb1ef34c, after reset 6719012acb1ef34c
PASS  codex config.toml byte-identical after reset: before set ee6f290df031c81b, after reset ee6f290df031c81b
PASS  ownership record emptied: entries=[]
PASS  guardrails.json byte-identical after reset: before set absent, after reset absent
RESULT: PASS
exit=0
```

## Reapply, second installer pass, compare

```text
=== reapply the final non-weakening values
PASS  set effort high: exit 0
PASS  set model claude-sonnet-5-5 --tool claude: exit 0
PASS  set model gpt-5.6-sol --tool codex: exit 0
PASS  set posture accept-edits: exit 0
PASS  set attribution off: exit 0
PASS  set git_guardrails on: exit 0
files reapplied: {"claude settings.json": "37457f1c93ee2e6b", "codex config.toml": "48100edda063da41", "ownership record": "84da44cccda143ab", "guardrails.json": "5a6857d0bf9721aa"}
RESULT: PASS
exit=0
=== stage install2 12:09:30
installer run2 : exit 0 timedOut=False in 316s
claude settings after rerun: 859bb9a305c58c6c  codex: 48100edda063da41  record: 84da44cccda143ab

=== done 12:14:48
=== compare after the second installer run
PASS  show --json identical record for record: 18 records compared
PASS  codex config.toml unchanged by the installer: 48100edda063da41 -> 48100edda063da41
PASS  ownership record unchanged by the installer: 84da44cccda143ab -> 84da44cccda143ab
PASS  guardrails.json unchanged by the installer: 5a6857d0bf9721aa -> 5a6857d0bf9721aa
PASS  claude settings.json still holds the values (parsed): bytes 37457f1c93ee2e6b -> 859bb9a305c58c6c
RESULT: PASS
```

## Real-file guard

```text
vscode user settings.json                    before=cc2bf1bf03d3d898  after=cc2bf1bf03d3d898  identical
claude settings.json                         before=0dd843698768f37e  after=0dd843698768f37e  identical
codex config.toml                            before=a08f300da3bc63cb  after=a08f300da3bc63cb  identical
copilot settings.json                        before=cfb6e024984de203  after=cfb6e024984de203  identical
real vscode extensions folder (names)        before=bb8506298fa3b5a9 (45 entries)  after=bb8506298fa3b5a9 (45 entries)  identical
real cursor extensions folder (names)        before=cc96caffee8d06e0 (18 entries)  after=cc96caffee8d06e0 (18 entries)  identical
real antigravity extensions folder (names)   before=7a4524b66eae3ae8 (13 entries)  after=7a4524b66eae3ae8 (13 entries)  identical
nexus-hub tree (no runs, edit-guard, provenance, usage-probe) before=4f2d49629a24b129 (95969 files)  after=6bf27d14afeba056 (95969 files)  DIFFERENT
gemini tree                                  before=f00a5ce5d8c34d79 (20737 files)  after=f00a5ce5d8c34d79 (20737 files)  identical

```

## Panel versus show --json

```text
panel rows 18 show records 18 state/value disagreements 0 []
trusted workspace read-only: False | untrusted workspace read-only: True | reason: This workspace is not trusted, so the panel shows the current state and cannot change anything. Trust the workspace to change a default.
steps.openedView: True | extension: 0.1.0 | path ends: nexus-hub.nexus-hub-settings-0.1.0
commands registered: 6 open command present: True
steps keys: ['openedView', 'registered', 'precheck', 'afterApply', 'afterRestore']
precheck {"ok": true, "apply": ["chat.tools.global.autoApprove"], "skipped": ["claudeCode.initialPermissionMode"]}
```
