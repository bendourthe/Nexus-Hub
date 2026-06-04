---
description: DEPRECATED (removed in v4.0.0). Forwarding to /research report. Was: export Markdown to a templated .docx or .pptx report.
---

# /generate-report (deprecated)

`/generate-report` is deprecated and will be removed in v4.0.0. It now forwards to `/research report`.

This is a v3.x backward-compatibility shim. Behavior is unchanged: `/research report` delegates to the same retained `generate-report` skill that ran the original work. Update scripts, docs, and muscle memory to call `/research report` directly.

When invoked, first print this notice:

      /generate-report is deprecated and will be removed in v4.0.0. Forwarding to /research report.

then delegate to `/research report`, passing every argument through unchanged.
