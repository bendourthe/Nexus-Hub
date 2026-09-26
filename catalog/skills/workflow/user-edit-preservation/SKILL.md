---
name: user-edit-preservation
description: "Use whenever you are about to change, regenerate, re-save, copy over, rebuild, or re-publish any file you read or wrote earlier: decks, documents, spreadsheets, PDFs, generated HTML, handbooks, configs, source files, and copies on OneDrive, SharePoint, Dropbox, or shared drives. Trigger phrases: update the deck, revise the report, change slide N, regenerate the document, rebuild it, re-export, copy it to my OneDrive, save over it, refresh the handbook, apply these edits to my file. Fires even when you plan to rerun your own generator script, because a rerun overwrites whatever the user changed since. SKIP only for a file you are creating new in this step that did not exist before."
summary_l0: "Detect and carry forward user edits before changing any file you read or wrote earlier"
overview_l1: "This skill owns what an agent does before changing a file it read or wrote earlier. The user may have edited that file since, in an editor, in PowerPoint, or through a synced drive, and regenerating it from a script or copying a fresh build over it silently destroys their work. The skill drives the bundled edit_guard.py helper: record the file after every read and write, check it before every change, and on a detected change stop, show the diff, tell the user what changed, treat their file as the source of truth, carry their edits into the change, and list suggestions separately without applying them. It covers files the helper cannot compare (placeholders, non-text Office changes, unrecorded existing files), open files and conflict copies, and recovery when an edit was already lost. A block is released only through accept after the user agrees, and every accept appears in the end-of-task summary."
---

# User-Edit Preservation

A file you read or wrote earlier may have changed since: the user edited a slide, fixed a typo, or restructured a section, often in another application or through a synced drive. Regenerating it from your script, or copying a fresh build over it, destroys that work without anyone noticing until it is gone. This skill is the procedure that prevents it. The always-loaded rule in `## Autonomous Operation` says when it applies; this file says exactly what to do. The helper `scripts/edit_guard.py` does the detection, so you never have to judge from memory whether a file changed.

## When to Use This Skill

- Before editing, rewriting, regenerating, re-saving, or copying over any existing file you read or wrote earlier in this session or a previous one.
- Before rerunning a generator script whose output lands on an existing deliverable (a deck, report, spreadsheet, PDF, or generated HTML).
- Before copying a build to a user-facing location: OneDrive, SharePoint, Dropbox, a shared drive, or a folder the user opens directly.
- When a hook (`user-edit-guard`) blocks or warns about a write.

**When NOT to use:** a file you are creating in this step that did not exist before. Everything else, including "a quick fix", goes through the procedure.

## Instructions

The helper lives next to this file. Run it with the current session id when you have one:

```bash
python <this-skill>/scripts/edit_guard.py record <path> [--from read|write|command]
python <this-skill>/scripts/edit_guard.py check <path>
python <this-skill>/scripts/edit_guard.py diff <path>
python <this-skill>/scripts/edit_guard.py accept <path>
python <this-skill>/scripts/edit_guard.py log
```

Set `NEXUS_EDIT_GUARD_SESSION` (or pass `--session`) to one value for the whole session, so `accept` can tell your own `diff` apart from another session's.

1. **Record after every read and write.** After you read a file you may later change, run `record <path> --from read`. After you write one, run `record <path> --from write`. After a command you ran changed a tracked file (a generator script, a converter), run `record <path> --from command`. A `record --from read` that exits 3 means the file changed since you last recorded it: go to step 3 before anything else.
2. **Check before every change.** Immediately before editing, regenerating, saving, or copying onto an existing file, run `check <path>` and branch on its exit code:

    | Exit | Meaning | What to do |
    |---|---|---|
    | 0 | Unchanged since you last saw it | Make the change, then `record <path> --from write`. |
    | 3 | Changed, or open, or a conflict copy exists | Stop. Go to step 3, or step 5 for an open file or conflict copy. |
    | 4 | No record for an existing file | If you produced it (you still have your own copy, such as a generator's `out/deck.pptx`), run `diff <path> --against <your copy>` and report every difference in step 3's reply, non-text changes included. Otherwise treat it as user-owned: say you have no baseline and ask before changing it. |
    | 5 | Cannot verify (an online-only placeholder) | Go to step 4. Never download it to check, and never overwrite it. |
    | 2 | Error (missing, unreadable, a link, a corrupt archive) | Report the error; do not treat it as unchanged. |

3. **On a detected change (exit 3), stop and report before any write.** Run `diff <path>` and read all of it. Treat the user's current file as the source of truth: never restore your earlier version, and never regenerate it from your script unless that script already includes their changes. Then end your turn with this reply, all three parts, before writing anything:

    ```text
    What you changed: <each user edit, in plain words: which slide, paragraph, section, or cells, and what it now says>
    Suggestions (not applied): <typos, grammar, layout, clarity, or content issues in THEIR edits, one per line; or "None">
    Plan: <your requested change, applied on top of their current file with every edit kept>. Shall I go ahead?
    ```

    Write only after the user says yes: run `accept <path>`, make the change ON their current file (open and edit it, or merge their edits into your working copy), then `record <path> --from write`. Apply a suggestion only if they ask. `accept` works only after your `diff` of that exact content in this session.
4. **When the change cannot be compared** (exit 5, or `diff` reports "non-text change" or "no stored copy"): tell the user the file changed since you last saw it and that the difference cannot be shown as text. Ask them to describe the change, or review the file together. Never overwrite it on the assumption that nothing important changed.
5. **When the file is open or a conflict copy exists:** ask the user to save and close it, and to resolve the conflict copy (`name-MACHINE.ext`) themselves. Then run `check` again.
6. **If an edit was already lost:** say so plainly, point the user to the file's version history (OneDrive or SharePoint "Version history", or `git log` / `git show` for a tracked file), and never overwrite that file again without step 2. No tool here restores it for you.
7. **End-of-task summary:** run `log` and list every `accept` from this task under **Completed**, naming the file and what you carried forward.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I will just regenerate it from my script." | The script produces your old version. Rerunning it and copying the result over the user's file is exactly how their edits were lost in the incident this skill exists for. |
| "Their change was small." | Size is not yours to judge. A one-word fix, a moved picture, or a deleted slide is still their work, and you cannot see what it meant to them. |
| "The titles match, so nothing changed." | A moved picture, new speaker notes, or a layout change is invisible to a title or text comparison. Compare with `edit_guard.py` (`check`, or `diff --against` your own copy when there is no record), never with an ad-hoc script. |
| "The diff was empty." | An empty text diff with a changed fingerprint is a non-text change (a moved picture, a layout, a table, formatting). `diff` says so. Ask; never assume nothing changed. |
| "I have no record, so it must be mine." | Exit 4 on an existing file means you have no baseline, not that nobody touched it. Treat it as user-owned and ask. |
| "I will restore my version and re-apply their change." | Restoring your version discards everything you did not notice. Edit their current file instead. |
| "The hook did not fire, so it is fine." | Many platforms have no hooks, and a script's own save is invisible to them. This procedure is the protection there. |

## Verification

- [ ] `record` ran after each read and write of every file you later changed (`log` and the store show the records).
- [ ] `check` ran immediately before each change to an existing file, and its exit code was acted on as in the table.
- [ ] After any exit 3, `diff` output was shown to or summarized for the user, their changes are present in the final file, and suggestions were listed separately and not applied unasked.
- [ ] No `accept` ran before the user agreed; every `accept` is listed in the end-of-task summary.
- [ ] No file that returned exit 4 or 5 was overwritten without the user's explicit go-ahead.

## Related Skills

- `docx-generation`, `pptx-generation`, `xlsx-generation`, `pdf-document-generation`, `document-to-interactive-html`, `deep-research-compilation`: revise existing deliverables by editing the current file or merging from a working path, and defer to this skill's procedure first.
- `verification-before-completion`: the evidence rule for claiming the user's edits survived.
- `agent-access-policy`: which files an agent may touch at all; this skill governs how it changes a file it may touch.
