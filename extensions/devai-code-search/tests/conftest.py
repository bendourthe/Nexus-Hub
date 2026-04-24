"""Shared pytest fixtures for devai-code-search tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from devai_code_search.config import CodeSearchConfig


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
        "# Sample Project\n\nThis is a test fixture for devai-code-search.\n",
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
