# Windows Console Handbook Review

This incremental review verifies the distribution handbook against the console-window repair, including installer delivery, command behavior, deterministic assembly and the changed route section in both browser views.

## Source Review

The changed code inputs are `scripts/installer.ps1`, `scripts/installer.sh`, `scripts/nexus_hub_cli.py`, `scripts/nexus_git_attribution.py`, `scripts/nexus_process.py`. Both installers copy nexus_process.py alongside native commands. The CLI installs its shared subprocess default before launches; standalone attribution hooks carry explicit flags because they survive independently of the installer checkout. The shared policy hides Windows console children, preserves output and refuses conflicting console flags. These claims match the retained route paragraph and existing ownership explanation. Unchanged code inputs retain their prior content hashes; their unchanged claims were preserved.

## Build Review

The retained builder generated distribution.html from the updated Markdown/model and unchanged composition/design inputs. Its read-only check reproduced output SHA-256 105c97b8d3f46b2c2b97211a84259f72e5ed478bfd3349f925a706eabd3e61d1. The source map now includes the shared module as an explicit code dependency.

## Browser Review

Chromium 153.0.8010.12 measured all five reading sections and five presentation slides across 200 states with zero reported errors. The browser report covers geometry, offline loading, inventory, no-JS/print behavior and declared runtime checks. Numeric source values and additional declared control mappings were not supplied and are not claimed by those optional guards.

The changed route section was also inspected in fresh 1366x768 screenshots of reading and presentation views. The full new explanation is readable, the three-stage installation figure remains aligned, and presentation controls remain visible without text clipping. Existing slide IDs, theme assignments and five-slide budget are preserved. The representative screenshots are retained under %TEMP%/nexus-v4140-native-hook-budget-oct17/console-window-root-repair-oct22/handbook-rebuild/. This incremental visual review covers the changed section; the automated measurement covers the full existing inventory.

## Integrated Installer Review

Develop commit 7b0a09a0d also restricts the Copilot Usage Monitor to VS Code and removes older Cursor copies. The merged installers retain that behavior and the new process policy copy. The upstream [Copilot host review](copilot-monitor-vscode-only-handbook-review.md) remains intact. The handbook makes no claim about usage-monitor host selection, so this integration changes only code dependency hashes; its rendered output and all rendering inputs still match the measured 105c97b8d3f46b2c2b97211a84259f72e5ed478bfd3349f925a706eabd3e61d1 artifact.
