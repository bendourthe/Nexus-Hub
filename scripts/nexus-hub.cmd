@echo off
rem nexus-hub launcher (Windows) -- v3.7.0 Phase 3.
rem
rem A thin shim installed on PATH at %USERPROFILE%\.nexus-hub\bin\nexus-hub.cmd.
rem It locates a Python interpreter and hands off to the CLI core at
rem %USERPROFILE%\.nexus-hub\scripts\nexus_hub_cli.py, which does all the real
rem work (--version, upgrade, ...). A .cmd (not a .ps1) is used so `nexus-hub`
rem runs as a bare command from both cmd.exe and PowerShell once the bin dir is
rem on PATH. Override the install root with NEXUS_HUB_HOME (used by the tests).
setlocal

if defined NEXUS_HUB_HOME (
    set "NEXUS_HOME=%NEXUS_HUB_HOME%"
) else (
    set "NEXUS_HOME=%USERPROFILE%\.nexus-hub"
)
set "CLI=%NEXUS_HOME%\scripts\nexus_hub_cli.py"

if not exist "%CLI%" (
    echo Error: nexus-hub CLI not found at "%CLI%" -- re-run the installer.>&2
    exit /b 1
)

set "PYTHON="
for %%P in (py python python3) do (
    if not defined PYTHON (
        where %%P >nul 2>nul && set "PYTHON=%%P"
    )
)

if not defined PYTHON (
    echo Error: Python 3 is required to run nexus-hub but was not found on PATH.>&2
    exit /b 1
)

"%PYTHON%" "%CLI%" %*
exit /b %errorlevel%
