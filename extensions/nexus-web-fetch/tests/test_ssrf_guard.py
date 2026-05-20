"""Tests for the SSRF guard."""
from __future__ import annotations

import pytest

from nexus_web_fetch.ssrf_guard import GuardConfig, SSRFError, validate_url


def test_file_scheme_blocked() -> None:
    with pytest.raises(SSRFError, match="not allowed|not in the allow list"):
        validate_url("file:///etc/passwd")


def test_ftp_scheme_blocked() -> None:
    with pytest.raises(SSRFError, match="not allowed|not in the allow list"):
        validate_url("ftp://example.com/file")


def test_localhost_blocked_by_default() -> None:
    with pytest.raises(SSRFError, match="private|reserved"):
        validate_url("http://127.0.0.1/")


def test_private_10_blocked() -> None:
    with pytest.raises(SSRFError, match="private|reserved"):
        validate_url("http://10.0.0.1/")


def test_private_192_168_blocked() -> None:
    with pytest.raises(SSRFError, match="private|reserved"):
        validate_url("http://192.168.1.1/")


def test_private_172_16_blocked() -> None:
    with pytest.raises(SSRFError, match="private|reserved"):
        validate_url("http://172.16.0.1/")


def test_link_local_blocked() -> None:
    with pytest.raises(SSRFError, match="private|reserved"):
        validate_url("http://169.254.169.254/")


def test_allow_override_for_tests() -> None:
    """When allow_private_networks=True, local HTTP fixture servers are reachable."""
    cfg = GuardConfig(allow_private_networks=True)
    # Should not raise.
    validate_url("http://127.0.0.1:8080/", cfg)


def test_blocklist_matches_hostname() -> None:
    cfg = GuardConfig(allow_private_networks=True, block_urls=["internal.example.com"])
    with pytest.raises(SSRFError, match="block_urls pattern"):
        validate_url("http://internal.example.com/", cfg)


def test_url_without_host_rejected() -> None:
    with pytest.raises(SSRFError):
        validate_url("http://")
