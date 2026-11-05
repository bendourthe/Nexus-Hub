# Phase 5 scratch-home run (v4.14.6, T036)

Driver output for the real Windows installer run into a scratch home. Method, hashes, and the reading of each result are in `v4.14.6-admission.md` (section T036). The driver is `phase-5-scratch-home-driver.ps1.txt` in this folder. Scratch root C:/nh5 (home C:/nh5/home, editor extensions C:/nh5/ext, editor user data C:/nh5/ud).

## Stage output

```text
=== stage baseline  10:05:29
baseline written
=== stage install1  10:06:06
installer run1 : exit 0 timedOut=False in 262s
=== stage observe  10:10:32
list-extensions:
nexus-hub.claude-usage-monitor@0.10.0
nexus-hub.codex-usage-monitor@0.2.11
nexus-hub.copilot-usage-monitor@0.1.0
nexus-hub.nexus-hub-settings@0.1.0

cli show exit 0
=== stage host  10:10:33
host trusted : exit 0 timedOut=False out=True
host untrusted : exit 0 timedOut=False out=True
=== stage set  10:10:55
set effort low -> exit 0
set model sonnet --tool claude -> exit 0
set model gpt-test-model --tool codex -> exit 0
set attribution off -> exit 0
set posture accept-edits -> exit 0
=== stage install2  10:11:00
installer run2 : exit 0 timedOut=False in 312s
claude settings after rerun: 4c133992d127cd8d  codex: e9950b2a975acd99  record: 36e27bf38ba971e1
=== stage after  10:16:12
vscode user settings.json                    before=cc2bf1bf03d3d898  after=cc2bf1bf03d3d898  identical
claude settings.json                         before=0dd843698768f37e  after=0dd843698768f37e  identical
codex config.toml                            before=a08f300da3bc63cb  after=a08f300da3bc63cb  identical
copilot settings.json                        before=cfb6e024984de203  after=cfb6e024984de203  identical
real vscode extensions folder (names)        before=bb8506298fa3b5a9 (45 entries)  after=bb8506298fa3b5a9 (45 entries)  identical
real cursor extensions folder (names)        before=cc96caffee8d06e0 (18 entries)  after=cc96caffee8d06e0 (18 entries)  identical
real antigravity extensions folder (names)   before=7a4524b66eae3ae8 (13 entries)  after=7a4524b66eae3ae8 (13 entries)  identical
nexus-hub tree (no runs, edit-guard, provenance, usage-probe) before=94376b6f4e770f03 (95965 files)  after=94376b6f4e770f03 (95965 files)  identical
gemini tree                                  before=515790a02f34b0b2 (20740 files)  after=515790a02f34b0b2 (20740 files)  identical
=== done 10:16:54

[exited with code 0]
```

## Panel versus show --json

Before any set, the installed extension in an isolated VS Code extension host against the scratch home.

| control | tool | surface | show state | panel badge text | panel value |
|---|---|---|---|---|---|
| attribution | claude | cli | tool-default | Tool default | - |
| attribution | codex | cli | not-settable | Not settable | - |
| attribution | copilot-cli | cli | not-settable | Not settable | - |
| attribution | vscode-copilot | vscode-host | not-settable | Not settable | - |
| effort | claude | cli | overridden-by | Overridden by env CLAUDE_CODE_EFFORT_LEVEL (settings.json env block) | - |
| effort | codex | cli | in-effect | In effect | medium |
| effort | copilot-cli | cli | not-settable | Not settable | - |
| effort | vscode-copilot | vscode-host | not-settable | Not settable | - |
| git_guardrails | internal | cli | tool-default | Tool default | - |
| model | claude | cli | in-effect | In effect | opus |
| model | codex | cli | in-effect | In effect | gpt-6-astra |
| model | copilot-cli | cli | not-settable | Not settable | - |
| model | vscode-copilot | vscode-host | not-settable | Not settable | - |
| posture | claude | cli | tool-default | Tool default | - |
| posture | claude | vscode-host | not-settable | Not settable | - |
| posture | codex | cli | in-effect | In effect | ask/accept-edits |
| posture | copilot-cli | cli | not-settable | Not settable | - |
| posture | vscode-copilot | vscode-host | not-settable | Not settable | - |

State disagreements between the 18 panel rows and the 18 `show --json` records: 0. Extension path reported by the host: `C:\nh5\ext\nexus-hub.nexus-hub-settings-0.1.0`, version 0.1.0. Trusted workspace read-only: False. Untrusted workspace read-only: True. The `nexusHubSettings.open` command is registered and the view was opened: True.

## show --json across the changes

Rows whose state or value changed. Every other row is identical in all three captures.

| control | tool | before set | after set | after installer rerun |
|---|---|---|---|---|
| attribution | claude | tool-default - | in-effect off | in-effect off |
| effort | claude | overridden-by - | overridden-by low | overridden-by low |
| effort | codex | in-effect medium | in-effect low | in-effect low |
| model | claude | in-effect opus | in-effect sonnet | in-effect sonnet |
| model | codex | in-effect gpt-6-astra | in-effect gpt-test-model | in-effect gpt-test-model |
| posture | claude | tool-default - | in-effect accept-edits | in-effect accept-edits |

`show --json` after the set equals `show --json` after the installer rerun, record for record: True.
