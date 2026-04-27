"""HTTP fetch + content extraction.

Two SSRF defenses are layered:

1. **Per-hop validation** - every URL (including each redirect target) is
   passed through `ssrf_guard.validate_url` before any network call.
   `follow_redirects=True` would skip the SSRF guard on `Location` targets,
   so this module sets `follow_redirects=False` and follows redirects
   manually with re-validation between each step.
2. **DNS pinning** - between validation and fetch, `pin_hostname_to_ip`
   monkeypatches `socket.getaddrinfo` so the hostname resolves only to the
   IP that passed validation. Without this pin, an attacker who controls
   authoritative DNS for the hostname could rebind to a private IP between
   the validate-time resolution and the connect-time resolution (classic
   DNS rebinding TOCTOU).

These two defenses together address the two SSRF findings from the v1.0.0
security review.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document

from devai_web_fetch.ssrf_guard import (
    GuardConfig,
    SSRFError,
    pin_hostname_to_ip,
    validate_url,
)

logger = logging.getLogger("devai-web-fetch")

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_MAX_REDIRECTS = 5
USER_AGENT = "devai-web-fetch/1.0 (+https://github.com)"
REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True)
class FetchResult:
    """Successful fetch + extraction result."""

    url: str
    final_url: str
    status_code: int
    title: str
    text: str
    content_type: str
    raw_html: str | None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "title": self.title,
            "text": self.text,
            "content_type": self.content_type,
            "raw_html": self.raw_html,
        }


class FetchError(RuntimeError):
    """Raised when a fetch fails (network, timeout, size, SSRF, etc.)."""


async def fetch_url(
    url: str,
    render_js: bool = False,
    extract_mode: str = "readability",
    config: GuardConfig | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_redirects: int = DEFAULT_MAX_REDIRECTS,
) -> FetchResult:
    """Fetch `url` and extract content per `extract_mode`.

    Redirects are followed manually so each `Location` target is re-validated
    by the SSRF guard. DNS is pinned per-hop to prevent rebinding.

    `render_js=True` is reserved for v1.1.0 and currently raises
    NotImplementedError. `extract_mode` is one of: readability, text, raw.
    """
    if render_js:
        raise NotImplementedError(
            "render_js=True is reserved for v1.1.0. devai-web-fetch v1.0.0 "
            "does not ship Playwright. Set render_js=False (the default) for "
            "static HTML extraction."
        )

    config = config or GuardConfig.load()
    requested_url = url
    current_url = url
    response: httpx.Response | None = None

    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=False,  # we re-validate each hop ourselves
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for hop in range(max_redirects + 1):
            # Per-hop SSRF validation - same gate runs on every redirect target.
            safe_ip = validate_url(current_url, config)
            current_host = urlparse(current_url).hostname or ""

            # DNS pin: between validate and fetch, force the hostname to
            # resolve only to the IP that just passed validation. Defends
            # against DNS rebinding TOCTOU.
            with pin_hostname_to_ip(current_host, safe_ip):
                try:
                    response = await client.get(current_url)
                except httpx.TimeoutException as exc:
                    raise FetchError(
                        f"Request timed out after {timeout_seconds}s: {exc}"
                    ) from exc
                except httpx.RequestError as exc:
                    raise FetchError(f"Request failed: {exc}") from exc

            if response.status_code in REDIRECT_STATUS_CODES:
                location = response.headers.get("location")
                if not location:
                    raise FetchError(
                        f"HTTP {response.status_code} from {current_url} but no Location header"
                    )
                # Resolve relative redirects against the current URL.
                next_url = urljoin(current_url, location)
                logger.debug(
                    "redirect hop %d: %s -> %s (status=%s)",
                    hop,
                    current_url,
                    next_url,
                    response.status_code,
                )
                current_url = next_url
                continue

            # Non-redirect response: this is the final hop.
            break
        else:
            # Loop exhausted max_redirects without a non-3xx response.
            raise FetchError(
                f"Exceeded max_redirects={max_redirects} starting from {requested_url}"
            )

    assert response is not None  # loop guarantees we reached the break

    if len(response.content) > max_bytes:
        raise FetchError(
            f"Response size {len(response.content)} exceeds max_bytes={max_bytes}"
        )

    if response.status_code >= 400:
        raise FetchError(
            f"HTTP {response.status_code} from {current_url}: {response.reason_phrase or 'error'}"
        )

    content_type = response.headers.get("content-type", "")
    html = response.text

    title, text, raw_html = _extract(html, extract_mode)

    return FetchResult(
        url=requested_url,
        final_url=current_url,
        status_code=response.status_code,
        title=title,
        text=text,
        content_type=content_type,
        raw_html=raw_html,
    )


def _extract(html: str, mode: str) -> tuple[str, str, str | None]:
    """Extract (title, text, optional raw_html) per the mode."""
    if mode == "raw":
        title = _extract_title_with_bs4(html)
        return title, "", html

    if mode == "text":
        soup = BeautifulSoup(html, "lxml")
        title = (soup.title.string.strip() if soup.title and soup.title.string else "")
        text = soup.get_text(separator="\n", strip=True)
        return title, text, None

    if mode == "readability":
        try:
            doc = Document(html)
            title = doc.short_title() or ""
            summary_html = doc.summary()
            soup = BeautifulSoup(summary_html, "lxml")
            text = soup.get_text(separator="\n", strip=True)
            return title, text, None
        except Exception:  # noqa: BLE001
            logger.debug("readability extraction failed; falling back to text mode")
            return _extract(html, "text")

    raise ValueError(f"Unknown extract_mode: {mode!r}. Expected one of: readability, text, raw.")


def _extract_title_with_bs4(html: str) -> str:
    try:
        soup = BeautifulSoup(html, "lxml")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
    except Exception:  # noqa: BLE001
        pass
    return ""
