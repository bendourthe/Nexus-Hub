# Decision: The Windows upgrade runs a downloaded installer file, never irm | iex on a command line

Status: implemented - `nexus-hub upgrade` on Windows downloads `install.ps1` and runs the local copy with `powershell -File`.
Date: 2026-11-20
Author: Ben Dourthe
Template: Nygard

## Problem

On a second Windows machine, `nexus-hub upgrade` from 4.15.4 to 4.15.5 failed twice with `PermissionError: [WinError 5] Access is denied`, raised by `CreateProcess`. The upgrade started Windows PowerShell with this command line:

```
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

The machine's Microsoft Defender Operational log recorded event 1116 for that exact command line: `Trojan:Win32/Commando.B!ml`, severity Severe, detection type `FastPath`. Defender scores a new process's command line as it is created; the `!ml` suffix marks a machine-learning match. It refused the process, and Windows reported the refusal to Python as access denied.

The diagnosis ruled out the other suspects on that machine. The python.org interpreter and the Microsoft Store interpreter (which the launcher reaches through the CLI's `#!/usr/bin/env python3` line) both started PowerShell through the same shared-console helper. A command with the same download, the same `iex` and the same `-ExecutionPolicy Bypass`, in different text, also started. The block is specific to the download-and-run text on a new process's command line. A person typing the same pipe into an open PowerShell window starts no new process, so the documented manual install is not affected.

## Decision

- On Windows, `run_bootstrap` downloads `install.ps1` with the CLI's existing `fetch_text` helper into a new temporary folder. It then runs `powershell -NoProfile -ExecutionPolicy RemoteSigned -File <folder>\install.ps1`, followed by any recorded selector flags, and removes the folder afterward.
- The folder is new and empty, so `install.ps1` finds no `scripts\installer.ps1` beside itself and takes its standalone path, as it does under `irm | iex`.
- The file is written with a UTF-8 byte-order mark, because Windows PowerShell 5.1 reads a file without one in the ANSI code page.
- `RemoteSigned` replaces `Bypass`. The file was written by this process and carries no download mark, so `RemoteSigned` runs it. A machine policy set by Group Policy still overrides either value.
- A refused start (any `OSError`) and a failed download now print the one-line manual install command and exit 1, instead of a Python traceback.
- macOS and Linux keep `curl | bash`. Nothing showed a block there, and changing it without evidence would be a guess.

## Alternatives considered

- **Keep `irm | iex` and document a Defender exclusion.** Rejected: it asks every affected user to weaken their antivirus to run an upgrade, and the detection model can change at any signature update.
- **Pass the command with `-EncodedCommand`.** Rejected: encoding hides the text but is itself a common malware pattern that the same scoring weighs heavily, so it trades one detection for another.
- **Keep the scriptblock form (`&([scriptblock]::Create((irm ...)))`).** Rejected: it is still download-and-run text on a process command line, which is what the model flags; it only avoided the literal `| iex`.
- **Download in PowerShell, then run in a second PowerShell process.** Rejected: it needs the download step on a command line too. The CLI already has a downloader (curl, then wget, then urllib), so Python does the download and only a plain `-File` launch reaches the command line.

## Consequences

- No Nexus-Hub process starts PowerShell with download-and-run text on its command line. A regression test asserts that the Windows command contains neither `irm` nor `iex`.
- The installer is written to disk briefly. It lives in a per-run temporary folder and is removed when the installer exits, whatever the outcome.
- A future detection that flags `-File` launches from a temporary folder would surface as the same refused start. The CLI would then print the manual command instead of a traceback, so the user still has a working path.
- The upgrade now needs the installer download to succeed before PowerShell starts. A failure is reported with the manual command, and nothing is changed on disk.
