# Prompt labels and context composer

Date: 2026-09-05

## Changes

- Rename Vague and Engineered to Vague Prompt and Engineered Prompt.
- Replace the context example's separate prompt/material boxes with one Engineered Prompt containing an attached image, an attached PDF, and a selected context folder above the message.
- Name api-traffic.png, load-test-report.pdf, and src/api/ in the prompt and explain why each is relevant. Keep the request/context highlights and legend.
- Match Context Engineering Best Practices to the section subtitle typography and update the budget comparison to reference the same selected material.

## Verification

- 143 tests passed, one skipped, and two inherited Python string-escape warnings. Coverage includes prompt structure, selected attachments, context budgets, Foundations layout, guide contracts, and file size. See [test output](tests.txt).
- [Layout checks](layout-checks.json) cover seven widths (320, 420, 560, 760, 761, 1024, 1440 pixels) in both themes: no page errors, horizontal overflow, or clipped attachment labels. Attachments precede the prompt and every displayed filename/folder is referenced.
- Best Practices and the section subtitle have matching computed size, weight, family, color, letter spacing, and line height at desktop width. Both use the same responsive fitting behavior.
- Inspected [desktop prompts](prompts-dark-1440.png), [desktop composer](context-dark-1440.png), and [mobile light-mode composer](context-light-420.png).
- [Content check](content-check.json) confirms unchanged content outside Prompt Engineering and Context Engineering, with all section order and IDs preserved.
- Final guide size: 397,497 normalized UTF-8 bytes. The only guide edit after the test run clarified a CSS comment; full repository CI was outside this focused correction.
