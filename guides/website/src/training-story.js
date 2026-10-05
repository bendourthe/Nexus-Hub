/* ===================================================================== Training story renderer (v4.13.10)
   Reads the story (#nh-training-story) and the stamped model map (#nh-training-models)
   and builds each stage: the step banner with its model badge, the play callouts, the
   structured agent sessions, and the project file panel. Text is only ever set with
   textContent. A story that is missing a required field renders nothing and names the
   field in the page notice instead. Inlined into training.html by
   scripts/stamp_guide_shared.py: edit this file, not the page.
   ===================================================================== */
window.NexusTrainingStory = (function () {
  "use strict";

  var PROVIDER_KEY = "nh-training-provider";
  var CHECK = "✓", CROSS = "✗";

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function readJson(id) {
    var node = document.getElementById(id);
    if (!node) throw new Error("the page has no #" + id + " block");
    return JSON.parse(node.textContent);
  }

  /* -------------------------------------------------- validation (the fields rendering relies on) */
  function need(obj, path, key, kind) {
    var v = obj == null ? undefined : obj[key];
    var ok = kind === "array" ? Array.isArray(v) && v.length > 0 : kind === "string" ? typeof v === "string" && v.length > 0 : v != null && typeof v === "object";
    if (!ok) throw new Error("field " + path + "." + key + " is missing or empty");
    return v;
  }
  function validate(story) {
    need(story, "story", "stages", "array");
    need(story, "story", "providers", "array");
    story.stages.forEach(function (st, i) {
      var p = "stages[" + i + "]";
      need(st, p, "id", "string");
      need(st, p, "kind", "string");
      if (st.kind === "intro") return;
      var banner = need(st, p, "banner", "object");
      ["step", "title", "now"].forEach(function (k) { need(banner, p + ".banner", k, "string"); });
      if (st.kind === "play") {
        need(st, p, "game", "string");
        need(need(st, p, "callout", "object"), p + ".callout", "items", "array");
      } else if (st.kind === "session") {
        need(st, p, "command", "string");
        var badge = need(st, p, "badge", "object");
        ["tier", "effort", "reason"].forEach(function (k) { need(badge, p + ".badge", k, "string"); });
        var session = need(st, p, "session", "object");
        need(session, p + ".session", "summary", "string");
        need(session, p + ".session", "sections", "array");
        need(st, p, "files", "array");
      } else {
        throw new Error("field " + p + ".kind has an unknown value " + JSON.stringify(st.kind));
      }
    });
  }

  /* -------------------------------------------------- provider choice */
  var models = null, provider = null, badges = [];
  function storedProvider() {
    try { return window.localStorage.getItem(PROVIDER_KEY); } catch (err) { return null; }
  }
  function setProvider(name) {
    if (!models || models.providers.indexOf(name) === -1) return;
    provider = name;
    try { window.localStorage.setItem(PROVIDER_KEY, name); } catch (err) { /* storage blocked: the choice lasts this visit */ }
    badges.forEach(paintBadge);
  }
  function paintBadge(b) {
    var row = models.tiers[b.tier] || {};
    b.model.textContent = row[provider] || "not in the bundled map";
    b.model.setAttribute("data-provider", provider);
    for (var i = 0; i < b.buttons.length; i++) {
      b.buttons[i].setAttribute("aria-pressed", b.buttons[i].getAttribute("data-provider") === provider ? "true" : "false");
    }
  }

  /* -------------------------------------------------- pieces */
  function badgeFor(st) {
    var box = el("div", "tr-badge");
    box.setAttribute("data-tier", st.badge.tier);
    box.setAttribute("aria-label", "What the agent uses for this step");
    var grid = el("dl", "tr-badge-grid");
    function pair(k, v, cls) {
      var wrap = el("div", "tr-badge-pair");
      wrap.appendChild(el("dt", null, k));
      var dd = el("dd", cls || null, v);
      wrap.appendChild(dd);
      grid.appendChild(wrap);
      return dd;
    }
    pair("Tier", st.badge.tier);
    pair("Effort", st.badge.effort);
    var model = pair("Model", "", "tr-badge-model");
    model.setAttribute("data-tier-model", st.badge.tier);
    box.appendChild(grid);
    box.appendChild(el("p", "tr-badge-why", st.badge.reason));
    var group = el("div", "tr-provider");
    group.setAttribute("role", "group");
    group.setAttribute("aria-label", "Show the model for");
    var buttons = [];
    models.providers.forEach(function (name) {
      var btn = el("button", null, name);
      btn.type = "button";
      btn.setAttribute("data-provider", name);
      btn.addEventListener("click", function () { setProvider(name); });
      group.appendChild(btn);
      buttons.push(btn);
    });
    box.appendChild(group);
    var b = { tier: st.badge.tier, model: model, buttons: buttons };
    badges.push(b);
    paintBadge(b);
    return box;
  }

  function bannerFor(st, heading) {
    var header = el("header", "tr-banner");
    var lead = el("div", "tr-banner-copy");
    lead.appendChild(el("p", "tr-step", st.banner.step));
    heading.textContent = st.banner.title;
    heading.classList.add("tr-title");
    lead.appendChild(heading);
    var now = el("p", "tr-now");
    now.appendChild(el("b", null, "Now: "));
    now.appendChild(document.createTextNode(st.banner.now));
    lead.appendChild(now);
    header.appendChild(lead);
    if (st.badge) header.appendChild(badgeFor(st));
    return header;
  }

  function checksFor(list) {
    var ul = el("ul", "tr-checks");
    list.forEach(function (c) {
      var li = el("li");
      li.setAttribute("data-result", c.result);
      li.appendChild(el("span", "tr-check-mark", c.result === "pass" ? CHECK : CROSS));
      li.appendChild(el("span", "tr-check-name", c.name));
      li.appendChild(el("span", "tr-check-result", c.result === "pass" ? "pass" : "fail"));
      ul.appendChild(li);
    });
    return ul;
  }

  function diffFor(diff) {
    var fig = el("figure", "tr-diff");
    if (diff.lines.length > 40) fig.setAttribute("data-long", "");
    fig.appendChild(el("figcaption", null, diff.path));
    var pre = el("pre");
    diff.lines.forEach(function (line) {
      var row = el("span", "tr-diff-line", line.length > 1 ? line : line + " ");
      row.setAttribute("data-op", line.charAt(0) === "+" ? "add" : line.charAt(0) === "-" ? "del" : "ctx");
      pre.appendChild(row);
    });
    fig.appendChild(pre);
    return fig;
  }

  function sessionFor(st) {
    var art = el("article", "tr-session");
    art.setAttribute("aria-label", "Agent session for " + st.command);
    var cmd = el("p", "tr-cmd");
    cmd.appendChild(el("span", "tr-prompt", ">"));
    cmd.appendChild(el("code", null, st.command));
    var run = el("button", "tr-run", "Run again");
    run.type = "button";
    cmd.appendChild(run);
    art.appendChild(cmd);
    art.appendChild(el("p", "tr-summary", st.session.summary));
    var parts = [];
    st.session.sections.forEach(function (sec) {
      var box = el("section", "tr-section");
      parts.push(box);
      box.appendChild(el("h2", "tr-section-title", sec.heading));
      if (sec.items) {
        var ul = el("ul", "tr-items");
        sec.items.forEach(function (t) { ul.appendChild(el("li", null, t)); });
        box.appendChild(ul);
      }
      if (sec.code) {
        var fig = el("figure", "tr-snippet");
        fig.appendChild(el("figcaption", null, sec.code.label));
        var pre = el("pre");
        pre.appendChild(el("code", null, sec.code.text));
        fig.appendChild(pre);
        box.appendChild(fig);
      }
      if (sec.diff) box.appendChild(diffFor(sec.diff));
      if (sec.checks) box.appendChild(checksFor(sec.checks));
      art.appendChild(box);
    });
    var details = el("details", "tr-details");
    details.appendChild(el("summary", null, "Show technical details"));
    var dl = el("dl");
    function row(k, v) { var w = el("div"); w.appendChild(el("dt", null, k)); w.appendChild(el("dd", null, v)); dl.appendChild(w); }
    row("Command", st.command);
    row("Files", st.files.map(function (f) { return f.path + " (" + f.status + ")"; }).join(", "));
    row("Model map", "verified " + models.verified_as_of + ", from " + models.source);
    details.appendChild(dl);
    art.appendChild(details);
    return { article: art, parts: parts, cmd: cmd, run: run };
  }

  function activityFor(st) {
    var box = el("section", "tr-activity");
    box.setAttribute("aria-label", "What the agent did, in order");
    box.appendChild(el("p", "tr-files-head", "Agent activity"));
    var ol = el("ol");
    st.activity.forEach(function (a) {
      var li = el("li");
      var tool = el("span", "tr-tool", a.tool);
      tool.setAttribute("data-tool", a.tool.toLowerCase());
      li.appendChild(tool);
      li.appendChild(el("span", "tr-target", a.target));
      ol.appendChild(li);
    });
    box.appendChild(ol);
    return box;
  }

  /* Sessions type themselves out the first time a stage is shown, so a step reads like a live
     agent run: the command is typed, then each part of the report and each activity line appears in
     reading order. "Skip" finishes at once and "Run again" replays. Layout never moves: waiting
     lines keep their space (visibility, not display). Reduced motion shows the finished report.
     Automated browsers (navigator.webdriver) also see it finished unless they turn typing on, so
     measurements read the whole report. */
  var REDUCED_MOTION = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var autoType = !REDUCED_MOTION && !navigator.webdriver;
  function lines(w) {
    var out = [w.article.querySelector(".tr-summary")];
    w.parts.forEach(function (part) {
      var nodes = part.querySelectorAll(".tr-section-title, .tr-items > li, .tr-snippet, .tr-diff, .tr-checks > li");
      for (var i = 0; i < nodes.length; i++) out.push(nodes[i]);
    });
    return out;
  }
  function finish(w) {
    w.timers.forEach(window.clearTimeout);
    w.timers = [];
    var code = w.cmd.querySelector("code");
    if (code.hasAttribute("data-full")) { code.textContent = code.getAttribute("data-full"); code.removeAttribute("data-full"); }
    var waiting = w.grid.querySelectorAll(".tr-wait, .tr-in");
    for (var i = 0; i < waiting.length; i++) waiting[i].classList.remove("tr-wait", "tr-in");
    w.article.removeAttribute("data-typing");
    w.run.textContent = "Run again";
  }
  function type(w) {
    finish(w);
    if (REDUCED_MOTION) return;
    w.played = true;
    var report = lines(w), acts = w.activity.querySelectorAll("li"), code = w.cmd.querySelector("code");
    var full = code.textContent;
    report.forEach(function (n) { n.classList.add("tr-wait"); });
    for (var a = 0; a < acts.length; a++) acts[a].classList.add("tr-wait");
    w.article.setAttribute("data-typing", "");
    w.run.textContent = "Skip";
    code.setAttribute("data-full", full);
    code.textContent = "";
    var t = 0;
    function at(ms, fn) { w.timers.push(window.setTimeout(fn, ms)); }
    for (var c = 1; c <= full.length; c++) at(t += 38, (function (n) { return function () { code.textContent = full.slice(0, n); }; })(c));
    t += 220;
    var shownActs = 0;
    report.forEach(function (n, i) {
      var len = (n.textContent || "").length, dur = Math.max(160, Math.min(1100, len * 9));
      at(t, function () { n.style.setProperty("--tr-d", dur + "ms"); n.classList.remove("tr-wait"); n.classList.add("tr-in"); });
      var due = Math.round((i + 1) / report.length * acts.length);
      while (shownActs < due) {
        at(t + 80, (function (li) { return function () { li.classList.remove("tr-wait"); li.classList.add("tr-in"); }; })(acts[shownActs]));
        shownActs += 1;
      }
      t += dur + 90;
    });
    at(t, function () { finish(w); });
  }
  function play(id) {
    works.forEach(function (w) {
      if (w.id !== id) { if (w.article.hasAttribute("data-typing")) finish(w); return; }
      if (autoType && !w.played) type(w);
    });
  }

  /* Keep the two columns close in height. With the columns side by side, two moves are
     measured each time a stage is shown: the report's trailing sections may continue under
     the file panel, and the activity log may sit under the report instead of under the
     files. The arrangement whose column bottoms end closest wins; reading order inside the
     report never changes. With one column, everything stays in its natural order. */
  var works = [];
  function place(w, k, activityLeft) {
    for (var i = 0; i < w.parts.length; i++) {
      if (i < k) w.article.insertBefore(w.parts[i], w.details);
      else w.more.appendChild(w.parts[i]);
    }
    w.more.hidden = k >= w.parts.length;
    if (activityLeft) w.main.appendChild(w.activity);
    else w.side.insertBefore(w.activity, w.more);
    /* The last visible card in each column grows, so both columns end flush. */
    [w.main, w.side].forEach(function (col) {
      var last = null;
      for (var c = 0; c < col.children.length; c++) {
        col.children[c].classList.remove("tr-grow");
        if (!col.children[c].hidden) last = col.children[c];
      }
      if (last) last.classList.add("tr-grow");
    });
  }
  function rebalance(w) {
    var n = w.parts.length;
    if (!w.grid.offsetParent) return;
    place(w, n, false);
    var sideBySide = w.side.getBoundingClientRect().top < w.main.getBoundingClientRect().bottom - 1;
    if (!sideBySide) return;
    var best = [n, false], bestGap = Infinity;
    [false, true].forEach(function (left) {
      for (var k = n; k >= 1; k--) {
        place(w, k, left);
        var gap = Math.abs(w.main.getBoundingClientRect().bottom - w.side.getBoundingClientRect().bottom);
        if (gap < bestGap - 1) { bestGap = gap; best = [k, left]; }
      }
    });
    place(w, best[0], best[1]);
  }

  function filesFor(st) {
    var aside = el("aside", "tr-files");
    aside.setAttribute("aria-label", "Project files");
    var head = el("p", "tr-files-head", "Project files");
    aside.appendChild(head);
    var list = el("div", "tr-tree");
    list.setAttribute("role", "tablist");
    list.setAttribute("aria-label", "Files the step read or changed");
    var code = el("pre", "tr-code");
    code.setAttribute("role", "tabpanel");
    var codeText = el("code");
    code.appendChild(codeText);
    var tabs = [];
    function select(i) {
      for (var k = 0; k < tabs.length; k++) {
        tabs[k].setAttribute("aria-selected", k === i ? "true" : "false");
        tabs[k].tabIndex = k === i ? 0 : -1;
      }
      codeText.textContent = st.files[i].code;
      code.setAttribute("aria-label", st.files[i].path);
    }
    st.files.forEach(function (f, i) {
      var tab = el("button", "tr-tab");
      tab.type = "button";
      tab.setAttribute("role", "tab");
      tab.appendChild(el("span", "tr-tab-path", f.path));
      var tag = el("span", "tr-tab-status", f.status);
      tag.setAttribute("data-status", f.status);
      tab.appendChild(tag);
      tab.addEventListener("click", function () { select(i); });
      tab.addEventListener("keydown", function (ev) {
        var n;
        if (ev.key === "ArrowRight" || ev.key === "ArrowDown") n = (i + 1) % tabs.length;
        else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") n = (i - 1 + tabs.length) % tabs.length;
        else if (ev.key === "Home") n = 0;
        else if (ev.key === "End") n = tabs.length - 1;
        else return;
        ev.preventDefault();
        select(n);
        tabs[n].focus();
      });
      list.appendChild(tab);
      tabs.push(tab);
    });
    aside.appendChild(list);
    aside.appendChild(code);
    select(st.files.length - 1);
    return aside;
  }

  function calloutFor(st) {
    var box = el("aside", "tr-callout");
    box.setAttribute("role", "note");
    box.setAttribute("data-tone", st.callout.tone === "ok" ? "ok" : "warn");
    box.appendChild(el("p", "tr-callout-title", st.callout.title));
    var ul = el("ul");
    st.callout.items.forEach(function (t) { ul.appendChild(el("li", null, t)); });
    box.appendChild(ul);
    if (st.callout.hidden) box.appendChild(el("p", "tr-callout-hidden", st.callout.hidden));
    return box;
  }

  /* -------------------------------------------------- build */
  function render(sectionFor, notice) {
    var story, problem = null;
    try {
      story = readJson("nh-training-story");
      models = readJson("nh-training-models");
      validate(story);
    } catch (err) {
      problem = err && err.message ? err.message : String(err);
    }
    if (problem) {
      notice.textContent = "The Training story could not be shown: " + problem + ".";
      notice.hidden = false;
      notice.setAttribute("data-story-error", "");
      return null;
    }
    var stored = storedProvider();
    provider = models.providers.indexOf(stored) !== -1 ? stored : story.defaultProvider;
    story.stages.forEach(function (st, i) {
      var section = sectionFor(st.id);
      var box = section && section.querySelector(".container");
      if (!box) return;
      if (st.kind === "intro") return;
      var nextNav = null;
      var heading = box.querySelector("h1, h2");
      var host = box.querySelector("[data-ss-id]");
      var banner = bannerFor(st, heading);
      box.insertBefore(banner, box.firstChild);
      if (st.kind === "play") {
        banner.appendChild(calloutFor(st));
        var after = el("p", "tr-after", st.after);
        if (host && host.nextSibling) box.insertBefore(after, host.nextSibling); else box.insertBefore(after, nextNav);
      } else {
        var grid = el("div", "tr-work");
        var report = sessionFor(st);
        var main = el("div", "tr-main");
        main.appendChild(report.article);
        var side = el("div", "tr-side");
        side.appendChild(filesFor(st));
        var activity = activityFor(st);
        side.appendChild(activity);
        var more = el("div", "tr-session tr-session-more");
        more.setAttribute("aria-label", "Agent session for " + st.command + ", continued");
        more.hidden = true;
        side.appendChild(more);
        grid.appendChild(main);
        grid.appendChild(side);
        box.insertBefore(grid, nextNav);
        var w = {
          id: st.id, grid: grid, main: main, article: report.article, side: side, activity: activity,
          more: more, parts: report.parts, details: report.article.querySelector(".tr-details"),
          cmd: report.cmd, run: report.run, timers: [], played: false
        };
        report.run.addEventListener("click", (function (work) {
          return function () { if (work.article.hasAttribute("data-typing")) finish(work); else type(work); };
        })(w));
        works.push(w);
      }
    });
    var timer = null;
    window.addEventListener("resize", function () {
      window.clearTimeout(timer);
      timer = window.setTimeout(function () { works.forEach(rebalance); }, 120);
    });
    return {
      story: story,
      provider: function () { return provider; },
      setProvider: setProvider,
      rebalance: function (id) { works.forEach(function (w) { if (!id || w.id === id) rebalance(w); }); },
      play: play,
      typing: function (on) { if (on != null) autoType = !!on && !REDUCED_MOTION; return autoType; },
      replay: function (id) { works.forEach(function (w) { if (w.id === id) type(w); }); },
      skip: function (id) { works.forEach(function (w) { if (!id || w.id === id) finish(w); }); }
    };
  }

  return { render: render };
})();
