"""Extract the visible text of a saved vendor page for v4.13.9 T405 (evidence only).

Scripts, styles, templates, and elements marked hidden (the `hidden` attribute,
`aria-hidden="true"`, or an inline `display:none` / `visibility:hidden` style) are
dropped, so a quote can never come from text a reader of the page would not see.

Usage: python extract_text.py <page.html> <page.txt>
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "noscript", "template", "svg", "head"}
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_BLOCK = {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "pre", "td", "th", "br", "table", "ul", "ol", "dt", "dd"}
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.I)


class _Visible(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[bool] = []  # True = this element hides its content
        self.out: list[str] = []

    def _hidden(self) -> bool:
        return any(self.stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _VOID:
            if tag == "br" and not self._hidden():
                self.out.append("\n")
            return
        a = {k: (v or "") for k, v in attrs}
        hides = (
            tag in _SKIP_TAGS
            or "hidden" in a
            or a.get("aria-hidden", "").lower() == "true"
            or bool(_HIDDEN_STYLE.search(a.get("style", "")))
        )
        self.stack.append(hides)
        if tag in _BLOCK and not self._hidden():
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID or not self.stack:
            return
        self.stack.pop()
        if tag in _BLOCK and not self._hidden():
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._hidden():
            self.out.append(data)


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    parser = _Visible()
    parser.feed(open(src, encoding="utf-8", errors="replace").read())
    text = "".join(parser.out)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    open(dst, "w", encoding="utf-8", newline="\n").write(cleaned + "\n")
    print(f"{dst}: {len(cleaned)} chars, {cleaned.count(chr(10)) + 1} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
