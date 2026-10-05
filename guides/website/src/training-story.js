/* ===================================================================== Training story renderer (v4.13.10 R4)
   Reads the story (#nh-training-story) and the stamped model map (#nh-training-models) and
   builds each stage: the step banner with its model badge, the play callouts, and, for every
   agent step, an emulated IDE: a project explorer, an editor, and a chat whose prompt, model
   tier, and effort are preset for the step. Send runs the step: the agent's reasoning steps
   appear one by one (reads open files, writes type new ones, edits change lines live, runs show
   their output), then a structured Markdown reply. Text is only ever set with textContent; the
   small Markdown renderer builds elements, never HTML strings. A story that is missing a
   required field renders nothing and names the field in the page notice instead. Inlined into
   training.html by scripts/stamp_guide_shared.py: edit this file, not the page.
   ===================================================================== */
window.NexusTrainingStory = (function () {
  "use strict";

  var PROVIDER_KEY = "nh-training-provider";
  var REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var STEP_KINDS = { read: "Read", search: "Search", think: "Think", write: "Write", edit: "Edit", run: "Run" };

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
    need(need(story, "story", "project", "object"), "story.project", "files", "array");
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
        need(need(st, p, "prompt", "object"), p + ".prompt", "command", "string");
        var badge = need(st, p, "badge", "object");
        ["tier", "effort", "reason"].forEach(function (k) { need(badge, p + ".badge", k, "string"); });
        need(st, p, "steps", "array").forEach(function (s, j) {
          need(s, p + ".steps[" + j + "]", "kind", "string");
          need(s, p + ".steps[" + j + "]", "label", "string");
          if (!STEP_KINDS[s.kind]) throw new Error("field " + p + ".steps[" + j + "].kind has an unknown value " + JSON.stringify(s.kind));
        });
        need(st, p, "reply", "string");
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

  /* -------------------------------------------------- banner, badge, callout */
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

  /* -------------------------------------------------- Markdown, as elements (never HTML strings) */
  function inline(parent, text) {
    var parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/);
    parts.forEach(function (part) {
      if (!part) return;
      if (part.charAt(0) === "`" && part.length > 2) parent.appendChild(el("code", null, part.slice(1, -1)));
      else if (part.indexOf("**") === 0 && part.length > 4) parent.appendChild(el("strong", null, part.slice(2, -2)));
      else parent.appendChild(document.createTextNode(part));
    });
    return parent;
  }
  function markdown(text) {
    var out = [], lines = text.split("\n"), i = 0, para = [];
    function flush() { if (para.length) { out.push(inline(el("p"), para.join(" "))); para = []; } }
    while (i < lines.length) {
      var line = lines[i], m;
      if (/^```/.test(line)) {
        flush();
        var lang = line.slice(3).trim(), body = [];
        i += 1;
        while (i < lines.length && !/^```/.test(lines[i])) { body.push(lines[i]); i += 1; }
        var pre = el("pre", "md-code");
        if (lang) pre.setAttribute("data-lang", lang);
        pre.appendChild(el("code", null, body.join("\n")));
        out.push(pre);
        i += 1;
        continue;
      }
      if ((m = /^(#{2,4})\s+(.*)$/.exec(line))) {
        flush();
        out.push(inline(el(m[1].length === 2 ? "h3" : "h4", "md-h"), m[2]));
        i += 1;
        continue;
      }
      if (/^\|/.test(line)) {
        flush();
        var rows = [];
        while (i < lines.length && /^\|/.test(lines[i])) { rows.push(lines[i]); i += 1; }
        var table = el("table", "md-table"), cells = function (r) { return r.replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); }); };
        var thead = el("thead"), tr = el("tr");
        cells(rows[0]).forEach(function (c) { tr.appendChild(inline(el("th"), c)); });
        thead.appendChild(tr);
        table.appendChild(thead);
        var tbody = el("tbody");
        rows.slice(2).forEach(function (r) { var row = el("tr"); cells(r).forEach(function (c) { row.appendChild(inline(el("td"), c)); }); tbody.appendChild(row); });
        table.appendChild(tbody);
        out.push(table);
        continue;
      }
      if ((m = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(line))) {
        flush();
        var ordered = /\d/.test(m[2]);
        var list = el(ordered ? "ol" : "ul", "md-list"), last = null;
        while (i < lines.length && (m = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(lines[i]))) {
          if (m[1].length >= 2 && last) {
            var sub = last.querySelector("ul, ol") || last.appendChild(el(/\d/.test(m[2]) ? "ol" : "ul", "md-list"));
            sub.appendChild(inline(el("li"), m[3]));
          } else {
            last = inline(el("li"), m[3]);
            list.appendChild(last);
          }
          i += 1;
        }
        out.push(list);
        continue;
      }
      if (!line.trim()) { flush(); i += 1; continue; }
      para.push(line.trim());
      i += 1;
    }
    flush();
    return out;
  }

  /* -------------------------------------------------- code view: lines, light colouring, diffs */
  var KEYWORDS = /\b(import|export|from|function|return|const|let|var|if|else|for|of|test|expect|true|false|new)\b/;
  function colour(row, text, path) {
    if (/\.md$/.test(path)) {
      if (/^#{1,6}\s/.test(text)) { row.appendChild(el("span", "tk-h", text)); return; }
      if (/^\s*([-*]|\d+\.)\s/.test(text)) { var mk = /^(\s*(?:[-*]|\d+\.)\s)(.*)$/.exec(text); row.appendChild(el("span", "tk-p", mk[1])); inline(row, mk[2]); return; }
      inline(row, text);
      return;
    }
    if (/\.json$/.test(path)) {
      text.split(/("[^"]*")/).forEach(function (part, k) { if (part) row.appendChild(k % 2 ? el("span", "tk-s", part) : document.createTextNode(part)); });
      return;
    }
    var comment = text.indexOf("//");
    var code = comment >= 0 ? text.slice(0, comment) : text;
    code.split(/('[^']*'|"[^"]*"|\b\d+\b|\b[A-Za-z_]+\b)/).forEach(function (part) {
      if (!part) return;
      var cls = /^['"]/.test(part) ? "tk-s" : /^\d+$/.test(part) ? "tk-n" : KEYWORDS.test(part) && part.replace(KEYWORDS, "") === "" ? "tk-k" : null;
      row.appendChild(cls ? el("span", cls, part) : document.createTextNode(part));
    });
    if (comment >= 0) row.appendChild(el("span", "tk-c", text.slice(comment)));
  }
  /* Line diff (longest common subsequence): ops of "=", "-", "+". */
  function diff(a, b) {
    var n = a.length, m = b.length, dp = [];
    for (var i = 0; i <= n; i++) { dp.push(new Array(m + 1).fill(0)); }
    for (i = n - 1; i >= 0; i--) for (var j = m - 1; j >= 0; j--) dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
    var ops = [];
    i = 0; j = 0;
    while (i < n && j < m) {
      if (a[i] === b[j]) { ops.push(["=", a[i]]); i += 1; j += 1; }
      else if (dp[i + 1][j] >= dp[i][j + 1]) { ops.push(["-", a[i]]); i += 1; }
      else { ops.push(["+", b[j]]); j += 1; }
    }
    while (i < n) { ops.push(["-", a[i]]); i += 1; }
    while (j < m) { ops.push(["+", b[j]]); j += 1; }
    return ops;
  }

  /* -------------------------------------------------- one IDE per agent step */
  var sessions = [];
  function treeOf(files) {
    var root = { dirs: {}, files: [] };
    Object.keys(files).sort().forEach(function (path) {
      var parts = path.split("/"), node = root;
      for (var k = 0; k < parts.length - 1; k++) node = node.dirs[parts[k]] = node.dirs[parts[k]] || { dirs: {}, files: [] };
      node.files.push({ name: parts[parts.length - 1], path: path });
    });
    return root;
  }

  function ideFor(st, before) {
    var s = { st: st, before: before, files: {}, state: "ready", timers: [], open: [], status: {} };
    Object.keys(before).forEach(function (p) { s.files[p] = before[p]; });
    var ide = el("div", "ide");
    ide.setAttribute("data-state", "ready");
    ide.setAttribute("role", "group");
    ide.setAttribute("aria-label", "Emulated IDE for " + st.prompt.command);
    var bar = el("div", "ide-bar");
    var dots = el("span", "ide-dots");
    dots.setAttribute("aria-hidden", "true");
    dots.appendChild(el("i")); dots.appendChild(el("i")); dots.appendChild(el("i"));
    bar.appendChild(dots);
    bar.appendChild(el("span", "ide-title", "sky-sentinel"));
    s.statusEl = el("span", "ide-status", "Ready");
    bar.appendChild(s.statusEl);
    ide.appendChild(bar);
    var body = el("div", "ide-body");

    /* explorer */
    var explorer = el("nav", "ide-explorer");
    explorer.setAttribute("aria-label", "Project files");
    explorer.appendChild(el("p", "ide-head", "Explorer"));
    s.tree = el("ul", "ide-tree");
    explorer.appendChild(s.tree);
    body.appendChild(explorer);

    /* editor */
    var editor = el("div", "ide-editor");
    s.tabs = el("div", "ide-tabs");
    s.tabs.setAttribute("role", "tablist");
    s.tabs.setAttribute("aria-label", "Open files");
    editor.appendChild(s.tabs);
    s.code = el("div", "ide-code");
    s.code.setAttribute("role", "tabpanel");
    s.lines = el("ol", "ide-lines");
    s.code.appendChild(s.lines);
    editor.appendChild(s.code);
    body.appendChild(editor);

    /* chat */
    var chat = el("div", "ide-chat");
    var head = el("div", "ide-chat-head");
    var picker = el("div", "ide-model");
    picker.setAttribute("aria-label", "Model for this step, preset");
    var name = el("span", "ide-model-name");
    picker.appendChild(name);
    picker.appendChild(el("span", "ide-chip", st.badge.tier));
    picker.appendChild(el("span", "ide-chip", st.badge.effort + " effort"));
    var lock = el("span", "ide-lock", "Preset");
    lock.setAttribute("title", "The model and effort are preset for this step of the workflow");
    picker.appendChild(lock);
    head.appendChild(picker);
    chat.appendChild(head);
    badges.push({ tier: st.badge.tier, model: name, buttons: [] });
    s.log = el("div", "ide-log");
    s.log.setAttribute("aria-live", "polite");
    s.log.appendChild(el("p", "ide-note", "New agent session in sky-sentinel. The prompt below is preset for this step: press Send to run it."));
    chat.appendChild(s.log);
    var composer = el("div", "ide-composer");
    var input = el("div", "ide-input");
    input.setAttribute("role", "textbox");
    input.setAttribute("aria-readonly", "true");
    input.setAttribute("aria-label", "Prompt for this step, preset");
    input.appendChild(el("span", "ide-cmd", st.prompt.command));
    if (st.prompt.argument) { input.appendChild(document.createTextNode(" ")); input.appendChild(el("span", "ide-arg", st.prompt.argument)); }
    composer.appendChild(input);
    s.send = el("button", "ide-send", "Send");
    s.send.type = "button";
    s.send.addEventListener("click", function () {
      if (s.state === "running") finish(s);
      else if (s.state === "done") { reset(s); run(s, false); }
      else run(s, false);
    });
    composer.appendChild(s.send);
    chat.appendChild(composer);
    body.appendChild(chat);
    ide.appendChild(body);
    s.ide = ide;
    paintTree(s);
    var first = null;
    st.steps.some(function (x) { if (x.file && before[x.file] != null) { first = x.file; return true; } return false; });
    openFile(s, first || Object.keys(before).sort()[0], false);
    return s;
  }

  function paintTree(s) {
    s.tree.textContent = "";
    var root = treeOf(s.files);
    (function walk(node, parent, depth) {
      Object.keys(node.dirs).forEach(function (d) {
        var li = el("li", "ide-dir");
        var label = el("span", "ide-dir-name", d);
        label.style.setProperty("--d", depth);
        li.appendChild(label);
        var ul = el("ul");
        li.appendChild(ul);
        parent.appendChild(li);
        walk(node.dirs[d], ul, depth + 1);
      });
      node.files.forEach(function (f) {
        var li = el("li");
        var b = el("button", "ide-file", f.name);
        b.type = "button";
        b.style.setProperty("--d", depth);
        b.setAttribute("data-path", f.path);
        if (s.status[f.path]) { b.setAttribute("data-status", s.status[f.path]); b.appendChild(el("span", "ide-mark", s.status[f.path] === "created" ? "A" : "M")); }
        if (s.current === f.path) b.setAttribute("aria-current", "true");
        b.addEventListener("click", function () { if (s.state !== "running") openFile(s, f.path, false); });
        li.appendChild(b);
        parent.appendChild(li);
      });
    })(root, s.tree, 0);
  }

  function tabFor(s, path) {
    var tab = null;
    s.open.forEach(function (t) { if (t.path === path) tab = t; });
    if (!tab) {
      var b = el("button", "ide-tab", path.split("/").pop());
      b.type = "button";
      b.setAttribute("role", "tab");
      b.setAttribute("title", path);
      b.addEventListener("click", function () { if (s.state !== "running") openFile(s, path, false); });
      s.tabs.appendChild(b);
      tab = { path: path, button: b };
      s.open.push(tab);
      if (s.open.length > 4) { s.tabs.removeChild(s.open[0].button); s.open.shift(); }
    }
    s.open.forEach(function (t) { t.button.setAttribute("aria-selected", t.path === path ? "true" : "false"); });
    return tab;
  }

  function showLines(s, path, text, marks) {
    s.lines.textContent = "";
    (text || "").split("\n").forEach(function (line, k) {
      var li = el("li");
      if (marks && marks[k]) li.setAttribute("data-op", marks[k]);
      colour(li, line, path);
      s.lines.appendChild(li);
    });
  }

  function openFile(s, path, highlight) {
    if (!path) return;
    s.current = path;
    tabFor(s, path);
    s.code.setAttribute("aria-label", path);
    showLines(s, path, s.files[path], s.marks && s.marks[path]);
    var btns = s.tree.querySelectorAll(".ide-file");
    for (var k = 0; k < btns.length; k++) {
      var on = btns[k].getAttribute("data-path") === path;
      if (on) btns[k].setAttribute("aria-current", "true"); else btns[k].removeAttribute("aria-current");
      if (on && highlight) { btns[k].classList.remove("ide-flash"); void btns[k].offsetWidth; btns[k].classList.add("ide-flash"); }
    }
  }

  /* -------------------------------------------------- running a step */
  function at(s, ms, fn) { s.timers.push(window.setTimeout(fn, ms)); }
  function setState(s, state) {
    s.state = state;
    s.ide.setAttribute("data-state", state);
    s.statusEl.textContent = state === "running" ? "Agent working" : state === "done" ? "Done" : "Ready";
    s.send.textContent = state === "running" ? "Skip" : state === "done" ? "Run again" : "Send";
  }
  function reset(s) {
    s.timers.forEach(window.clearTimeout);
    s.timers = [];
    s.files = {};
    Object.keys(s.before).forEach(function (p) { s.files[p] = s.before[p]; });
    s.status = {};
    s.marks = {};
    s.log.textContent = "";
    s.log.appendChild(el("p", "ide-note", "New agent session in sky-sentinel. The prompt below is preset for this step: press Send to run it."));
    s.tabs.textContent = "";
    s.open = [];
    paintTree(s);
    setState(s, "ready");
  }
  function userMessage(s) {
    var msg = el("div", "ide-msg ide-msg--user");
    msg.appendChild(el("span", "ide-who", "You"));
    var p = el("p");
    p.appendChild(el("span", "ide-cmd", s.st.prompt.command));
    if (s.st.prompt.argument) { p.appendChild(document.createTextNode(" ")); p.appendChild(el("span", "ide-arg", s.st.prompt.argument)); }
    msg.appendChild(p);
    s.log.appendChild(msg);
  }
  function stepRow(s, step) {
    var li = el("li", "ide-step");
    li.setAttribute("data-kind", step.kind);
    li.appendChild(el("span", "ide-step-kind", STEP_KINDS[step.kind]));
    li.appendChild(el("span", "ide-step-label", step.label));
    if (step.output) {
      var out = el("pre", "ide-step-out");
      out.appendChild(el("code", null, step.output));
      li.appendChild(out);
    }
    return li;
  }
  function applyFile(s, path, after) {
    var existed = Object.prototype.hasOwnProperty.call(s.before, path);
    s.status[path] = existed ? "modified" : "created";
    var a = existed ? s.before[path].split("\n") : [], b = after.split("\n");
    var ops = diff(a, b), marks = [];
    ops.forEach(function (o) { if (o[0] !== "-") marks.push(o[0] === "+" ? "add" : null); });
    /* A new file is all new: change markers only make sense on an edited one. */
    s.marks[path] = existed ? marks : null;
    s.files[path] = after;
    return ops;
  }
  /* Writes type in line by line; edits strike removed lines, then type the new ones in place. */
  function animateFile(s, path, ops, start) {
    var t = start, shown = [];
    openFile(s, path, true);
    s.lines.textContent = "";
    var rows = ops.map(function (o) {
      var li = el("li");
      li.setAttribute("data-op", o[0] === "+" ? "add" : o[0] === "-" ? "del" : "ctx");
      colour(li, o[1], path);
      if (o[0] === "+") li.classList.add("ide-wait");
      s.lines.appendChild(li);
      return li;
    });
    var dels = rows.filter(function (r, k) { return ops[k][0] === "-"; });
    if (dels.length) { t += 450; at(s, t, function () { dels.forEach(function (r) { r.classList.add("ide-strike"); }); }); t += 650; }
    rows.forEach(function (r, k) {
      if (ops[k][0] !== "+") return;
      var dur = Math.max(70, Math.min(420, ops[k][1].length * 9));
      at(s, t, function () { r.classList.remove("ide-wait"); r.style.setProperty("--tr-d", dur + "ms"); r.classList.add("ide-type"); r.scrollIntoView && s.code.scrollTo({ top: Math.max(0, r.offsetTop - s.code.clientHeight / 2) }); });
      t += dur + 30;
    });
    at(s, t + 200, function () { openFile(s, path, false); });
    return t + 300;
  }

  function run(s, instant) {
    reset(s);
    setState(s, "running");
    s.log.textContent = "";
    userMessage(s);
    var work = el("div", "ide-msg ide-msg--agent");
    work.appendChild(el("span", "ide-who", "Agent"));
    var steps = el("ol", "ide-steps");
    steps.setAttribute("aria-label", "What the agent did, in order");
    work.appendChild(steps);
    s.log.appendChild(work);
    var quick = instant || REDUCED;
    var t = quick ? 0 : 500;
    s.st.steps.forEach(function (step) {
      var row = stepRow(s, step);
      var ops = null;
      if ((step.kind === "write" || step.kind === "edit") && step.file) ops = applyFileLater(s, step);
      if (quick) {
        steps.appendChild(row);
        if (ops) { applyFile(s, step.file, step.content); }
        return;
      }
      at(s, t, function () {
        row.classList.add("is-running");
        steps.appendChild(row);
        scrollLog(s);
        if (step.kind === "read" && step.file) openFile(s, step.file, true);
      });
      var dur = { read: 750, search: 700, think: 1000, run: 1100, write: 400, edit: 400 }[step.kind];
      if (ops) {
        var o = null;
        at(s, t + 300, function () { o = applyFile(s, step.file, step.content); paintTree(s); });
        var startAt = t + 320;
        at(s, startAt, function () { animateFile(s, step.file, o, 0); });
        var lines = step.content.split("\n").length;
        dur = 700 + Math.min(4200, lines * 120);
      }
      t += dur;
      at(s, t, function () { row.classList.remove("is-running"); row.classList.add("is-done"); });
      t += 140;
    });
    function replyNow() {
      var reply = el("div", "ide-msg ide-msg--reply");
      var blocks = markdown(s.st.reply);
      s.log.appendChild(reply);
      if (quick) { blocks.forEach(function (b) { reply.appendChild(b); }); done(); return; }
      blocks.forEach(function (b, k) {
        at(s, k * 160, function () { b.classList.add("ide-type"); b.style.setProperty("--tr-d", "260ms"); reply.appendChild(b); scrollLog(s); });
      });
      at(s, blocks.length * 160 + 200, done);
    }
    function done() {
      paintTree(s);
      var last = null;
      s.st.steps.forEach(function (x) { if ((x.kind === "write" || x.kind === "edit") && x.file) last = x.file; });
      if (last) openFile(s, last, false);
      var foot = el("p", "ide-foot", s.st.steps.length + " steps, " + Object.keys(s.status).length + " file" + (Object.keys(s.status).length === 1 ? "" : "s") + " changed");
      s.log.appendChild(foot);
      setState(s, "done");
      if (!quick) scrollLog(s);
    }
    if (quick) { paintTree(s); replyNow(); return; }
    at(s, t + 200, replyNow);
  }
  function applyFileLater(s, step) { return step; }
  function scrollLog(s) { s.log.scrollTop = s.log.scrollHeight; }
  function finish(s) {
    s.timers.forEach(window.clearTimeout);
    s.timers = [];
    run(s, true);
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
    /* The project evolves through the story: each step starts from what earlier steps wrote. */
    var tree = {};
    story.project.files.forEach(function (f) { tree[f.path] = f.code; });
    story.stages.forEach(function (st) {
      var section = sectionFor(st.id);
      var box = section && section.querySelector(".container");
      if (!box) return;
      if (st.kind === "intro") return;
      var heading = box.querySelector("h1, h2");
      var host = box.querySelector("[data-ss-id]");
      var banner = bannerFor(st, heading);
      box.insertBefore(banner, box.firstChild);
      if (st.kind === "play") {
        banner.appendChild(calloutFor(st));
        var after = el("p", "tr-after", st.after);
        if (host && host.nextSibling) box.insertBefore(after, host.nextSibling); else box.appendChild(after);
        return;
      }
      var before = {};
      Object.keys(tree).forEach(function (p) { before[p] = tree[p]; });
      var s = ideFor(st, before);
      s.id = st.id;
      box.appendChild(s.ide);
      sessions.push(s);
      st.steps.forEach(function (x) { if ((x.kind === "write" || x.kind === "edit") && x.file) tree[x.file] = x.content; });
    });
    badges.forEach(paintBadge);
    function find(id) { var f = null; sessions.forEach(function (x) { if (x.id === id) f = x; }); return f; }
    return {
      story: story,
      provider: function () { return provider; },
      setProvider: setProvider,
      rebalance: function () {},
      play: function () {},
      /* For scripts and tests: run a step (instantly with { instant: true }), read its state, or reset it. */
      send: function (id, opts) { var x = find(id); if (x) run(x, !!(opts && opts.instant)); return !!x; },
      state: function (id) { var x = find(id); return x ? x.state : null; },
      reset: function (id) { var x = find(id); if (x) reset(x); }
    };
  }

  return { render: render };
})();
