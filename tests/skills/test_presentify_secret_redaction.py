"""v4.13.11 AR-03: the presentify repository walk redacts secrets.

A walked repository is copied into a site the user may share, so a secret in a
walked file must never reach the content model. Every fake secret below is
assembled by concatenation, and every config line by joining a key and a value,
so the repository's own secret scanner does not see a literal token or a
literal credential assignment in this file.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_EXTRACTOR = (
    _ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "extract_content.py"
)

_AWS_ID = "AKIA" + "Z7QF3XW9" + "LM2KPR4T"
_AWS_KEY = "wJalr" + "XUtnFEMI/K7MDENG/bPxR" + "fiCYzz9q8v3a1b2c"
_GITHUB = "gh" + "p_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6q7R8s9T0"
_SLACK = "xo" + "xb-" + "1234567890-0987654321-" + "AbCdEfGhIjKlMnOp"
_OPENAI = "s" + "k-" + "proj-" + "Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"
_GOOGLE = "AI" + "za" + "SyD3f9K2mXq7Lp0Rt5Wv8Bn1Cz4Hj6Ge2Ab"
_DB_PASS = "Tr0ub" + "4dor-and-3"
_PEM_BODY = "MIIEow" + "IBAAKCAQEA7s9fakefakefakefake" + "QIDAQAB"
_BEGIN = "-----" + "BEGIN RSA PRIVATE KEY" + "-----"
_END = "-----" + "END RSA PRIVATE KEY" + "-----"
_ODD_BEGIN = "-----" + "BEGIN ENCRYPTED PRIVATE KEY" + "-----"
_ODD_BODY = "MIIFHz" + "BJBgkqhkiG9w0BBQ0wPDAbBgkqfake"

_SECRETS = [_AWS_ID, _AWS_KEY, _GITHUB, _SLACK, _OPENAI, _GOOGLE, _DB_PASS]

_YAML_LINES = [
    ("aws_access_key_id", _AWS_ID),
    ("aws_secret_access_key", _AWS_KEY),
    ("slack_webhook", _SLACK),
    ("openai", _OPENAI),
    ("maps", _GOOGLE),
    ("db_password", _DB_PASS),
    ("region", "eu-west-1"),
]


def _fixture_repo(root: Path) -> Path:
    repo = root / "demo-repo"
    (repo / "config").mkdir(parents=True)
    (repo / "README.md").write_text(
        "# Demo service\n\nDeploy with the CI credential " + _GITHUB + " today.\n",
        encoding="utf-8",
    )
    yaml_text = "".join(key + ": " + value + "\n" for key, value in _YAML_LINES)
    (repo / "config" / "secrets.yaml").write_text(yaml_text, encoding="utf-8")
    (repo / "config" / "deploy-key.txt").write_text(
        "Key follows\n" + _BEGIN + "\n" + _PEM_BODY + "\n" + _END + "\nafter the key\n",
        encoding="utf-8",
    )
    (repo / "config" / "odd.txt").write_text(
        "Unterminated block\n" + _ODD_BEGIN + "\n" + _ODD_BODY + "\n",
        encoding="utf-8",
    )
    (repo / "app.py").write_text(
        "import os\n\nAPI = os.environ.get('SERVICE_URL')\nREGION = 'eu-west-1'\n",
        encoding="utf-8",
    )
    return repo


def _run(tmp_path: Path, *inputs: Path) -> tuple[str, dict, str]:
    out = tmp_path / "model.json"
    proc = subprocess.run(
        [sys.executable, str(_EXTRACTOR), *map(str, inputs), "-o", str(out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    raw = out.read_text(encoding="utf-8")
    return raw, json.loads(raw), proc.stderr


@pytest.fixture()
def walked(tmp_path: Path) -> tuple[str, dict, str]:
    return _run(tmp_path, _fixture_repo(tmp_path))


def test_no_planted_secret_reaches_the_model_or_the_log(walked):
    raw, _model, stderr = walked
    for secret in [*_SECRETS, _PEM_BODY, _ODD_BODY]:
        assert secret not in raw
        assert secret not in stderr


@pytest.mark.parametrize(
    "category",
    [
        "aws-access-key",
        "aws-secret-key",
        "github-token",
        "slack-token",
        "api-key",
        "google-api-key",
        "credential-assignment",
        "private-key",
    ],
)
def test_each_category_leaves_a_marker(walked, category):
    raw, _model, _stderr = walked
    assert f"[REDACTED:{category}]" in raw


def test_an_unknown_pem_type_without_an_end_line_is_redacted_to_the_end(walked):
    raw, _model, _stderr = walked
    assert "ENCRYPTED PRIVATE KEY" not in raw
    assert "Unterminated block" in raw


def test_surrounding_text_and_ordinary_code_survive(walked):
    raw, _model, _stderr = walked
    assert "after the key" in raw
    assert "region: eu-west-1" in raw
    assert "os.environ.get('SERVICE_URL')" in raw


def test_coverage_reports_counts_not_values(walked):
    _raw, model, stderr = walked
    walk = model["coverage"]["walk"]
    assert walk["secrets_redacted"] == 9
    per = {
        c["path"]: c.get("secrets_redacted", {})
        for c in model["coverage"]["per_source"]
    }
    assert per["config/secrets.yaml"]["aws-access-key"] == 1
    assert per["README.md"] == {"github-token": 1}
    assert per["app.py"] == {}
    assert any("secrets redacted: config/secrets.yaml" in n for n in walk["notes"])
    assert "[REDACTED:<category>]" in stderr


_AWS_KEY_NAMES = [
    "aws_secret_access_key",
    "AWS_SECRET_ACCESS_KEY",
    "secret_access_key",
    "secretAccessKey",
    "SecretAccessKey",
    "awsSecretAccessKey",
    "secret-access-key",
    "aws-secret-access-key",
]


def _variant_secret(index: int) -> str:
    """A distinct 40-character AWS-secret-shaped value per key-name variant."""
    value = "wJalr" + "XUtnFEMI/K7MDENG/bPx" + "R" + "fiCYzz9q8v3a" + f"{index:02d}"
    assert len(value) == 40
    return value


def test_case_and_separator_variants_of_the_aws_secret_key_name(tmp_path):
    # Cycle 2 B1: STS JSON and camelCase YAML leaked the 40-character value.
    repo = tmp_path / "aws-variants"
    repo.mkdir()
    sts = {"AccessKeyId": _AWS_ID, "SecretAccessKey": _variant_secret(90)}
    (repo / "sts.json").write_text(json.dumps(sts, indent=2), encoding="utf-8")
    (repo / "serverless.yml").write_text(
        "provider:\n  secretAccessKey: " + _variant_secret(91) + "\n", encoding="utf-8"
    )
    lines = [
        name + " = " + _variant_secret(index) for index, name in enumerate(_AWS_KEY_NAMES)
    ]
    (repo / "credentials.ini").write_text("\n".join(lines) + "\n", encoding="utf-8")

    raw, model, stderr = _run(tmp_path, repo)

    secrets = [_variant_secret(i) for i in range(len(_AWS_KEY_NAMES))]
    for secret in [*secrets, _variant_secret(90), _variant_secret(91)]:
        assert secret not in raw
        assert secret not in stderr
    per = {
        c["path"]: c.get("secrets_redacted", {})
        for c in model["coverage"]["per_source"]
    }
    assert per["sts.json"].get("aws-secret-key") == 1
    assert per["serverless.yml"].get("aws-secret-key") == 1
    assert per["credentials.ini"].get("aws-secret-key") == len(_AWS_KEY_NAMES)
    # The key names themselves survive, so the model still reads as config.
    assert "SecretAccessKey" in raw and "secretAccessKey" in raw


def test_a_single_file_input_is_not_redacted(tmp_path):
    note = tmp_path / "aws-example.md"
    note.write_text(
        "# Key format\n\nAn id looks like " + _AWS_ID + ".\n", encoding="utf-8"
    )
    raw, model, _stderr = _run(tmp_path, note)
    assert _AWS_ID in raw
    assert "walk" not in model["coverage"]
