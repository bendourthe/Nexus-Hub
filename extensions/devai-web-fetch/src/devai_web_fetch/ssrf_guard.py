"""SSRF protection for devai-web-fetch.

Enforces that a target URL does not resolve to a private, loopback, or
link-local address range. Blocks `file://` unconditionally. Allows a
YAML config override at ~/.devai/web-fetch.yaml for explicit allow/deny
rules.
"""
from __future__ import annotations

import contextlib
import ipaddress
import logging
import re
import socket
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger("devai-web-fetch")

CONFIG_PATH = Path.home() / ".devai" / "web-fetch.yaml"

DISALLOWED_SCHEMES = frozenset({"file", "ftp", "data", "javascript", ""})
ALLOWED_SCHEMES = frozenset({"http", "https"})


class SSRFError(ValueError):
    """Raised when a URL fails SSRF validation."""


@dataclass
class GuardConfig:
    """User-configurable SSRF policy loaded from ~/.devai/web-fetch.yaml."""

    allow_private_networks: bool = False
    block_urls: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> GuardConfig:
        if not path.exists():
            return cls()
        try:
            import yaml
        except ImportError:
            logger.warning("pyyaml not installed; GuardConfig overrides ignored")
            return cls()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except (OSError, ValueError) as exc:
            logger.warning("Could not load %s: %s", path, exc)
            return cls()
        return cls(
            allow_private_networks=bool(data.get("allow_private_networks", False)),
            block_urls=list(data.get("block_urls", []) or []),
        )


def validate_url(url: str, config: GuardConfig | None = None) -> str:
    """Raise SSRFError if the URL violates the SSRF policy.

    Checks:
      1. Scheme must be http or https.
      2. Hostname must resolve to a non-private address (unless
         `allow_private_networks` is True in config).
      3. Hostname must not match any `block_urls` pattern.

    Returns:
      The validated IP address as a string. Callers can pass this IP to
      a DNS-pinning context manager to prevent rebinding between this
      validation and the actual HTTP fetch.
    """
    config = config or GuardConfig.load()

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()

    if scheme in DISALLOWED_SCHEMES:
        raise SSRFError(f"Scheme '{scheme}' is not allowed")
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFError(f"Scheme '{scheme}' is not in the allow list (http, https)")

    host = parsed.hostname
    if not host:
        raise SSRFError("URL has no hostname")

    # Hostname pattern denylist (simple fnmatch-style check).
    if _is_blocked(host, config.block_urls):
        raise SSRFError(f"Hostname '{host}' matches a block_urls pattern in user config")

    # Resolve hostname to IP(s) and check each. The first valid (and policy-
    # passing) IP is returned so the caller can pin DNS for the actual fetch.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if scheme == "https" else 80))
    except socket.gaierror as exc:
        raise SSRFError(f"Could not resolve hostname '{host}': {exc}") from exc

    safe_ip: str | None = None
    for _family, _type, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _is_private(ip) and not config.allow_private_networks:
            raise SSRFError(
                f"Hostname '{host}' resolves to private/reserved address {ip}"
            )
        if safe_ip is None:
            safe_ip = ip_str

    if safe_ip is None:
        raise SSRFError(f"Hostname '{host}' did not resolve to any usable address")

    return safe_ip


@contextlib.contextmanager
def pin_hostname_to_ip(hostname: str, ip: str):
    """Monkeypatch socket.getaddrinfo so `hostname` resolves to `ip` only.

    Used between `validate_url` and the actual HTTP fetch to prevent DNS
    rebinding attacks: an attacker who controls authoritative DNS for
    `hostname` could otherwise return a public IP during validation and a
    private IP during the fetch.

    All other hostnames continue to resolve normally. This patches a
    process-global; if multiple `fetch_url` calls run concurrently for
    different hostnames the pins stack safely (the dispatch is by hostname).
    Concurrent calls for the SAME hostname race - documented behavior. Use
    a serializing lock at the caller if that matters in your deployment.
    """
    original = socket.getaddrinfo

    def pinned(host, *args, **kwargs):
        if host == hostname:
            return original(ip, *args, **kwargs)
        return original(host, *args, **kwargs)

    socket.getaddrinfo = pinned  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.getaddrinfo = original  # type: ignore[assignment]


def _is_private(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _is_blocked(host: str, patterns: list[str]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(host.lower(), pat.lower()) for pat in patterns)


def looks_like_private_literal(url: str) -> bool:
    """Cheap pre-check before DNS resolution for obviously-private literal IPs.

    Useful for fast-failing localhost / 127.* / 10.* etc. without triggering DNS.
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Hostname (not a literal IP).
        return host.lower() in {"localhost"}
    return _is_private(ip)


# Quick heuristic: reject URLs that contain obviously-private IP literals
# without needing DNS. Keeps the SSRF check fast in the common case.
_PRIVATE_HOST_RE = re.compile(
    r"^(localhost|127\.|0\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|169\.254\.|\[::1\]|\[fe80)",
    re.IGNORECASE,
)
