"""Framework-aware route extractors.

These resolvers run AFTER the per-language AST extraction completes for any
file matched by the per-framework predicate (urls.py, decorated FastAPI/Flask
handlers, Express call sites). Each resolver returns extra `(nodes, edges)`
the orchestrator merges into the per-file output before flushing to SQLite.

Local-only by policy: no network calls, no model downloads, no telemetry.

Public surface:
    FrameworkResolver        Abstract base class.
    DjangoFrameworkResolver  Detects path() / re_path() / url() / include().
    FastAPIFrameworkResolver Detects @app.get / @router.post decorators.
    ExpressFrameworkResolver Detects app.get() / router.post() calls.
    FRAMEWORK_RESOLVERS      All registered resolvers in evaluation order.
"""

from __future__ import annotations

from nexus_code_search.frameworks.base import ContextProvider, FrameworkResolver
from nexus_code_search.frameworks.django import DjangoFrameworkResolver
from nexus_code_search.frameworks.express import ExpressFrameworkResolver
from nexus_code_search.frameworks.fastapi import FastAPIFrameworkResolver
from nexus_code_search.frameworks.markdown import MarkdownContextProvider

FRAMEWORK_RESOLVERS: list[FrameworkResolver] = [
    DjangoFrameworkResolver(),
    FastAPIFrameworkResolver(),
    ExpressFrameworkResolver(),
]

CONTEXT_PROVIDERS: list[ContextProvider] = [MarkdownContextProvider()]

__all__ = [
    "CONTEXT_PROVIDERS",
    "FRAMEWORK_RESOLVERS",
    "ContextProvider",
    "DjangoFrameworkResolver",
    "ExpressFrameworkResolver",
    "FastAPIFrameworkResolver",
    "FrameworkResolver",
    "MarkdownContextProvider",
]
