"""Declared browser evidence matrix for the Nexus Hub guide (v4.4.2 Phase 7).

Dev-only tool, versioned so the evidence a release ships can be regenerated on demand. It is
NOT installer-copied and needs Playwright with Chromium (``pip install playwright &&
playwright install chromium``).

The case set is DECLARED before anything runs: every group below is Cartesian only across the
dimensions that own a distinct layout, theme, state, or interaction contract, and the summary
records the declared count next to the executed count so a silently dropped case is visible.
Each case captures console errors, external requests (there must be none: the guide is one
offline file), Training geometry (pairwise intersection and fullscreen coverage), and, for
the retained cases, a screenshot.

Usage::

    python tests/guides/tools/browser_matrix.py --label phase-7
    python tests/guides/tools/browser_matrix.py --label phase-7 --groups home,fullscreen
    python tests/guides/tools/browser_matrix.py --label phase-9 --out docs/releases/v4/v4.4/development/guide-illustration-clarity-rebuild/renders

If one invocation would exceed the 20 minute focused-runtime ceiling, run the groups in
labelled batches with ``--groups`` rather than dropping a declared case. Evidence must stay
under 30 MiB per label.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parents[3]
GUIDE = _ROOT / "guides" / "website" / "nexus-hub-guide.html"
PLAN_SLUG = "guide-illustration-clarity-rebuild"
PLAN_LABEL = "v4.4.3 guide-illustration-clarity-rebuild"
DEFAULT_OUT = _ROOT / "docs" / "releases" / "v4" / "v4.4" / "development" / PLAN_SLUG / "renders"

PAGES = ("home", "foundations", "training", "cheatsheets")
THEMES = ("dark", "light")
ROUTES = ("describe", "review", "plan", "implement", "compare", "test", "update", "presentify")
DESKTOP = ((1280, 720), (1366, 768), (1440, 900), (1920, 1080))

REGIONS = {
    "toolbar": ".nht-bar", "progress": ".nht-loop", "head": ".nht-head", "game": ".nht-game",
    "terminal": ".term--nht", "tools": ".nht-tools", "after": ".nht-after",
    "explorer": ".nht-explorer", "takeaway": ".nht-takeaway", "controls": ".nht-controls",
}
PAIRS = [
    ("toolbar", "game"), ("toolbar", "terminal"), ("game", "terminal"), ("game", "explorer"),
    ("terminal", "explorer"), ("explorer", "takeaway"), ("takeaway", "controls"),
]

GEOMETRY_JS = """([regions, pairs]) => {
    const visibleRect = (el) => {
        const r = el.getBoundingClientRect();
        let box = {l: r.left, t: r.top, rt: r.right, b: r.bottom};
        for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
            const cs = getComputedStyle(p);
            if (cs.overflow === 'visible' && cs.overflowY === 'visible' && cs.overflowX === 'visible') continue;
            const pr = p.getBoundingClientRect();
            box.l = Math.max(box.l, pr.left); box.t = Math.max(box.t, pr.top);
            box.rt = Math.min(box.rt, pr.right); box.b = Math.min(box.b, pr.bottom);
        }
        return {x: box.l, y: box.t, w: Math.max(0, box.rt - box.l), h: Math.max(0, box.b - box.t)};
    };
    const box = {}, missing = [];
    for (const k in regions) {
        const el = document.querySelector(regions[k]);
        if (!el) { missing.push(k); continue; }
        box[k] = visibleRect(el);
    }
    const overlaps = [];
    for (const [a, b] of pairs) {
        if (!box[a] || !box[b]) continue;
        const A = box[a], B = box[b];
        const ow = Math.max(0, Math.min(A.x + A.w, B.x + B.w) - Math.max(A.x, B.x));
        const oh = Math.max(0, Math.min(A.y + A.h, B.y + B.h) - Math.max(A.y, B.y));
        if (ow * oh >= 1) overlaps.push({pair: a + '/' + b, area: Math.round(ow * oh)});
    }
    const vw = innerWidth, vh = innerHeight, cell = 8, cols = Math.ceil(vw / cell);
    const grid = new Uint8Array(cols * Math.ceil(vh / cell));
    for (const k in box) {
        const r = box[k];
        for (let y = Math.max(0, r.y); y < Math.min(vh, r.y + r.h); y += cell)
            for (let x = Math.max(0, r.x); x < Math.min(vw, r.x + r.w); x += cell)
                grid[Math.floor(y / cell) * cols + Math.floor(x / cell)] = 1;
    }
    let n = 0; for (const v of grid) n += v;
    const stage = document.querySelector('.nag-stage');
    return {
        missing, overlaps,
        coverage: +(n / grid.length).toFixed(3),
        stageHeightFraction: stage ? +(stage.getBoundingClientRect().height / vh).toFixed(3) : null,
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        portraitGame: stage ? stage.getBoundingClientRect().height >= stage.getBoundingClientRect().width - 1 : null,
    };
}"""


def declare_groups() -> dict[str, list[dict]]:
    """Every case, declared up front. Keys are group names usable with --groups."""
    base = GUIDE.as_uri()
    g: dict[str, list[dict]] = {}

    g["base"] = [dict(label=f"base-{pg}-{th}-{w}", url=f"{base}#{pg}", width=w, height=900, theme=th, retain=True)
                 for pg in PAGES for th in THEMES for w in (320, 420, 900, 1440)]
    g["seam"] = [dict(label=f"seam-foundations-{th}-{w}", url=f"{base}#foundations", width=w, height=900, theme=th, retain=True)
                 for th in THEMES for w in (720, 721)]
    g["states"] = [dict(label=f"state-{r}-{th}-1440", url=f"{base}#training/{r}", width=1440, height=900, theme=th, retain=True)
                   for r in ROUTES for th in THEMES]
    g["fullscreen"] = [dict(label=f"fs-{r}-{mode}-{th}-{w}x{h}", url=f"{base}#training/{r}", width=w, height=h, theme=th,
                            retain=(r == "presentify"), fullscreen=mode, after="present", geometry=True)
                       for r in ("describe", "presentify") for mode in ("native", "fallback") for th in THEMES for (w, h) in DESKTOP]
    g["narrow"] = [dict(label=f"narrow-{r}-{th}-{w}", url=f"{base}#training/{r}", width=w, height=900, theme=th,
                        retain=(r == "presentify"), fullscreen="fallback", after="present", geometry=True)
                   for r in ("describe", "presentify") for th in THEMES for w in (320, 420, 900)]
    g["short"] = [dict(label=f"short-presentify-{th}-1280x600", url=f"{base}#training/presentify", width=1280, height=600, theme=th,
                       retain=True, fullscreen="fallback", after="present", geometry=True) for th in THEMES]
    g["reduced"] = [dict(label=f"rm-{name}-{th}-1440", url=url, width=1440, height=900, theme=th, retain=True, reduced=True)
                    for (name, url) in (("home", f"{base}#home"), ("foundations", f"{base}#foundations"), ("training-presentify", f"{base}#training/presentify"))
                    for th in THEMES]
    g["zoom"] = [dict(label=f"zoom200-{r}-{th}-{w}x{h}", url=f"{base}#training/{r}", width=w, height=h, theme=th,
                      retain=(r == "presentify"), zoom=2, after="present", geometry=True)
                 for r in ("describe", "presentify") for th in THEMES for (w, h) in ((1280, 720), (1366, 768))]
    # v4.4.2 additions
    g["home-sections"] = [dict(label=f"home-{sec}-{th}-{w}", url=f"{base}#home", width=w, height=900, theme=th, retain=True, scroll=f"#{sec}")
                          for sec in ("nhg-why", "nhg-how", "nhg-guardrails", "nhg-commands") for th in THEMES for w in (420, 1440)]
    g["annotated"] = [dict(label=f"ann-{scene}-{state}-{th}-1440", url=f"{base}#foundations", width=1440, height=900, theme=th, retain=True,
                           scroll=f"#{scene}", seq=(scene, state))
                      for scene in ("fx-ann-prompt", "fx-ann-context") for state in ("mid", "end") for th in THEMES]
    # v4.4.4 retired the audio output and its waveform, so the group that photographed it goes too.
    # v4.4.3: the two harness scenes are one, its figure carries six stops, and two more scenes
    # became choreographed. Each group names the id its sequence root now has.
    g["harness"] = [dict(label=f"harness-step{step}-{th}-1440", url=f"{base}#foundations", width=1440, height=900, theme=th, retain=True,
                         scroll="#fx-harness", seq=("hx-harness", step)) for step in (1, 3, 5, "end") for th in THEMES]
    # v4.4.5 rebuilt Models on an eight-stage spine, and a rebuilt scene that nothing
    # photographs is a scene whose duplication ships. This plan's Phase 5 shipped exactly that
    # for one commit, so the scene now has its own group at a narrow and a wide width.
    g["models"] = [dict(label=f"models-{th}-{w}", url=f"{base}#foundations", width=w, height=900,
                        theme=th, retain=True, scroll="#fx-model-lifecycle")
                   for th in THEMES for w in (420, 1440)]
    g["comparison"] = [dict(label=f"compare-{state}-{th}-{w}", url=f"{base}#foundations", width=w, height=900, theme=th, retain=True,
                            scroll="#fx-agent-platform", seq=("cv-compare", state))
                       for state in ("mid", "end") for th in THEMES for w in (420, 1440)]
    # v4.4.4 merged the comparison into the Agentic Platforms scene and retired its six-stage
    # flow, so the comparison group below photographs that scene and a platforms group is not needed.
    g["pointer"] = [dict(label=f"arena-pointer-paused-{th}-1440", url=f"{base}#training/describe", width=1440, height=900, theme=th, retain=True, pointer=True)
                    for th in THEMES]
    return g


def run(groups: dict[str, list[dict]], out: pathlib.Path, label: str) -> dict:
    from playwright.sync_api import sync_playwright

    out_dir = out / label
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    cases: list[dict] = []
    shots = 0
    declared = sum(len(v) for v in groups.values())

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for group, items in groups.items():
            for c in items:
                ctx = browser.new_context(viewport={"width": c["width"], "height": c["height"]}, color_scheme=c["theme"],
                                          reduced_motion="reduce" if c.get("reduced") else "no-preference", device_scale_factor=1)
                errors: list[str] = []
                requests: list[str] = []
                page = ctx.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
                page.on("request", lambda r: requests.append(r.url) if r.url.startswith("http") else None)
                page.goto(c["url"])
                page.wait_for_function("window.NexusTraining && window.NexusShooter && window.NexusSeq")
                page.wait_for_timeout(300)
                if c.get("zoom"):
                    page.evaluate("z => { document.documentElement.style.zoom = z; }", c["zoom"])
                    page.wait_for_timeout(200)
                if c.get("after") == "present":
                    page.locator("#nhtPresent").click()
                    page.wait_for_function("document.getElementById('nhTraining').classList.contains('is-present')")
                    page.wait_for_timeout(300)
                if c.get("scroll"):
                    page.locator(c["scroll"]).first.scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                if c.get("seq"):
                    root, state = c["seq"]
                    if state == "end":
                        page.evaluate(f"() => {{ const r = document.getElementById('{root}'); window.NexusSeq.pause(r); "
                                      f"r.querySelectorAll('[data-seq]').forEach(e => e.classList.add('is-on')); }}")
                    else:
                        target = 2 if state == "mid" else int(state)
                        page.evaluate(f"() => {{ const r = document.getElementById('{root}'); window.NexusSeq.reset(r); window.NexusSeq.play(r); }}")
                        page.wait_for_function(f"() => window.NexusSeq.state(document.getElementById('{root}')).step >= {target}", timeout=15000)
                        page.evaluate(f"() => window.NexusSeq.pause(document.getElementById('{root}'))")
                    page.wait_for_timeout(200)
                if c.get("wave"):
                    page.evaluate("() => { const a = document.querySelector('audio.fx-out-audio'); a.volume = 0.05; return a.play(); }")
                    page.wait_for_function("() => document.querySelector('canvas.fx-wave').dataset.waveState === 'live'", timeout=5000)
                    if c["wave"] == "paused":
                        page.evaluate("() => document.querySelector('audio.fx-out-audio').pause()")
                        page.wait_for_function("() => document.querySelector('canvas.fx-wave').dataset.waveState === 'static'")
                    page.wait_for_timeout(150)
                if c.get("pointer"):
                    page.locator("[data-arcade-start]").click()
                    page.wait_for_function("window.NexusShooter.snapshot().lifecycle === 'running'")
                    box = page.locator('[data-arcade="stage"]').bounding_box()
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    page.mouse.move(box["x"] + box["width"] + 60, box["y"] + 20)
                    page.wait_for_function("window.NexusShooter.snapshot().pauseReasons.includes('pointer')")
                    page.wait_for_timeout(150)
                geo = page.evaluate(GEOMETRY_JS, [REGIONS, PAIRS]) if c.get("geometry") else {}
                record = {"group": group, **{k: v for k, v in c.items() if k != "url"}, "errors": errors,
                          "externalRequests": requests, "geometry": geo}
                if c.get("retain"):
                    page.screenshot(path=str(out_dir / f"{c['label']}.png"), full_page=False)
                    shots += 1
                cases.append(record)
                ctx.close()
        browser.close()

    elapsed = time.time() - started
    failures = [r for r in cases if r["errors"] or r["externalRequests"] or r["geometry"].get("overlaps")
                or r["geometry"].get("missing") or r["geometry"].get("horizontalOverflow")]
    evidence_bytes = sum(f.stat().st_size for f in out_dir.glob("*.png"))
    summary = {
        "generated": time.strftime("%Y-%m-%d"), "label": label, "plan": PLAN_LABEL,
        "declaredCases": declared, "executedCases": len(cases),
        "declaredScreenshots": sum(1 for v in groups.values() for c in v if c.get("retain")), "retainedScreenshots": shots,
        "focusedRuntimeSeconds": round(elapsed, 1), "runtimeTargetSeconds": 1200,
        "evidenceBytes": evidence_bytes, "evidenceCeilingBytes": 30 * 1024 * 1024,
        "groups": {k: len(v) for k, v in groups.items()},
        "failures": [{"label": r["label"], "errors": r["errors"], "externalRequests": r["externalRequests"], "geometry": r["geometry"]} for r in failures],
        "cases": cases,
    }
    (out_dir / f"{label}-browser-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"cases: {len(cases)}/{declared}  screenshots: {shots}/{summary['declaredScreenshots']}")
    print(f"runtime: {elapsed:.0f}s / 1200s   evidence: {evidence_bytes / 1024 / 1024:.1f} MiB / 30 MiB")
    print(f"failures: {len(failures)}")
    for f in failures[:8]:
        print("  ", f["label"], f["errors"][:1], f["externalRequests"][:1], f["geometry"].get("overlaps"))
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--label", required=True, help="evidence label, e.g. phase-7")
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--groups", default="", help="comma-separated subset of case groups (default: all)")
    args = ap.parse_args(argv)
    groups = declare_groups()
    if args.groups:
        wanted = [g.strip() for g in args.groups.split(",") if g.strip()]
        unknown = [g for g in wanted if g not in groups]
        if unknown:
            print(f"browser_matrix: unknown group(s) {unknown}; known: {list(groups)}", file=sys.stderr)
            return 2
        groups = {g: groups[g] for g in wanted}
    summary = run(groups, args.out, args.label)
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
