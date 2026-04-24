"""HTTP fetch + content extraction."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from readability import Document

from devai_web_fetch.ssrf_guard import GuardConfig, validate_url

logger = logging.getLogger("devai-web-fetch")

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
USER_AGENT = "devai-web-fetch/1.0 (+https://github.com)"


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
) -> FetchResult:
    """Fetch `url` and extract content per `extract_mode`.

    `render_js=True` is reserved for v1.1.0 and currently raises
    NotImplementedError. `extract_mode` is one of: readability, text, raw.
    """
    if render_js:
        raise NotImplementedError(
            "render_js=True is reserved for v1.1.0. devai-web-fetch v1.0.0 "
            "does not ship Playwright. Set render_js=False (the default) for "
            "static HTML extraction."
        )

    validate_url(url, config)

    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        try:
            response = await client.get(url)
        except httpx.TimeoutException as exc:
            raise FetchError(f"Request timed out after {timeout_seconds}s: {exc}") from exc
        except httpx.RequestError as exc:
            raise FetchError(f"Request failed: {exc}") from exc

    if len(response.content) > max_bytes:
        raise FetchError(
            f"Response size {len(response.content)} exceeds max_bytes={max_bytes}"
        )

    if response.status_code >= 400:
        raise FetchError(
            f"HTTP {response.status_code} from {url}: {response.reason_phrase or 'error'}"
        )

    content_type = response.headers.get("content-type", "")
    html = response.text

    title, text, raw_html = _extract(html, extract_mode)

    return FetchResult(
        url=url,
        final_url=str(response.url),
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
