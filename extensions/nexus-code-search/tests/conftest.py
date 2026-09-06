"""Shared pytest fixtures for nexus-code-search tests."""
from __future__ import annotations

import os
import socket
from pathlib import Path

import pytest

if os.environ.get("NEXUS_CODE_SEARCH_BLOCK_NETWORK") == "1":
    _original_connect = socket.socket.connect
    _original_connect_ex = socket.socket.connect_ex
    _original_sendto = socket.socket.sendto
    _original_create_connection = socket.create_connection
    _loopback_hosts = frozenset({"127.0.0.1", "::1", "localhost"})

    def _is_loopback(address: object) -> bool:
        return isinstance(address, tuple) and str(address[0]).lower() in _loopback_hosts

    def _guard_connect(sock: socket.socket, address: object) -> None:
        if _is_loopback(address):
            _original_connect(sock, address)
            return
        raise RuntimeError("network egress blocked by nexus-code-search test guard")

    def _guard_connect_ex(sock: socket.socket, address: object) -> int:
        if _is_loopback(address):
            return _original_connect_ex(sock, address)
        raise RuntimeError("network egress blocked by nexus-code-search test guard")

    def _guard_sendto(sock: socket.socket, data: bytes, *args: object) -> int:
        address = args[-1] if args else None
        if _is_loopback(address):
            return _original_sendto(sock, data, *args)
        raise RuntimeError("network egress blocked by nexus-code-search test guard")

    def _guard_create_connection(address: object, *args: object, **kwargs: object) -> socket.socket:
        if _is_loopback(address):
            return _original_create_connection(address, *args, **kwargs)
        raise RuntimeError("network egress blocked by nexus-code-search test guard")

    socket.socket.connect = _guard_connect
    socket.socket.connect_ex = _guard_connect_ex
    socket.socket.sendto = _guard_sendto
    socket.create_connection = _guard_create_connection

from nexus_code_search.config import CodeSearchConfig


@pytest.fixture
def default_config() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


@pytest.fixture
def sample_tree(tmp_path: Path) -> Path:
    """Create a small fixture tree with Python + TS + markdown files."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def compute_total(items):\n"
        "    return sum(items)\n"
        "\n"
        "\n"
        "class Calculator:\n"
        "    def add(self, a, b):\n"
        "        return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "utils.ts").write_text(
        "export function greet(name: string) {\n"
        "  return `Hello, ${name}`;\n"
        "}\n"
        "\n"
        "export class UserService {\n"
        "  findUser(id: number) { return null; }\n"
        "}\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "# Sample Project\n\nThis is a test fixture for nexus-code-search.\n",
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
    # Decoy file that should be ignored via .gitignore
    (tmp_path / "debug.log").write_text("noise\n", encoding="utf-8")
    # Decoy directory that should be skipped via default-exclude
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lodash.js").write_text("// huge vendored lib", encoding="utf-8")
    # Binary file that should be skipped
    (tmp_path / "src" / "icon.bin").write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd\xfc")
    return tmp_path
