"""Export the HTML guide's complete cheatsheet as theme-neutral GitHub Markdown."""
from __future__ import annotations

import unicodedata


def cheatsheet(page, root):
    page.goto((root / "guides/website/nexus-hub-guide.html").as_uri() + "#cheatsheets")
    groups = page.evaluate(r"""() => {
      function md(el) {
        if (!el) return '';
        return [...el.childNodes].map(n => {
          if(n.nodeType===3) return n.textContent;
          const text=md(n);
          if(n.tagName==='CODE') return '`'+n.textContent+'`';
          if(n.tagName==='A') {const href=n.getAttribute('href');return '['+text+']('+(href.startsWith('http')?href:'guides/website/'+href)+')';}
          if(['B','STRONG'].includes(n.tagName)) return '**'+text+'**';
          if(n.tagName==='BR') return ' ';
          return text;
        }).join('').replace(/\s+/g,' ').trim();
      }
      return [...document.querySelectorAll('#page-cheatsheets .cs-group')].map(g=>({
        title:md(g.querySelector('h2')),description:md(g.querySelector(':scope > p')),
        cards:[...g.querySelectorAll('.cs-cmd')].map(c=>({name:md(c.querySelector('.cs-name')),description:md(c.querySelector('.cs-desc')),
          scopes:[...c.querySelectorAll('.cs-scope')].map(s=>[md(s.querySelector('code')),md(s.querySelector('span'))]),
          examples:[...c.querySelectorAll('.inv')].map(n=>n.textContent.trim()),
          notes:[...c.querySelectorAll('.cs-flags,.cs-teach')].map(md)}))}));
    }""")
    assert len(groups) == 7 and sum(len(g["cards"]) for g in groups) == 24
    lines = ["<!-- readme-cheatsheet:start -->"]
    for index, group in enumerate(groups):
        if index:
            lines.extend(["", "---"])
        lines.extend(["", f"### {group['title']}", "", group["description"]])
        for card in group["cards"]:
            # The installed handoff contract is chat-only unless a file is requested.
            description = card["description"] if card["name"] != "/handoff" else "Print a paste-ready resume prompt in chat so another agent can continue. Write a file only when requested."
            lines.extend(["", f"#### `{card['name']}`", "", description])
            if card["scopes"]:
                lines.extend(["", "| Scope | Behavior |", "| --- | --- |"])
                for scope, detail in card["scopes"]:
                    lines.append("| `" + scope.strip("`").replace("|", "\\|") + "` | " + detail.replace("|", "\\|") + " |")
            if card["examples"]:
                lines.extend(["", "```text", *card["examples"], "```"])
            for note in card["notes"]:
                lines.extend(["", note])
    lines.extend(["", "<!-- readme-cheatsheet:end -->"])
    text = "\n".join(lines)
    text = text.translate(str.maketrans({"\u2014": ": ", "\u2013": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2192": "->", "\u2026": "...", "\u00a0": " "}))
    text = unicodedata.normalize("NFKD", text).encode("ascii", "xmlcharrefreplace").decode("ascii")
    return text + "\n"
