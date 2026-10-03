# Host-Agent Disk Writes

Summary: what to do about the reported Codex CLI disk-write problem: check your Codex version, update it, and, if you want to, measure your SSD's wear yourself with read-only tools.
Read this when: you use OpenAI Codex CLI and saw reports that it wears out SSDs, or you want a safe, read-only way to check how much your drive has written.
Covers: what was reported, what the widely shared command does and does not do, the fix version and how it was verified, checking and updating Codex, measuring SSD wear on macOS, Linux, and Windows, and what Nexus-Hub never does on your behalf.

## What was reported

In June 2026 several outlets reported that Codex CLI wrote very large amounts of log data to disk, enough to raise concern about SSD wear. These are secondary sources; they summarize user reports and do not speak for OpenAI:

- [Windows Report](https://windowsreport.com/openai-codex-cli-bug-may-wear-out-ssds-with-excessive-logging/)
- [Tech Times](https://www.techtimes.com/articles/318876/20260622/openai-codex-cli-bug-silently-writes-640-tb-year-your-ssd-no-patch.htm)
- [Codersera](https://codersera.com/blog/openai-codex-ssd-wear-bug-640tb-fix-2026/)

The outlets describe Codex keeping detailed logs in files under `~/.codex` named `logs_2.sqlite` and its companions. Their headline figure, about 640 TB per year, is an extrapolation from one heavy user's three weeks of writes, not a measurement of typical use. Treat it as a worst case, not as what your machine does.

## What the widely shared command does and does not do

A social-media post that circulated with these reports offered a `smartctl` command as "the fix". It is not a fix. It reads your drive's health counters (model, percentage used, data written, power-on hours, and overall health) and changes nothing. It also needs administrator rights and a separately installed tool, and its device name (`/dev/disk0`) only works on a Mac.

Reading those counters is still useful: it tells you whether your drive has actually been affected. The read-only steps are below.

## The fix version

The logging change shipped in **Codex CLI 0.142.0**. This is verified against two OpenAI primary sources that agree, checked on 2026-10-03:

- the [0.142.0 release notes](https://github.com/openai/codex/releases/tag/rust-v0.142.0), published 2026-06-22, which list a reduction in persistent-log churn from removing per-event WebSocket payload logging, citing pull requests #29432 and #29457;
- [pull request #29432](https://github.com/openai/codex/pull/29432), which stopped logging every Responses WebSocket event, merged on 2026-06-22, and whose merge commit falls between the `rust-v0.141.0` and `rust-v0.142.0` tags.

What is verified is that this change is in 0.142.0. How much it reduces writes on a given machine is not stated by OpenAI; the outlets' figures remain theirs.

## Check your Codex version

Run this in a terminal:

```bash
codex --version
```

Expected: a version number. If it is lower than 0.142.0, update.

## Update Codex

Update Codex the same way you installed it. With a package manager:

```bash
# Installed with npm
npm install -g @openai/codex@latest

# Installed with Homebrew
brew upgrade --cask codex
```

If you used OpenAI's standalone installer, download the current release from the [Codex releases page](https://github.com/openai/codex/releases) or follow the install section of the [Codex README](https://github.com/openai/codex#readme). This guide does not show a command that pipes a downloaded script straight into a shell, because that runs code you have not inspected.

Run `codex --version` again afterwards. Expected: 0.142.0 or later.

## Measure what Codex has written (optional, read-only)

These commands only read file sizes. Run them in your own terminal, not through an AI agent.

On macOS or Linux:

```bash
du -ch ~/.codex/logs_2.sqlite* 2>/dev/null | tail -n 1
```

On Windows (PowerShell):

```powershell
(Get-ChildItem "$HOME\.codex\logs_2.sqlite*" -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB
```

Expected: a total size. A large total on a version older than 0.142.0 is a reason to update. Deleting old log files is your decision, and only after Codex is closed.

## Measure your SSD's wear (optional, read-only)

Reading a drive's health counters needs administrator rights on every operating system. Open an administrator terminal yourself, run only the read command, and close it. Never ask an AI coding agent, Nexus-Hub, or any of its commands to run with administrator rights on your behalf; none of them needs it.

Get each tool only from its official source, and check the download before installing it:

- **smartmontools** (`smartctl`, for macOS, Linux, and Windows): the official [smartmontools releases on GitHub](https://github.com/smartmontools/smartmontools/releases). Each download has a matching `.asc` signature file; verify it with GnuPG against the project's published signing key before installing. On Linux, prefer your distribution's own package (for example `smartmontools`), which your package manager already verifies.
- **CrystalDiskInfo** (Windows): the official [Crystal Dew World page](https://crystalmark.info/en/software/crystaldiskinfo/). Crystal Dew World documents its [digital signature](https://crystalmark.info/en/information/digital-signature/); check that the installer is signed by the publisher it names before running it.

Then read the counters:

1. **macOS:** in an administrator terminal, list drives with `diskutil list`, then run `smartctl -a disk0` (replace `disk0` with your drive).
2. **Linux:** list drives with `smartctl --scan`, then run `smartctl -a /dev/nvme0` (replace it with a device from the scan) in a root shell you opened yourself.
3. **Windows:** open CrystalDiskInfo, or in an administrator terminal run `smartctl --scan` and then `smartctl -a` with a device it lists.

Look at **Percentage Used** (or Health Status) and **Data Units Written** (or Total Host Writes). A percentage used far below 100 means the drive has plenty of rated life left. Compare the written total with your drive's rated endurance (TBW) from its manufacturer's specification.

## What Nexus-Hub does and does not do

Nexus-Hub does not change Codex, delete Codex logs, or run anything with administrator rights. The files its own hooks write are measured and capped by a test, `catalog/hooks/tests/test_hook_size_bound.py`. This guide is documentation only: every step above is one you run yourself.
