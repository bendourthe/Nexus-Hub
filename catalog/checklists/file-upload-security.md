# File Upload Security Checklist

Checklist of defenses against file-upload-specific exploits. Use before shipping any endpoint that accepts user-supplied files (direct uploads, form attachments, profile avatars, CSV imports, archive extraction). Covers polyglot files, MIME confusion, archive path traversal, resource limits, and AV/re-encoding pipelines. Each item is a pass/fail gate - partial implementations are failures.

Companion skill: [catalog/skills/security/security-patch-advisor/SKILL.md](../skills/security/security-patch-advisor/SKILL.md) (Strategy 7: Path Traversal + Strategy 8: Insecure Deserialization for archive uploads).

---

## 1. File-type validation

- [ ] Validate MIME by **content sniffing** (read the first N bytes; compare against a magic-number table). Do NOT trust the client-supplied `Content-Type` header.
- [ ] Reject polyglot files - files that are valid in two formats (e.g., a JPG that is also valid HTML, or a PDF that contains executable JavaScript). At minimum, re-encode images through a trusted library that strips non-image content.
- [ ] Normalize file extensions server-side. Reject **double-extensions** (`file.jpg.php`, `image.png.html`) - strip trailing extensions iteratively until one matches the detected content type.
- [ ] Enforce an allowlist of accepted types per endpoint (e.g., avatars accept `image/png` and `image/jpeg` only; do not accept `image/svg+xml` because SVG can contain `<script>`).
- [ ] Reject files whose detected type does not match the endpoint's allowlist, regardless of extension or client-sent MIME.

## 2. Path handling

- [ ] Server generates storage filenames (UUID, content hash, or opaque token). Client-supplied filenames are used for display only, never for storage.
- [ ] For archive uploads (zip, tar, 7z): detect **path-traversal entries** (`../`, absolute paths, `..\` on Windows, UNC paths `\\server\share`) BEFORE extraction. Reject the entire archive on the first offending entry.
- [ ] Extract archives into a dedicated, isolated root directory. Use `chroot`, a container, or language-level sandboxing (e.g., Python `zipfile` with manual path normalization and `Path.resolve().is_relative_to(root)` check per entry).
- [ ] Normalize every extracted path with `resolve()` / `realpath()` and re-verify it stays within the intended root. Do this AFTER extraction as a belt-and-braces check, in addition to the pre-extraction scan.
- [ ] On Windows, also reject reserved device names (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) and names ending in `.` or space.

## 3. Size and resource limits

- [ ] Enforce a content-length limit at the reverse proxy / CDN AND at the application. Both layers must independently reject oversize payloads; do not rely on either alone.
- [ ] Enforce a per-user quota (total stored bytes, file count, or both) and reject uploads that would exceed it.
- [ ] Reject **zip-bomb** signatures:
  - Nested compression (archive containing archive containing archive, beyond 2 levels)
  - Extreme compression ratio (e.g., > 1000:1 uncompressed:compressed)
  - Declared uncompressed size that exceeds a hard cap (e.g., 1 GB)
  - Entry count exceeding a cap (e.g., 10k entries per archive)
- [ ] Cap decompression **wall-clock time** and memory. Kill extraction that exceeds either.
- [ ] For image re-encoding, impose max-dimensions and max-pixel-count before allocating a decoding buffer (prevents "pixel flood" attacks that allocate gigabytes of RAM from a small file).

## 4. Content scanning

- [ ] AV-scan every upload in a sandboxed pipeline before the file is made available for download or further processing. Run the AV engine in a short-lived container with no network access; delete the file on a positive result.
- [ ] Re-encode images through a trusted library (ImageMagick with delegates disabled, Pillow, libvips) to strip:
  - Embedded exploits (e.g., malformed JPEG segments, SVG `<script>`)
  - EXIF/metadata that may leak location or device info
  - Color profiles or ICC data not needed for display
- [ ] For PDF/Office documents, consider conversion to a neutral rendering (PDF -> image, DOCX -> HTML) before serving, especially if documents are displayed to third parties.
- [ ] For CSV/Excel imports (business-data path), validate the cell content against the target schema; reject formula-injection signatures (`=`, `+`, `-`, `@` at cell start) or prefix them with a single quote.

## 5. Storage and serving

- [ ] Store uploads **outside the web root**. A correctly-configured web server cannot list or serve them by URL; serving must go through an authenticated endpoint that validates ownership and permission.
- [ ] Serve user-uploaded non-image types with `Content-Disposition: attachment; filename="<safe-name>"` so browsers download rather than render them.
- [ ] Set `X-Content-Type-Options: nosniff` on download responses so browsers do not override the server-sent Content-Type based on content.
- [ ] Set `Content-Security-Policy` on any page that displays user-uploaded content to prevent XSS via SVG, HTML, or embedded scripts.
- [ ] Serve user uploads from a distinct origin (e.g., `user-content.example.com` vs `app.example.com`) so stored HTML or SVG runs in a sandboxed cross-origin context rather than alongside the application's session.
- [ ] Authenticated downloads: verify the downloading user has permission to access the specific file (IDOR defense). File UUID alone is not authorization.

---

## Related

- [security-patch-advisor](../skills/security/security-patch-advisor/SKILL.md) - patch patterns for path traversal (Strategy 7) and insecure deserialization (Strategy 8).
- [business-logic-abuse](../skills/security/business-logic-abuse/SKILL.md) - check-sequence abuse (Step 7) covers the pattern where validation is done on one input but action is taken on another (e.g., validate MIME but save with client-supplied filename).
- [advanced-attack-patterns](../skills/security/advanced-attack-patterns/SKILL.md) - cache poisoning (Step 2) covers CDN-level risks with uploaded content served from the application origin.
