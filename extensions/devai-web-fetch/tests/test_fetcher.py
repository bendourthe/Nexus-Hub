"""Tests for fetcher.py against the local HTTP fixture server."""
from __future__ import annotations

import pytest

from devai_web_fetch.fetcher import FetchError, fetch_url
from devai_web_fetch.ssrf_guard import GuardConfig


@pytest.fixture
def permissive_config() -> GuardConfig:
    """Allow private networks so tests can hit the local fixture server."""
    return GuardConfig(allow_private_networks=True)


async def test_readability_extraction(http_fixture: str, permissive_config: GuardConfig) -> None:
    result = await fetch_url(
        f"{http_fixture}/ok",
        extract_mode="readability",
        config=permissive_config,
    )
    assert result.status_code == 200
    # readability-lxml may not always populate a title in test-sized HTML;
    # body text should always include the article paragraph.
    assert "quick brown fox" in result.text
    assert result.raw_html is None


async def test_text_mode_returns_all_text(
    http_fixture: str, permissive_config: GuardConfig
) -> None:
    result = await fetch_url(
        f"{http_fixture}/ok",
        extract_mode="text",
        config=permissive_config,
    )
    assert "Sample Page" in result.title or "Sample Page" in result.text
    # Text mode returns full plain text including nav/footer.
    assert "Navigation" in result.text
    assert "copyright" in result.text


async def test_raw_mode_returns_html(
    http_fixture: str, permissive_config: GuardConfig
) -> None:
    result = await fetch_url(
        f"{http_fixture}/ok",
        extract_mode="raw",
        config=permissive_config,
    )
    assert result.raw_html is not None
    assert "<html>" in result.raw_html


async def test_404_raises(http_fixture: str, permissive_config: GuardConfig) -> None:
    with pytest.raises(FetchError, match="HTTP 404"):
        await fetch_url(f"{http_fixture}/404", config=permissive_config)


async def test_render_js_raises_not_implemented(
    http_fixture: str, permissive_config: GuardConfig
) -> None:
    with pytest.raises(NotImplementedError, match="v1.1.0"):
        await fetch_url(
            f"{http_fixture}/ok",
            render_js=True,
            config=permissive_config,
        )


async def test_file_scheme_blocked_end_to_end(permissive_config: GuardConfig) -> None:
    # Even with permissive_config allowing private networks, file:// is blocked.
    from devai_web_fetch.ssrf_guard import SSRFError

    with pytest.raises(SSRFError):
        await fetch_url("file:///etc/passwd", config=permissive_config)


async def test_unknown_extract_mode_raises(
    http_fixture: str, permissive_config: GuardConfig
) -> None:
    with pytest.raises(ValueError, match="Unknown extract_mode"):
        await fetch_url(
            f"{http_fixture}/ok",
            extract_mode="unknown",
            config=permissive_config,
        )
