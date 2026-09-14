# HTML Visual Self-Verification Rules

A task that produces or edits a rendered artifact is **not complete** until the agent has rendered it headless, captured the edited region, and inspected the capture.

A document is a visual artifact. Its correctness lives in rendered geometry, not in source text, so an agent that inspects only its own markup is checking the wrong thing.

## The loop

- **Render it. Look at it. Then say it is done.** Producing the edit is not evidence that the edit worked.
- **Never ask the user for a screenshot the agent can render itself.** A user pasting screenshots back is a symptom of a broken loop, not a workflow. In the source project nearly every correction traced to this one omission, and several took five or more rounds.
- **Verification reads COMPUTED DOM values, never re-read authored source.** Re-reading the file you just wrote confirms the file, not the render. `getComputedStyle`, `getBoundingClientRect` and `getScreenCTM` are the instruments; the stylesheet is not.

## Every programmatic edit asserts its anchor first

Before replacing text in a file, assert the anchor is **present and unique**.

A replacement that matches nothing does nothing and reports success. A replacement that matches twice corrupts the second site silently. Both look identical to a passing run.

## Capture rules

- **Clip the capture to the edited REGION**, not the whole page. A full-page capture of a long document resolves nothing at the size it arrives.
- **Cap near 1500px on the longest edge at device scale 1.** Oversized images are silently rejected by the image pipeline, which costs the agent its only feedback channel without producing an error to notice.

## Scope

Every HTML artifact this harness produces: documentation, `/presentify` output, `document-to-interactive-html` output, reports, guides, and any generated page.

## Related

- `responsive-layout.md` - the fluid-width rules the rendered check reads against.
- `[[verification-before-completion]]` - the general rule this specialises. Rendering evidence is what satisfies it for a visual artifact; "I made the edit" is not evidence.
- `[[document-to-interactive-html]]` - owns the measurement scripts that perform this loop (`measure_handbook.py`, `geometric_audit.py`).
