#!/usr/bin/env python3
"""Browser-based viewer for one iteration of the skill-eval-loop.

Renders with_skill / without_skill outputs and optional raw_memory output, plus the
benchmark table from benchmark.json. Collects user feedback into a structured
feedback.json that the next iteration consumes.

Two modes:

    server (default): starts a local HTTP server, opens the user's browser,
                      and accepts a POST to /submit-feedback that writes
                      <iteration_dir>/feedback.json.

    static (--static <path>): writes a standalone HTML file at <path>. The
                              page includes a "Submit All Reviews" button
                              that downloads feedback.json as a Blob (no
                              network round-trip needed). Use this in
                              headless / CI environments.

Stdlib-only (http.server, html, json, webbrowser, argparse, pathlib).
No optional deps required; jinja-style templating is done with str.format.

Usage:
    python scripts/skill_eval_viewer.py <iteration_dir>
    python scripts/skill_eval_viewer.py <iteration_dir> --port 8765
    python scripts/skill_eval_viewer.py <iteration_dir> --static review.html
    python scripts/skill_eval_viewer.py <iteration_dir> --no-open

Schema reference:
    catalog/skills/workflow/skill-eval-loop/references/schemas.md
"""

from __future__ import annotations

import argparse
import html as _html
import json
import socketserver
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


_RUN_CONDITIONS = ("with_skill", "without_skill")
_OPTIONAL_RUN_CONDITION = "raw_memory"


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _read_json_safe(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def collect_iteration_data(iteration_dir: Path) -> dict[str, Any]:
    """Walk the iteration directory and gather every artifact the viewer renders."""
    eval_dirs = sorted(d for d in iteration_dir.iterdir() if d.is_dir() and d.name.startswith("eval-"))
    evals: list[dict[str, Any]] = []

    for eval_dir in eval_dirs:
        entry: dict[str, Any] = {"id": eval_dir.name}
        for cond in _RUN_CONDITIONS:
            run_dir = eval_dir / cond
            entry[cond] = {
                "response": _read_text_safe(run_dir / "outputs" / "response.txt"),
                "metadata": _read_json_safe(run_dir / "outputs" / "run_metadata.json") or {},
                "grading": _read_json_safe(run_dir / "grading.json") or {},
            }
        raw_memory_dir = eval_dir / _OPTIONAL_RUN_CONDITION
        if raw_memory_dir.is_dir():
            entry[_OPTIONAL_RUN_CONDITION] = {
                "response": _read_text_safe(raw_memory_dir / "outputs" / "response.txt"),
                "metadata": _read_json_safe(raw_memory_dir / "outputs" / "run_metadata.json") or {},
                "grading": _read_json_safe(raw_memory_dir / "grading.json") or {},
            }
        evals.append(entry)

    benchmark = _read_json_safe(iteration_dir / "benchmark.json") or {}
    return {
        "iteration_dir": str(iteration_dir.resolve()),
        "iteration_name": iteration_dir.name,
        "evals": evals,
        "benchmark": benchmark,
    }


# ── HTML rendering ────────────────────────────────────────────────────────────


def _esc(text: str) -> str:
    return _html.escape(text or "", quote=True)


def _render_path(text: str) -> str:
    """Escape a filesystem path and add safe wrap opportunities at separators."""
    return _esc(text).replace("\\", "\\<wbr>").replace("/", "/<wbr>")


def render_html(data: dict[str, Any], static_mode: bool) -> str:
    """Render the viewer page. `static_mode=True` swaps the submit endpoint
    for a JS Blob download instead of a POST to /submit-feedback."""
    n_evals = len(data["evals"])
    benchmark_table = _render_benchmark_table(data["benchmark"])
    eval_blocks = "\n".join(_render_eval_block(e) for e in data["evals"])

    submit_handler = _STATIC_SUBMIT_JS if static_mode else _SERVER_SUBMIT_JS

    return _PAGE_TEMPLATE.format(
        iteration_name=_esc(data["iteration_name"]),
        n_evals=n_evals,
        iteration_dir=_render_path(data["iteration_dir"]),
        iteration_dir_title=_esc(data["iteration_dir"]),
        benchmark_table=benchmark_table,
        eval_blocks=eval_blocks,
        submit_handler=submit_handler,
    )


def _render_benchmark_table(benchmark: dict[str, Any]) -> str:
    if not benchmark or "overall" not in benchmark:
        return "<p><em>benchmark.json not found - run scripts/aggregate_benchmark.py first.</em></p>"

    overall = benchmark["overall"]
    by_eval = benchmark.get("by_eval", {})
    rows = []
    rows.append(
        "<tr><td>Overall (mean across evals)</td>"
        f"<td>{overall['with_skill_pass_rate']:.3f}</td>"
        f"<td>{overall['without_skill_pass_rate']:.3f}</td>"
        f"<td>{overall['pass_rate_delta']:+.3f}</td>"
        f"<td>{overall['with_skill_duration_ms_mean']:.0f}</td>"
        f"<td>{overall['without_skill_duration_ms_mean']:.0f}</td></tr>"
    )
    for eval_id, ev in by_eval.items():
        rows.append(
            f"<tr><td>{_esc(eval_id)}</td>"
            f"<td>{ev['with_skill']['pass_rate']:.3f}</td>"
            f"<td>{ev['without_skill']['pass_rate']:.3f}</td>"
            f"<td>{ev['delta']['pass_rate']:+.3f}</td>"
            f"<td>{ev['with_skill']['duration_ms_mean']:.0f}</td>"
            f"<td>{ev['without_skill']['duration_ms_mean']:.0f}</td></tr>"
        )

    table = (
        "<table><thead><tr><th>Eval</th><th>with_skill pass</th>"
        "<th>without_skill pass</th><th>Delta</th>"
        "<th>with_skill ms</th><th>without_skill ms</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )
    raw_memory = overall.get(_OPTIONAL_RUN_CONDITION, "not_run")
    if raw_memory == "not_run":
        return table + "<p><strong>raw_memory:</strong> not_run</p>"
    if raw_memory.get("status") == "invalid":
        invalid = ", ".join(_esc(eval_id) for eval_id in raw_memory.get("invalid_evals", []))
        return table + f"<p><strong>raw_memory:</strong> invalid ({invalid})</p>"
    invalid_note = ""
    if raw_memory.get("invalid_evals"):
        invalid = ", ".join(_esc(eval_id) for eval_id in raw_memory["invalid_evals"])
        invalid_note = f"<p><strong>Invalid raw_memory evals:</strong> {invalid}</p>"
    return (
        table
        + "<h3>Raw memory arm</h3>"
        + f"<p><strong>Status:</strong> {_esc(raw_memory['status'])}</p>"
        + invalid_note
        + "<table><thead><tr><th>Evals run</th><th>Pass rate</th><th>Duration mean (ms)</th><th>Tokens mean</th></tr></thead>"
        + f"<tbody><tr><td>{raw_memory['n_evals']}</td><td>{raw_memory['pass_rate']:.3f}</td>"
        + f"<td>{raw_memory['duration_ms_mean']:.0f}</td><td>{raw_memory['tokens_mean']:.0f}</td></tr></tbody></table>"
    )


def _render_eval_block(entry: dict[str, Any]) -> str:
    eval_id = entry["id"]
    ws = entry["with_skill"]
    wos = entry["without_skill"]
    raw_memory = entry.get(_OPTIONAL_RUN_CONDITION)
    raw_memory_block = ""
    if raw_memory is not None:
        raw_memory_block = f"""
    <div class="run">
      <h4>raw_memory (prior notes)</h4>
      {_render_run_meta(raw_memory)}
      <pre class="response">{_esc(raw_memory['response']) or '<em>(no response.txt)</em>'}</pre>
      {_render_grading(raw_memory['grading'])}
    </div>"""

    return f"""
<section class="eval" data-eval-id="{_esc(eval_id)}">
  <h3>{_esc(eval_id)}</h3>
  <div class="grid">
    <div class="run">
      <h4>with_skill</h4>
      {_render_run_meta(ws)}
      <pre class="response">{_esc(ws['response']) or '<em>(no response.txt)</em>'}</pre>
      {_render_grading(ws['grading'])}
    </div>
    <div class="run">
      <h4>without_skill (baseline)</h4>
      {_render_run_meta(wos)}
      <pre class="response">{_esc(wos['response']) or '<em>(no response.txt)</em>'}</pre>
      {_render_grading(wos['grading'])}
    </div>
    {raw_memory_block}
  </div>
  <div class="feedback">
    <label><strong>Verdict:</strong>
      <select class="verdict" data-eval-id="{_esc(eval_id)}">
        <option value="">(unselected)</option>
        <option value="looks-right">looks-right</option>
        <option value="wrong-direction">wrong-direction</option>
        <option value="ambiguous">ambiguous</option>
      </select>
    </label>
    <label><strong>Notes:</strong>
      <textarea class="notes" data-eval-id="{_esc(eval_id)}" rows="2" cols="80"></textarea>
    </label>
  </div>
</section>
"""


def _render_run_meta(run: dict[str, Any]) -> str:
    md = run.get("metadata", {})
    if not md:
        return "<p class='meta'><em>(no run_metadata.json)</em></p>"
    parts = []
    if "duration_ms" in md:
        parts.append(f"duration: {md['duration_ms']:.0f} ms")
    if "total_tokens" in md:
        suffix = " (estimated)" if md.get("tokens_estimated") else ""
        parts.append(f"tokens: {md['total_tokens']}{suffix}")
    if "cli" in md:
        parts.append(f"cli: {_esc(md['cli'])}")
    if "exit_code" in md and md["exit_code"] != 0:
        parts.append(f"<strong>exit_code: {md['exit_code']}</strong>")
    return f"<p class='meta'>{' &middot; '.join(parts)}</p>"


def _render_grading(grading: dict[str, Any]) -> str:
    if not grading or "assertions" not in grading:
        return "<p class='grading'><em>(no grading.json)</em></p>"
    rows = []
    for a in grading["assertions"]:
        passed = a.get("passed", False)
        badge = "PASS" if passed else "FAIL"
        css = "pass" if passed else "fail"
        evidence = _esc(str(a.get("evidence", "")))
        text = _esc(str(a.get("text", "")))
        rows.append(
            f"<li class='{css}'><strong>{badge}</strong> {text}"
            f"<br><small>{evidence}</small></li>"
        )
    pr = grading.get("pass_rate", 0.0)
    return f"<ul class='grading'>{''.join(rows)}</ul><p>pass_rate: {pr:.2f}</p>"


_STATIC_SUBMIT_JS = """
function submitFeedback() {
  const blob = new Blob([JSON.stringify(collectReviews(), null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'feedback.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  setStatus('Downloaded feedback.json. Move it to the iteration directory.');
}
"""

_SERVER_SUBMIT_JS = """
function submitFeedback() {
  fetch('/submit-feedback', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(collectReviews())
  }).then(r => r.json()).then(j => {
    setStatus('Wrote ' + j.path);
  }).catch(e => setStatus('Error: ' + e));
}
"""

_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>skill-eval-loop viewer - {iteration_name}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       max-width: 1400px; margin: 1.5em auto; padding: 0 1.5em; line-height: 1.4;
       overflow-wrap: anywhere; }}
h1 {{ border-bottom: 2px solid #333; padding-bottom: 0.3em; }}
.tabs {{ display: flex; gap: 0.5em; margin: 1em 0; border-bottom: 1px solid #ccc; }}
.tab-btn {{ padding: 0.5em 1em; background: #eee; border: none; cursor: pointer; }}
.tab-btn.active {{ background: #333; color: white; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); gap: 1em; }}
.run {{ background: #fafafa; padding: 0.8em; border: 1px solid #ddd; border-radius: 4px; }}
.run h4 {{ margin-top: 0; }}
.response {{ background: white; padding: 0.6em; border: 1px solid #eee; max-height: 24em; overflow: auto;
             white-space: pre-wrap; word-wrap: break-word; font-size: 0.85em; }}
.meta {{ color: #666; font-size: 0.85em; margin: 0.3em 0; }}
.source-path {{ display: block; width: 100%; max-width: 100%; box-sizing: border-box; white-space: normal; overflow-wrap: anywhere; word-break: break-all; }}
.grading {{ list-style: none; padding-left: 0; margin: 0.5em 0; font-size: 0.85em; }}
.grading li {{ padding: 0.3em; margin: 0.2em 0; }}
.grading li.pass {{ background: #e8f5e9; }}
.grading li.fail {{ background: #ffebee; }}
.feedback {{ margin-top: 0.8em; padding: 0.5em; background: #fffde7; }}
.feedback label {{ display: block; margin: 0.4em 0; }}
.feedback textarea {{ width: 100%; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #ddd; padding: 0.4em; text-align: left; }}
th {{ background: #f5f5f5; }}
.eval {{ margin-bottom: 2em; padding-bottom: 1.5em; border-bottom: 1px dashed #ccc; }}
#status {{ position: fixed; bottom: 1em; right: 1em; padding: 0.6em 1em;
           background: #333; color: white; border-radius: 4px; display: none; }}
button.submit {{ padding: 0.6em 1.5em; font-size: 1em; background: #1976d2;
                 color: white; border: none; border-radius: 4px; cursor: pointer; }}
</style>
</head>
<body>
<h1>skill-eval-loop viewer</h1>
<p>Iteration: <strong>{iteration_name}</strong> &middot; Evals: {n_evals}</p>
<p>Source: <code class="source-path" title="{iteration_dir_title}">{iteration_dir}</code></p>
<div class="tabs">
  <button class="tab-btn active" data-tab="outputs">Outputs</button>
  <button class="tab-btn" data-tab="benchmark">Benchmark</button>
</div>
<div id="tab-outputs" class="tab-content active">
{eval_blocks}
<p><button class="submit" onclick="submitFeedback()">Submit All Reviews</button></p>
</div>
<div id="tab-benchmark" class="tab-content">
{benchmark_table}
</div>
<div id="status"></div>
<script>
function setStatus(msg) {{
  const el = document.getElementById('status');
  el.textContent = msg;
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 4000);
}}
function collectReviews() {{
  const reviews = {{}};
  document.querySelectorAll('.verdict').forEach(sel => {{
    const id = sel.dataset.evalId;
    const notes = document.querySelector('.notes[data-eval-id="' + id + '"]').value;
    reviews[id] = {{verdict: sel.value, notes: notes}};
  }});
  return {{
    iteration: '{iteration_name}',
    submitted_at: new Date().toISOString(),
    reviews: reviews
  }};
}}
{submit_handler}
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>
"""


# ── Server mode ───────────────────────────────────────────────────────────────


def _make_handler(html_body: str, iteration_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 - http.server convention
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_body.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):  # noqa: N802
            if self.path != "/submit-feedback":
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                return
            target = iteration_dir / "feedback.json"
            target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"path": str(target.resolve())}).encode("utf-8"))

        def log_message(self, fmt, *args):  # silence default access logs
            pass

    return Handler


def run_server(html_body: str, iteration_dir: Path, port: int, open_browser: bool) -> int:
    handler = _make_handler(html_body, iteration_dir)
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        actual_port = httpd.server_address[1]
        url = f"http://127.0.0.1:{actual_port}/"
        print(f"Viewer running at {url} (Ctrl+C to stop)")
        if open_browser:
            threading.Thread(
                target=lambda: (time.sleep(0.4), webbrowser.open(url)),
                daemon=True,
            ).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nViewer stopped.")
    return 0


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "iteration_dir",
        type=Path,
        help="Path to the iteration directory (e.g., my-skill-workspace/iteration-1)",
    )
    parser.add_argument("--port", type=int, default=0, help="Server port (default: random)")
    parser.add_argument(
        "--static",
        type=Path,
        default=None,
        help="Write a standalone HTML file at this path instead of starting a server",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="In server mode, do not open the browser automatically",
    )
    args = parser.parse_args()

    if not args.iteration_dir.is_dir():
        print(f"Error: iteration directory does not exist: {args.iteration_dir}", file=sys.stderr)
        return 1

    data = collect_iteration_data(args.iteration_dir)
    static_mode = args.static is not None
    html_body = render_html(data, static_mode=static_mode)

    if static_mode:
        args.static.parent.mkdir(parents=True, exist_ok=True)
        args.static.write_text(html_body, encoding="utf-8")
        print(f"Wrote static viewer to {args.static.resolve()}")
        print("Open the file in a browser; clicking 'Submit All Reviews' will download feedback.json.")
        return 0

    return run_server(
        html_body=html_body,
        iteration_dir=args.iteration_dir,
        port=args.port,
        open_browser=not args.no_open,
    )


if __name__ == "__main__":
    sys.exit(main())
