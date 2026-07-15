# Doc-Header Summary Convention

Summary: how to front-load every durable system doc with a dense, greppable summary.
Read this when: writing or editing an architecture note, policy, reference guide, or runbook.
Covers: the header format, what counts as a system doc, and the self-healing rule.

Every Nexus-Hub SYSTEM doc (a doc that explains how a system, subsystem, workflow, or policy works - not a one-off report) should open with a dense, greppable summary in its first few lines, the same way a `SKILL.md` front-loads `summary_l0` and `overview_l1`. The goal: an agent or a person can `grep` the top of a doc and know in one read whether it is the right doc, without loading the whole file. The first three lines of this very guide are an example.

## The convention

- **First line**: an ATX `#` H1 title.
- **Next 3-7 lines**: a summary block stating, one continuous line each, (1) what the doc covers, (2) who reads it and when, and (3) the key topics or sections it contains. Plain text, no hard wrapping, greppable. A `Summary:` / `Read this when:` / `Covers:` prefix triple is a good default.
- Place the summary ABOVE the first `##` section so it is the first thing read and the first thing a `grep -A7` on the title returns.

## What counts as a system doc

Apply this to durable docs that explain a system: architecture notes, policy docs, reference guides, runbooks, and long design docs. Do NOT force it onto point-in-time artifacts (session histories, comparison reports, CHANGELOG, plans) - those carry their own front-matter or metadata conventions.

## Self-healing

When you change how a system behaves, update the doc that describes it in the same change - including its summary header when the change alters what the doc covers. A header that no longer matches the system is worse than no header, because it misleads a reader who trusted the greppable summary. The `documentation-consistency` skill audits system docs for header presence and for header-vs-system drift.
