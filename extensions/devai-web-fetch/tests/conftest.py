"""Shared pytest fixtures: local HTTP fixture server so tests never touch the internet."""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator

import pytest

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Sample Page</title></head>
<body>
<header><nav>Navigation</nav></header>
<main>
  <article>
    <h1>Headline</h1>
    <p>The quick brown fox jumps over the lazy dog.</p>
    <p>This is a sample article used as a fixture for devai-web-fetch tests.</p>
  </article>
</main>
<footer>copyright</footer>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 (std API naming)
        if self.path == "/ok":
            body = SAMPLE_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/404":
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"missing")
        elif self.path == "/redirect-to-ok":
            # Single-hop relative redirect to /ok (legitimate, should succeed).
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif self.path == "/redirect-to-private":
            # Attempts to redirect to a private RFC 1918 address. The SSRF
            # guard MUST reject this hop. Use a literal IP so DNS doesn't
            # mask the attack at validate time.
            self.send_response(302)
            self.send_header("Location", "http://10.0.0.1/internal")
            self.end_headers()
        elif self.path == "/redirect-to-loopback":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:1/admin")
            self.end_headers()
        elif self.path.startswith("/redirect-loop"):
            self.send_response(302)
            self.send_header("Location", "/redirect-loop-2")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"fallback")

    def log_message(self, fmt: str, *args) -> None:  # silence stderr noise
        return


@pytest.fixture(scope="session")
def http_fixture() -> Iterator[str]:
    """Start a local HTTPServer on 127.0.0.1 and yield its base URL."""
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
