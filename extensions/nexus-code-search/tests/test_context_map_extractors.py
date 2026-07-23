"""Unit tests for the Phase 2 context-map extractors.

Covers behavior-tag inference, route extraction (params + tags + handler),
env-var audit (required vs default + decoy rejection + env-example name-only),
middleware detection/categorization, and the v2 map sections + routes article.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.contextmap import generate_context_map
from nexus_code_search.contextmap.behavior import infer_behavior_tags
from nexus_code_search.contextmap.components import extract_components
from nexus_code_search.contextmap.env import audit_env_vars
from nexus_code_search.contextmap.events import detect_events
from nexus_code_search.contextmap.middleware import (
    categorize_middleware,
    detect_middleware,
)
from nexus_code_search.contextmap.routes import extract_routes
from nexus_code_search.contextmap.schema import extract_schema
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator


def _cfg() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


def _index_dir(root: Path) -> Path:
    return index_dir_for(root, _cfg())


@pytest.fixture
def webapp_repo(tmp_path: Path) -> Path:
    """An indexed repo with FastAPI + Express routes, env vars, and middleware."""
    (tmp_path / "api").mkdir()
    (tmp_path / "api" / "main.py").write_text(
        "import os\n"
        "from fastapi import FastAPI, Depends\n"
        "from fastapi.middleware.cors import CORSMiddleware\n"
        "app = FastAPI()\n"
        "app.add_middleware(CORSMiddleware)\n"
        "DB = os.environ['DATABASE_URL']\n"
        "PORT = os.getenv('PORT', 8000)\n"
        "NOPE = plain_dict['NOPE']\n\n"
        "@app.get('/items/{item_id}')\n"
        "def read_item(item_id: int):\n"
        "    return session.query(Item).get(item_id)\n\n"
        "@app.post('/pay')\n"
        "def pay(user=Depends(get_current_user)):\n"
        "    return stripe.checkout.session.create()\n",
        encoding="utf-8",
    )
    (tmp_path / "api" / "server.ts").write_text(
        "import express from 'express';\n"
        "const app = express();\n"
        "const KEY = process.env.API_KEY;\n"
        "app.use(cors());\n"
        "app.get('/ping', (req, res) => res.send('pong'));\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.example").write_text("EXTRA_TOKEN=x\n", encoding="utf-8")
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    return tmp_path


# --- behavior tags ----------------------------------------------------------


def test_behavior_tags_detects_known_signals() -> None:
    tags = infer_behavior_tags("x = session.query(User).all(); stripe.checkout.session")
    assert "db" in tags
    assert "payment" in tags


def test_behavior_tags_empty_and_plain() -> None:
    assert infer_behavior_tags("") == ()
    assert infer_behavior_tags("return {'ok': True}") == ()


def test_behavior_tags_ordered() -> None:
    tags = infer_behavior_tags("stripe.charge(); authenticate(user)")
    # Render order is fixed (auth before payment) regardless of source order.
    assert tags == ("auth", "payment")


# --- routes -----------------------------------------------------------------


def test_extract_routes_parses_method_path_params_tags(webapp_repo: Path) -> None:
    conn = open_database(_index_dir(webapp_repo))
    try:
        routes = extract_routes(conn, webapp_repo)
    finally:
        conn.close()
    by_path = {r.path: r for r in routes}
    assert set(by_path) >= {"/items/{item_id}", "/pay", "/ping"}
    assert by_path["/items/{item_id}"].method == "GET"
    assert by_path["/items/{item_id}"].params == ("item_id",)
    assert "db" in by_path["/items/{item_id}"].behavior_tags
    assert set(by_path["/pay"].behavior_tags) >= {"auth", "payment"}
    assert by_path["/ping"].behavior_tags == ()


# --- env --------------------------------------------------------------------


def test_env_audit_classifies_and_rejects_decoy(webapp_repo: Path) -> None:
    code_files = [
        (p, lang)
        for p, lang in open_database(_index_dir(webapp_repo)).execute(
            "SELECT path, language FROM files"
        )
    ]
    envs = {e.name: e for e in audit_env_vars(webapp_repo, code_files)}
    assert envs["DATABASE_URL"].required is True
    assert envs["PORT"].required is False
    assert envs["API_KEY"].required is True
    assert envs["EXTRA_TOKEN"].required is False  # from .env.example (name only)
    assert "NOPE" not in envs  # decoy dict access rejected


# --- middleware -------------------------------------------------------------


def test_detect_middleware_categorizes(webapp_repo: Path) -> None:
    code_files = [
        (p, lang)
        for p, lang in open_database(_index_dir(webapp_repo)).execute(
            "SELECT path, language FROM files"
        )
    ]
    mws = {m.name: m for m in detect_middleware(webapp_repo, code_files)}
    assert mws["cors"].category == "cors"
    assert mws["CORSMiddleware"].category == "cors"


def test_categorize_middleware_rules() -> None:
    assert categorize_middleware("rateLimit") == "rate-limit"
    assert categorize_middleware("AuthenticationMiddleware") == "auth"
    assert categorize_middleware("morgan") == "logging"
    assert categorize_middleware("CsrfViewMiddleware") == "validation"
    assert categorize_middleware("errorHandler") == "error-handling"
    assert categorize_middleware("somethingElse") == "other"


# --- v2 map -----------------------------------------------------------------


def test_map_has_routes_env_middleware_sections(webapp_repo: Path) -> None:
    generate_context_map(webapp_repo, _index_dir(webapp_repo))
    text = (webapp_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    for section in ("## Routes", "## Environment", "## Middleware"):
        assert section in text, f"missing {section}"
    assert "/items/{item_id}" in text
    assert "DATABASE_URL" in text
    assert "cors" in text


def test_routes_article_written_and_linked(webapp_repo: Path) -> None:
    generate_context_map(webapp_repo, _index_dir(webapp_repo))
    routes_article = webapp_repo / ".nexus" / "context" / "routes.md"
    assert routes_article.is_file()
    assert "/pay" in routes_article.read_text(encoding="utf-8")
    map_text = (webapp_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    assert "context/routes.md" in map_text


def test_env_example_change_invalidates_noop(webapp_repo: Path) -> None:
    first = generate_context_map(webapp_repo, _index_dir(webapp_repo))
    assert not first.skipped
    assert generate_context_map(webapp_repo, _index_dir(webapp_repo)).skipped

    (webapp_repo / ".env.example").write_text(
        "EXTRA_TOKEN=x\nANOTHER=y\n", encoding="utf-8"
    )
    second = generate_context_map(webapp_repo, _index_dir(webapp_repo))
    assert not second.skipped
    assert second.source_hash != first.source_hash


# --- Phase 3: schema / components / events ----------------------------------


@pytest.fixture
def data_repo(tmp_path: Path) -> Path:
    """An indexed repo with ORM models, a React component, and an event."""
    (tmp_path / "models.py").write_text(
        "from django.db import models\n\n"
        "class Author(models.Model):\n"
        "    name = models.CharField(max_length=100, unique=True)\n\n"
        "class Book(models.Model):\n"
        "    title = models.CharField(max_length=200)\n"
        "    author = models.ForeignKey(Author, on_delete=models.CASCADE)\n\n"
        "class PlainService:\n"
        "    def run(self):\n"
        "        return 1\n",
        encoding="utf-8",
    )
    (tmp_path / "schema.prisma").write_text(
        "model Account {\n  id Int @id\n  email String @unique\n}\n", encoding="utf-8"
    )
    (tmp_path / "ui.tsx").write_text(
        "interface P { title: string; }\n"
        "export function Panel({ title }: P) { return <div>{title}</div>; }\n",
        encoding="utf-8",
    )
    (tmp_path / "tasks.py").write_text(
        "from celery import shared_task\n\n@shared_task\ndef run_job(x):\n    return x\n",
        encoding="utf-8",
    )
    with ExtractionOrchestrator(tmp_path, _cfg(), _index_dir(tmp_path)) as orch:
        orch.run()
    return tmp_path


def test_extract_schema_fields_and_relations(data_repo: Path) -> None:
    conn = open_database(_index_dir(data_repo))
    try:
        models = extract_schema(conn, data_repo)
    finally:
        conn.close()
    by_name = {m.name: m for m in models}
    assert set(by_name) >= {"Author", "Book", "Account"}
    assert "PlainService" not in by_name  # non-model class rejected
    assert next(f for f in by_name["Author"].fields if f.name == "name").unique is True
    book_rel = {r.name: r for r in by_name["Book"].relations}
    assert book_rel["author"].target == "Author"
    assert book_rel["author"].kind == "many-to-one"
    account = by_name["Account"]
    assert account.framework == "prisma"
    assert next(f for f in account.fields if f.name == "id").primary_key is True


def test_extract_components(data_repo: Path) -> None:
    code_files = [
        (p, lang)
        for p, lang in open_database(_index_dir(data_repo)).execute(
            "SELECT path, language FROM files"
        )
    ]
    comps = {c.name: c for c in extract_components(data_repo, code_files)}
    assert "Panel" in comps
    assert comps["Panel"].props == ("title",)


def test_detect_events(data_repo: Path) -> None:
    code_files = [
        (p, lang)
        for p, lang in open_database(_index_dir(data_repo)).execute(
            "SELECT path, language FROM files"
        )
    ]
    events = {(e.name, e.kind) for e in detect_events(data_repo, code_files)}
    assert ("run_job", "celery-task") in events


def test_map_has_schema_components_events_sections(data_repo: Path) -> None:
    generate_context_map(data_repo, _index_dir(data_repo))
    text = (data_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    for section in ("## Data Models", "## Components", "## Events"):
        assert section in text, f"missing {section}"
    assert "Book" in text and "Panel" in text and "run_job" in text
    database_article = data_repo / ".nexus" / "context" / "database.md"
    assert database_article.is_file()
    assert "many-to-one" in database_article.read_text(encoding="utf-8")


def test_prisma_change_invalidates_noop(data_repo: Path) -> None:
    first = generate_context_map(data_repo, _index_dir(data_repo))
    assert not first.skipped
    assert generate_context_map(data_repo, _index_dir(data_repo)).skipped
    (data_repo / "schema.prisma").write_text(
        "model Account {\n  id Int @id\n  email String @unique\n  name String\n}\n",
        encoding="utf-8",
    )
    second = generate_context_map(data_repo, _index_dir(data_repo))
    assert not second.skipped
    assert second.source_hash != first.source_hash
