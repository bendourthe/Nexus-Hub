"""Regression tests for the manifest-driven cross-installer parity gate."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "check_installer_parity.py"


def _seed(root: Path) -> Path:
    scripts = root / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "tool.py").write_text("print('ok')\n", encoding="utf-8")
    (scripts / "a.sh").write_text(
        "alpha() { :; }\ninvoke_registry_platform x \"global\" \"\" \"alpha-platform\"\npython scripts/tool.py\n",
        encoding="utf-8",
    )
    (scripts / "b.ps1").write_text(
        'function Alpha { }\nInvoke-RegistryPlatform -IntegrationKey "alpha-platform"\npython scripts\\tool.py\n',
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "installers": [
            {
                "id": "a",
                "path": "scripts/a.sh",
                "function_pattern": r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\(\)\s*\{",
                "platform_pattern": r"(?m)^invoke_registry_platform[^\n]*\s\"([^\"]+)\"$",
                "script_reference_pattern": r"scripts[/\\]([A-Za-z0-9_-]+\.(?:py|js))",
            },
            {
                "id": "b",
                "path": "scripts/b.ps1",
                "function_pattern": r"(?im)^function\s+([A-Za-z0-9_-]+)\b",
                "platform_pattern": r"(?im)^Invoke-RegistryPlatform[^\n]*-IntegrationKey\s+\"([^\"]+)\"",
                "script_reference_pattern": r"scripts[/\\]([A-Za-z0-9_-]+\.(?:py|js))",
            },
        ],
        "platforms": ["alpha-platform"],
        "platform_exceptions": [],
        "script_artifact_exceptions": [],
        "function_groups": [{"a": ["alpha"], "b": ["Alpha"], "reason": "same fixture capability"}],
        "external_dependencies": [
            {
                "binary": "python",
                "installers": {
                    "a": {"fallback_markers": ["python"], "reason": "fixture fallback"},
                    "b": {"fallback_markers": ["python"], "reason": "fixture fallback"},
                },
            }
        ],
    }
    manifest_path = root / "parity.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _run(runner, root: Path, manifest: Path):
    return runner(SCRIPT, root, ["--manifest", str(manifest)])


def test_real_repository_is_in_installer_parity(runner) -> None:
    result = runner(SCRIPT, REPO_ROOT)
    assert result.returncode == 0, result.stderr


def test_script_artifact_asymmetry_exits_nonzero(tmp_path: Path, runner) -> None:
    manifest = _seed(tmp_path)
    path = tmp_path / "scripts" / "a.sh"
    path.write_text(path.read_text(encoding="utf-8") + "python scripts/extra.py\n", encoding="utf-8")
    result = _run(runner, tmp_path, manifest)
    assert result.returncode == 1
    assert "script-artifact" in result.stderr


def test_platform_asymmetry_exits_nonzero(tmp_path: Path, runner) -> None:
    manifest = _seed(tmp_path)
    path = tmp_path / "scripts" / "a.sh"
    path.write_text(path.read_text(encoding="utf-8") + 'invoke_registry_platform x "global" "" "beta-platform"\n', encoding="utf-8")
    result = _run(runner, tmp_path, manifest)
    assert result.returncode == 1
    assert "platform" in result.stderr


def test_function_asymmetry_exits_nonzero(tmp_path: Path, runner) -> None:
    manifest = _seed(tmp_path)
    path = tmp_path / "scripts" / "a.sh"
    path.write_text(path.read_text(encoding="utf-8") + "extra_only() { :; }\n", encoding="utf-8")
    result = _run(runner, tmp_path, manifest)
    assert result.returncode == 1
    assert "function" in result.stderr


def test_external_dependency_without_fallback_exits_nonzero(tmp_path: Path, runner) -> None:
    manifest = _seed(tmp_path)
    path = tmp_path / "scripts" / "a.sh"
    path.write_text(path.read_text(encoding="utf-8") + "npx package\n", encoding="utf-8")
    result = _run(runner, tmp_path, manifest)
    assert result.returncode == 1
    assert "external-dependency" in result.stderr
