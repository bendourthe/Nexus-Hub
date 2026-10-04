"""v4.13.10 helper for plan sub-task 7.4a (T042): shared openings and outlines on Foundations and Cheatsheets.

Written and verified during Phase 2, then held because the guide's 500,000-byte ceiling has no room
until Phase 7 removes the old in-guide Training. Run it from the repository root once, after that
removal. Before running, adjust two things the Phase 2 state changed:

- The manifest step at the bottom adds fragment definitions that already exist. Instead, add
  opening-css, outline-css, outline-js, and motion-css to the guide page's "fragments" list.
- Also add a "/* shared:motion-css */" marker pair beside the opening and outline markers, and remove
  the guide's own copies of the generic reduced-motion lines that motion-css now carries.

Then run python scripts/stamp_guide_shared.py and delete this file.
"""
import json
import re
from pathlib import Path

G = Path("guides/website/nexus-hub-guide.html")
raw = G.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
s = raw.replace("\r\n", "\n")


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old))
    s = s.replace(old, new)


SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
GLYPH = {
    "tokens": '<rect x="3" y="6" width="6" height="5" rx="1.5"/><rect x="11" y="6" width="10" height="5" rx="1.5"/><rect x="3" y="13" width="9" height="5" rx="1.5"/><rect x="14" y="13" width="7" height="5" rx="1.5"/>',
    "models": '<path d="M12 3 3 8l9 5 9-5-9-5Z"/><path d="m3 13 9 5 9-5"/>',
    "prompts": '<path d="M4 6h16M4 11h10M4 16h7"/><path d="m15 19 5-5-2-2-5 5v2h2Z"/>',
    "context": '<rect x="5" y="3" width="11" height="14" rx="2"/><path d="M9 21h8a2 2 0 0 0 2-2V8"/><path d="M8 8h5M8 12h5"/>',
    "platform": '<path d="M20 12a8 8 0 1 1-2.34-5.66"/><path d="M20 4v5h-5"/><circle cx="12" cy="12" r="2"/>',
    "shield": '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    "explore": '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
    "plan": '<path d="M10 6h10M10 12h10M10 18h10"/><path d="m3.5 6 1.5 1.5L7.5 5M3.5 12l1.5 1.5L7.5 11"/><circle cx="5" cy="18" r="1"/>',
    "build": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    "ship": '<path d="M5 19 19 5M19 5h-7M19 5v7"/>',
    "talk": '<path d="M4 5h16v11H9l-5 4V5Z"/><path d="M8 9h8M8 12h5"/>',
    "grid": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
}


def tile(glyph, title, text, href, extra=""):
    return (
        f'          <li><span class="pg-glyph">{SVG.format(GLYPH[glyph])}</span>'
        f'<div><b>{title}</b><span>{text}</span>{extra}</div>'
        f'<a href="{href}" aria-label="{title}: {text}"></a></li>\n'
    )


# 1. Shared fragment markers.
rep("/* /shared:footer-css */\n", "/* /shared:footer-css */\n/* shared:opening-css */\n/* /shared:opening-css */\n/* shared:outline-css */\n/* /shared:outline-css */\n")
rep("/* /shared:nexusseq-js */\n", "/* /shared:nexusseq-js */\n/* shared:outline-js */\n/* /shared:outline-js */\n")

# 2. Foundations opening.
f_tiles = "".join([
    tile("tokens", "Tokens", "The units a model actually reads", "#foundations/fx-tokens"),
    tile("models", "Models", "How a model learns, then answers", "#foundations/fx-model-lifecycle"),
    tile("prompts", "Prompt Engineering", "Stating the job so the result is checkable", "#foundations/fx-prompts"),
    tile("context", "Context Engineering", "Choosing the material the job needs", "#foundations/fx-context"),
    tile("platform", "Agentic Platforms", "Same model, very different capabilities", "#foundations/fx-agent-platform"),
    tile("shield", "Harnesses", "Turning knowledge into safer, reusable work", "#foundations/fx-harness"),
])
m = re.search(r'      <div class="hero">\n        <h1 data-ty="h1" class="hero-subtitle page-title">(.*?)</h1>\n        <p data-ty="lead" class="page-lead">(.*?)</p>\n      </div>\n', s, re.DOTALL)
assert m and s.count('class="hero-subtitle page-title"') == 1
s = s[:m.start()] + (
    '      <div class="hero pg-open">\n'
    f'        <h1 data-ty="h1" class="hero-subtitle page-title pg-open-title">{m.group(1)}</h1>\n'
    f'        <p data-ty="lead" class="page-lead pg-open-lead">{m.group(2)}</p>\n'
    '        <ol class="pg-map" aria-label="What this page covers">\n' + f_tiles +
    '        </ol>\n'
    '      </div>\n'
    '      <div class="pg-outline-host" data-outline-page="foundations"></div>\n'
) + s[m.end():]

# 3. Cheatsheets opening (the jump bar becomes the outline).
c_start = s.index('      <div class="hero">\n        <span data-ty="eyebrow" class="eyebrow">Cheatsheets</span>')
c_end = s.index("        </nav>\n      </div>\n", c_start) + len("        </nav>\n      </div>\n")
old = s[c_start:c_end]
lead = re.search(r'<p data-ty="lead" class="lead">(.*?)</p>', old, re.DOTALL).group(1)
groups = [("explore", "explore", "Understand and evaluate", "Read-only reports on a codebase", 3),
          ("plan", "plan", "Plan the work", "Specs, plans, and their review", 3),
          ("build", "build", "Build it", "Implement a phase, then the whole plan", 2),
          ("harden", "shield", "Prove it", "Tests and multi-angle review", 1),
          ("ship", "ship", "Ship and govern", "Releases, docs, and repository hygiene", 4),
          ("communicate", "talk", "Communicate", "Reports, decks, and visuals", 3),
          ("catalog", "grid", "Catalog and session", "Skills, models, and session tools", 8)]
c_tiles = "".join(
    tile(glyph, title, text, f"#cheatsheets/{gid}",
         f'<span class="pg-count" data-cs-count="cs-{gid}">{n} command{"s" if n != 1 else ""}</span>')
    for gid, glyph, title, text, n in groups)
s = s[:c_start] + (
    '      <div class="hero pg-open">\n'
    '        <h1 data-ty="h1" class="pg-open-title">Every command, <span class="gtext">every scope</span></h1>\n'
    f'        <p data-ty="lead" class="pg-open-lead">{lead}</p>\n'
    '        <ol class="pg-map" aria-label="Command groups">\n' + c_tiles +
    '        </ol>\n'
    '      </div>\n'
    '      <div class="pg-outline-host" data-outline-page="cheatsheets"></div>\n'
) + s[c_end:]

# 4. Router: Foundations sub-routes scroll like Cheatsheets ones.
rep('''    if (id === "cheatsheets" && parts[1]) {
      window.requestAnimationFrame(function () {
        var el = document.getElementById("cs-" + parts[1]);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "start", behavior: "auto" });
      });
    }
''', '''    if (id === "cheatsheets" && parts[1]) {
      window.requestAnimationFrame(function () {
        var el = document.getElementById("cs-" + parts[1]);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "start", behavior: "auto" });
      });
    }
    if (id === "foundations" && parts[1]) {
      window.requestAnimationFrame(function () {
        var el = document.getElementById(parts[1]);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "start", behavior: "auto" });
      });
    }
''')

# 5. Mount the outlines and fill the group counts.
rep("  /* -------------------------------------------------- boot */\n", '''  /* -------------------------------------------------- page outlines (v4.13.10) */
  (function () {
    var hosts = document.querySelectorAll("[data-outline-page]");
    for (var h = 0; h < hosts.length; h++) {
      var pageId = hosts[h].getAttribute("data-outline-page");
      var cs = pageId === "cheatsheets";
      var secs = document.querySelectorAll(cs ? "#page-cheatsheets section.cs-group[id]" : "#page-foundations section.fx-scene[id]");
      var items = [];
      for (var k = 0; k < secs.length; k++) {
        var label = (cs ? (secs[k].querySelector(".eyebrow") || secs[k].querySelector("h2")) : secs[k].querySelector("h2")).textContent;
        var sub = cs ? secs[k].id.replace(/^cs-/, "") : secs[k].id;
        items.push({ id: secs[k].id, label: label.replace(/\\s+/g, " ").trim(), href: "#" + pageId + "/" + sub, target: secs[k].id });
      }
      window.NexusOutline.mount(hosts[h], items, { mode: "scroll" });
    }
    var counts = document.querySelectorAll("[data-cs-count]");
    for (var c = 0; c < counts.length; c++) {
      var group = document.getElementById(counts[c].getAttribute("data-cs-count"));
      var n = group ? group.querySelectorAll(".cs-cmd").length : 0;
      counts[c].textContent = n + (n === 1 ? " command" : " commands");
    }
  })();

  /* -------------------------------------------------- boot */
''')

G.write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))

mf = Path("guides/website/shared/fragments.json")
d = json.loads(mf.read_text(encoding="utf-8"))
d["fragments"]["opening-css"] = {"syntax": "css", "file": "opening.css"}
d["fragments"]["outline-css"] = {"syntax": "css", "file": "outline.css"}
d["fragments"]["outline-js"] = {"syntax": "js", "file": "outline.js"}
mf.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8", newline="\n")
print("guide edited")
