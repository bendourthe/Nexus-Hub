## Step 6: Markdown Output

If the user requested `.md` (alone or with other formats), author it directly with the Write tool at `<final_dir>/<ReportTitle>.md` -- no Python needed. Read the intermediate synthesis from `<cache_dir>/merged.md` and transform it by prepending the title heading, inserting the manual TOC, wrapping each `[N]` as `<sup>[[N]](#refN)</sup>`, and emitting the References section with anchor targets.

Structure:

```markdown
# <Title>

*<Subtitle>*

*<Date>*

---

## Document's Purpose

<prose paragraph>

|  |  |
| --- | --- |
| **Authors** | <Author> |
| **Last Updated** | <Date> |

## Table of Contents

1. [Executive Summary](#executive-summary)
   1.1. [Topic A](#topic-a)
   1.2. [Topic B](#topic-b)
2. [Body Section 1](#body-section-1)
   ...

## Executive Summary

<prose> <sup>[[1](#ref1),[2](#ref2)]</sup>.

...

## References

<a id="ref1"></a>**[1]** Author. "Title." Venue, Date. [https://example.com](https://example.com)

<a id="ref2"></a>**[2]** ...
```

Slug rules for TOC anchors: lowercase, non-word chars -> space, spaces -> `-`, collapse runs, strip leading/trailing `-`. GitHub-compatible.

Citation rendering: replace every `[N]` in the body with `<sup>[[N]](#refN)</sup>`. Multi-citations `[N,M]` become `<sup>[[N](#refN),[M](#refM)]</sup>`.

---
