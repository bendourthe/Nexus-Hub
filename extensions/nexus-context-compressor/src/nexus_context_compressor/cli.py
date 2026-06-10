"""Command-line surface for the context-compression engine.

Three subcommands, all local and zero-outbound:

* ``compress`` -- read raw tool output on stdin, write the compressed text on
  stdout. This is what the PreToolUse compression hook pipes a command's output
  through (and what the Windows CLAUDE.md path invokes explicitly). It is
  **fail-open by design**: on any internal error it writes the *original* text
  back unchanged, so wiring the engine into a live session can never lose a
  command's output. Compression metrics go to stderr so they never pollute the
  stdout stream that flows into the model's context.
* ``retrieve`` -- resolve a ``<<ccr:HASH N_rows>>`` marker (or bare hash) back to
  the original dropped records, printed as JSON. Exit 1 (and a stderr note) on a
  miss, so a shell caller can branch on the status.
* ``serve`` -- launch the internal MCP server (requires the optional ``mcp``
  extra; prints an install hint and exits non-zero when it is absent).

The bare invocation (no subcommand) prints package identity and the active
token-counting mode, preserving the Phase 1 behavior of
``python -m nexus_context_compressor``.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, compress_output
from .ccr import NOT_FOUND, CCRStore, retrieve
from .tokens import count_tokens, using_accurate_counter
from .transforms.content_router import RouteResult


def compress_output_safe(text: str, *, persist: bool = True) -> RouteResult:
    """Compress ``text``, never raising; on failure return an identity result.

    The single fail-open core for the ``compress`` subcommand. The hook that
    pipes a command's output through the engine must never drop output just
    because compression hit an edge case, so any internal error yields a
    :class:`RouteResult` whose ``text`` is the input unchanged (and whose metrics
    report an identity transform).
    """
    try:
        return compress_output(text, persist=persist)
    except Exception:  # noqa: BLE001 - fail-open: never lose the user's output
        n = count_tokens(text) if text else 0
        return RouteResult(text=text, segments=[], tokens_before=n, tokens_after=n)


def run_compress(text: str, *, persist: bool = True) -> str:
    """Compress ``text`` and return the compressed string (original on failure)."""
    return compress_output_safe(text, persist=persist).text


def run_retrieve(marker: str) -> tuple[bool, str]:
    """Resolve a CCR marker to its originals.

    Returns ``(found, payload)``: ``(True, json)`` on a hit, ``(False, "")`` on a
    miss or any store error. Never raises -- a miss is the documented outcome.
    """
    try:
        with CCRStore() as store:
            original = retrieve(marker, store=store)
    except Exception:  # noqa: BLE001 - a store error is a miss, not a crash
        return False, ""
    if original is NOT_FOUND:
        return False, ""
    return True, json.dumps(original, ensure_ascii=False, indent=2)


def _cmd_compress(args: argparse.Namespace) -> int:
    result = compress_output_safe(sys.stdin.read(), persist=not args.no_persist)
    sys.stdout.write(result.text)
    if result.tokens_before:
        sys.stderr.write(
            f"[nexus-context-compressor] {result.tokens_before} -> "
            f"{result.tokens_after} tokens (ratio {result.ratio:.3f})\n"
        )
    return 0


def _cmd_retrieve(args: argparse.Namespace) -> int:
    found, payload = run_retrieve(args.marker)
    if found:
        print(payload)
        return 0
    print(
        f"[nexus-context-compressor] not found: {args.marker!r} "
        "(span evicted or marker unrecognized)",
        file=sys.stderr,
    )
    return 1


def _cmd_serve(_args: argparse.Namespace) -> int:
    try:
        from .server import serve_blocking
    except ImportError:
        print(
            "Error: the internal MCP server requires the optional 'mcp' extra.\n"
            "Install it with: pip install 'nexus-context-compressor[mcp]'",
            file=sys.stderr,
        )
        return 1
    return serve_blocking()


def _print_identity() -> int:
    mode = "tiktoken" if using_accurate_counter() else "stdlib-fallback"
    print(f"nexus-context-compressor {__version__} (token counter: {mode})")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Dispatch the CLI. ``argv`` defaults to ``sys.argv[1:]``."""
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="nexus_context_compressor",
        description="Local-first context-compression engine (zero outbound).",
    )
    sub = parser.add_subparsers(dest="command")

    p_compress = sub.add_parser(
        "compress", help="compress raw tool output read from stdin (stdout = compressed)"
    )
    p_compress.add_argument(
        "--no-persist",
        action="store_true",
        help="do not write dropped spans to the CCR store (pure compression)",
    )
    p_compress.set_defaults(func=_cmd_compress)

    p_retrieve = sub.add_parser(
        "retrieve", help="resolve a CCR marker (or hash) back to its originals"
    )
    p_retrieve.add_argument("marker", help="a <<ccr:HASH N_rows>> marker or bare hash")
    p_retrieve.set_defaults(func=_cmd_retrieve)

    p_serve = sub.add_parser("serve", help="launch the internal MCP server (needs the 'mcp' extra)")
    p_serve.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    if getattr(args, "func", None) is None:
        return _print_identity()
    return args.func(args)
