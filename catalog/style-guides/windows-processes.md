# Windows Process Launches

This policy covers console programs launched by agents, product commands, tests, fixtures, installers and builds on Windows. Read it before creating or changing a process launch, or investigating console windows that steal desktop focus. Both installers distribute this guide globally, including workspace-only installs.

## Launch Policy

Use one shared Python helper or default that passes creationflags=subprocess.CREATE_NO_WINDOW on Windows for every subprocess.run, Popen and check_* call. Load the same default in product entry points and every applicable pytest conftest.py. Preserve other compatible flags and output handling; reject CREATE_NEW_CONSOLE and DETACHED_PROCESS for console programs. Prefer an in-process call when it supplies the required behavior.

For Node and TypeScript, every child_process spawn, exec, execFile and related call passes windowsHide: true. Batch shims such as code.cmd, cursor.cmd and npm.cmd run through the same hidden-window helper; a bare shell call from a console-less parent can open a visible window. Preserve argument boundaries.

In PowerShell, prefer calling commands directly. A background Start-Process uses -WindowStyle Hidden. PowerShell cannot combine -WindowStyle with -NoNewWindow; when using ProcessStartInfo, set UseShellExecute to false and CreateNoWindow to true.

## Verification

Run the affected tests and the actual installer or build step in isolation while observing an idle desktop. Verify that no visible console window appears or steals focus. Use the installed console-window-guard hook to check launch sites before test, installer, build and helper commands. A deliberate exception places nexus: console-window-ok followed by a concrete reason in a comment on the launch line.

Protect the rule with regression coverage for new launch sites and for instruction links resolving to distributed files. Keep evidence of actual process behavior separate from static guard coverage. Stop a window-spawning run through an owned process handle; never stop other agents by matching process names or command lines.
