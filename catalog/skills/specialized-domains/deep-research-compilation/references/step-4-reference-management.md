## Step 4: Reference Management

After ingesting, consolidate references across all inputs.

### Deduplication

Priority order:

1. **DOI** -- case-insensitive exact match.
2. **Normalized URL** -- lowercase host, strip `www.`, strip fragment, drop `utm_*` / `fbclid` / `gclid` / `ref*` query params, strip trailing slash.
3. **Title fuzzy match** -- `rapidfuzz.fuzz.token_set_ratio >= 85` on the first 80 chars of the entry text (lowercased, punctuation-stripped). Fallback to `difflib.SequenceMatcher.ratio()` if `rapidfuzz` is missing.

```python
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
TRACK = {"utm_source","utm_medium","utm_campaign","utm_term","utm_content","fbclid","gclid","ref","ref_src","ref_url"}
def norm_url(u):
    if not u: return None
    p = urlparse(u.strip())
    host = p.netloc.lower().removeprefix("www.")
    q = urlencode([(k,v) for k,v in parse_qsl(p.query) if k.lower() not in TRACK])
    return urlunparse(((p.scheme or "https").lower(), host, p.path.rstrip("/"), "", q, ""))
```

### Renumbering

Build `canonical: [{num, text, url, doi}]` (1-indexed) and `renumbering: {source_path: {local_num: canonical_num}}`. Then rewrite every `[N_local]` in every `content_md` to `[N_canonical]` using the per-source renumbering map.

For a paragraph that had `[1,3]` in source A and source B's `[1]` maps to canonical 4, the merged paragraph reads `[1,3,4]` (sorted, deduped).

### Present to the user

> Reference deduplication: 34 input references across 3 sources -> 28 canonical (6 duplicates collapsed). Proceed? [Y/edit]

Allow the user to challenge a specific collapse if they believe two cited works are actually distinct.

---
