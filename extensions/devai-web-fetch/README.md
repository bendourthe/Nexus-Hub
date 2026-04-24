# devai-web-fetch

DevAI-Hub local-only web-fetch MCP server. Fetches a single URL over HTTPS, extracts readable text from the HTML response, and returns it to the agent. No third-party intermediary - data destination is the URL itself.

**Policy compliance**: governed by the [MCP Registry Policy](../../AGENTS.md) in the repo root. Classified `re-full` in the [Reverse-Engineering Matrix](../../docs/v1.0.0/mcp-reverse-engineering-matrix.md) as the internal replacement for external web-scraping services that route fetches through their own infrastructure.

## Status

- **v1.0.0**: HTTPS fetch + `readability-lxml` main-content extraction. SSRF guard blocks RFC 1918 ranges, loopback, link-local, and `file://` by default. Single-URL scope.
- **v1.1.0 roadmap**: optional Playwright-based JS rendering for pages that require browser-side execution. Currently `render_js=True` raises `NotImplementedError`.

## Install

From the DevAI-Hub repo root:

```bash
pip install -e "extensions/devai-web-fetch[dev]"
```

The DevAI-Hub installer also installs this package into the shared MCP venv alongside `devai-skill-server` and `devai-code-search`.

## MCP tools

| Tool | Purpose |
|---|---|
| `fetch_url(url, render_js=False, extract_mode="readability")` | Fetch the URL, extract content per the mode, return title + text + optional raw HTML. |

## Extraction modes

| Mode | Behavior |
|---|---|
| `readability` | Use `readability-lxml` to extract the main article content. Best for blog posts, documentation pages, news articles. |
| `text` | Return the full plain-text rendering of the page (BeautifulSoup `get_text()`). |
| `raw` | Return the raw HTML unmodified. |

## SSRF safety

By default the fetcher rejects:

- `file://` URLs
- Non-HTTPS URLs that resolve to RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`, `fe80::/10`).

Users can override via a YAML config file at `~/.devai/web-fetch.yaml`:

```yaml
allow_private_networks: false  # keep False in regulated environments
block_urls:
  - "internal.example.com"
  - "*.corp.example.net"
```

Per-request limits: 30s connect + read timeout, 5 MB max response body size, no cookies, no auth headers.

## 5-question audit

Per the MCP Registry Policy:

1. **Who runs the process?** Python subprocess on the user's machine; spawned by the user's agent.
2. **Outbound calls?** HTTPS (and HTTP, allowed but discouraged) to the user-specified URL only. No intermediary service.
3. **API keys?** None.
4. **Data transmitted to third parties?** Only the URL itself (which by definition the user already intends to reach). No prompts, no source code, no query text beyond the URL.
5. **Vendor relationship required?** None.

## License

MIT. Copyright (c) Benjamin Dourthe / DevAI-Hub.
