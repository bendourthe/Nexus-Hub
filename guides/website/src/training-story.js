/* ===================================================================== Training story renderer (v4.13.10 R8)
   Reads the story (#nh-training-story) and the stamped model map (#nh-training-models) and
   builds the page's parts: a plain head for each part with the Development Workflow strip, and,
   for every workflow step, an IDE that plays the step as an animation. A cursor picks the model
   and effort in the chat, the command types in, Send is pressed, the agent works (reads open
   files, writes type them in, edits change lines in place, runs show output), then a Markdown
   reply. In /implement the usage bar reaches the provider's limit and the agent hands off to a
   second provider. Each player has play, replay, a seek bar, and speed; every frame is rebuilt
   from the script for its time, so seeking always lands on the same frame. Text is only ever
   set with textContent; the Markdown renderer builds elements, never HTML strings. A story
   missing a required field renders nothing and names the field in the page notice. Inlined
   into training.html by scripts/stamp_guide_shared.py: edit this file, not the page.
   ===================================================================== */
window.NexusTrainingStory = (function () {
  "use strict";

  var REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var STEP_KINDS = { read: "Read", search: "Search", think: "Think", write: "Write", edit: "Edit", run: "Run" };
  var TIERS = ["frontier", "strong", "standard", "fast"];
  var EFFORTS = ["low", "medium", "high", "max"];
  var SPEEDS = [0.5, 1, 2];

  /* Every text block carries its role from shared/type.css. */
  function ty(node, role) { node.setAttribute("data-ty", role); return node; }
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function svg(paths, cls) {
    var NS = "http://www.w3.org/2000/svg", s = document.createElementNS(NS, "svg");
    s.setAttribute("viewBox", "0 0 24 24");
    s.setAttribute("aria-hidden", "true");
    if (cls) s.setAttribute("class", cls);
    paths.forEach(function (d) { var p = document.createElementNS(NS, "path"); p.setAttribute("d", d); s.appendChild(p); });
    return s;
  }
  function readJson(id) {
    var node = document.getElementById(id);
    if (!node) throw new Error("the page has no #" + id + " block");
    return JSON.parse(node.textContent);
  }
  function cap(w) { return /^\d/.test(w) ? w : w.charAt(0).toUpperCase() + w.slice(1); }
  /* Model ids read as product names: claude-sonnet-5-5 -> Claude Sonnet 5.5, gpt-6.1-sol -> GPT-6.1 Sol. */
  function modelName(id) {
    if (!id) return "Unknown model";
    var p = String(id).split("-");
    if (p[0] === "claude") {
      var nums = p.slice(2).filter(function (x) { return /^\d+$/.test(x); });
      return "Claude " + cap(p[1]) + (nums.length ? " " + nums.join(".") : "");
    }
    if (p[0] === "gpt") return "GPT-" + p[1] + (p.length > 2 ? " " + p.slice(2).map(cap).join(" ") : "");
    return p.map(cap).join(" ");
  }
  function clock(ms) { var s = Math.max(0, Math.round(ms / 1000)); return Math.floor(s / 60) + ":" + (s % 60 < 10 ? "0" : "") + (s % 60); }
  function ease(p) { return p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; }

  /* -------------------------------------------------- validation (the fields rendering relies on) */
  function need(obj, path, key, kind) {
    var v = obj == null ? undefined : obj[key];
    var ok = kind === "array" ? Array.isArray(v) && v.length > 0 : kind === "string" ? typeof v === "string" && v.length > 0 : v != null && typeof v === "object";
    if (!ok) throw new Error("field " + path + "." + key + " is missing or empty");
    return v;
  }
  function validate(story) {
    need(story, "story", "stages", "array");
    need(story, "story", "workflow", "array");
    need(need(story, "story", "project", "object"), "story.project", "files", "array");
    story.stages.forEach(function (st, i) {
      var p = "stages[" + i + "]";
      need(st, p, "id", "string");
      need(st, p, "kind", "string");
      if (st.kind === "intro") return;
      var head = need(st, p, "head", "object");
      ["title", "now"].forEach(function (k) { need(head, p + ".head", k, "string"); });
      if (st.kind === "play") {
        need(st, p, "game", "string");
        need(need(st, p, "notes", "object"), p + ".notes", "items", "array");
      } else if (st.kind === "session") {
        need(st, p, "step", "string");
        need(st, p, "why", "string");
        need(st, p, "script", "array").forEach(function (a, j) {
          var q = p + ".script[" + j + "]";
          need(a, q, "do", "string");
          if (a.do === "pick") { if (TIERS.indexOf(a.tier) === -1) throw new Error("field " + q + ".tier has an unknown value " + JSON.stringify(a.tier)); }
          else if (a.do === "prompt") need(a, q, "command", "string");
          else if (a.do === "work") need(a, q, "steps", "array").forEach(function (s, k) {
            need(s, q + ".steps[" + k + "]", "label", "string");
            if (!STEP_KINDS[s.kind]) throw new Error("field " + q + ".steps[" + k + "].kind has an unknown value " + JSON.stringify(s.kind));
          });
          else if (a.do === "reply" || a.do === "limit" || a.do === "paste") need(a, q, "text", "string");
          else if (a.do !== "copy") throw new Error("field " + q + ".do has an unknown value " + JSON.stringify(a.do));
        });
      } else {
        throw new Error("field " + p + ".kind has an unknown value " + JSON.stringify(st.kind));
      }
    });
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
          var text2 = m[3], box = /^\[( |x)\]\s+(.*)$/.exec(text2), item;
          if (box) { item = el("li", "md-check"); item.setAttribute("data-done", box[1] === "x" ? "true" : "false"); inline(item, box[2]); }
          else item = inline(el("li"), text2);
          if (m[1].length >= 2 && last) {
            var sub = last.querySelector("ul, ol") || last.appendChild(el(/\d/.test(m[2]) ? "ol" : "ul", "md-list"));
            sub.appendChild(item);
          } else {
            last = item;
            list.appendChild(item);
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

  /* -------------------------------------------------- code view: light colouring and line diffs */
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
  function langOf(path) { return /\.md$/.test(path) ? "Markdown" : /\.json$/.test(path) ? "JSON" : /\.js$/.test(path) ? "JavaScript" : "Plain Text"; }

  /* -------------------------------------------------- the Development Workflow strip */
  function flowFor(workflow, current, mode) {
    var ol = el("ol", "tr-flow");
    ol.setAttribute("aria-label", "Development Workflow");
    var at = -1;
    workflow.forEach(function (w, k) { if (w.step === current) at = k; });
    workflow.forEach(function (w, k) {
      var li = el("li");
      var state = mode === "done" ? "done" : mode === "before" ? "next" : k < at ? "done" : k === at ? "now" : "next";
      li.setAttribute("data-state", state);
      li.setAttribute("data-step", w.step);
      if (state === "now") li.setAttribute("aria-current", "step");
      var a = el("a");
      a.href = "#" + encodeURIComponent(w.step);
      a.appendChild(el("span", "tr-flow-n", String(k + 1)));
      a.appendChild(el("code", null, w.command));
      a.appendChild(el("small", null, w.label));
      li.appendChild(a);
      ol.appendChild(li);
    });
    return ol;
  }
  function headFor(st, heading, workflow) {
    var header = el("header", "tr-head");
    if (st.kind === "session") header.appendChild(flowFor(workflow, st.step));
    else header.appendChild(flowFor(workflow, null, st.game === "fixed" ? "done" : "before"));
    if (st.head.kicker) header.appendChild(el("p", "tr-kicker", st.head.kicker));
    heading.textContent = st.head.title;
    heading.classList.add("tr-title");
    header.appendChild(heading);
    header.appendChild(ty(el("p", "tr-now", st.head.now), "lead"));
    return header;
  }
  function notesFor(st) {
    var box = el("div", "tr-notes");
    box.setAttribute("data-tone", st.game === "fixed" ? "ok" : "bug");
    box.appendChild(ty(el("h3", "tr-notes-title", st.notes.title), "h3"));
    var ul = el("ul", "tr-notes-list");
    st.notes.items.forEach(function (t) { ul.appendChild(ty(el("li", null, t), "body")); });
    box.appendChild(ul);
    if (st.notes.hidden) box.appendChild(ty(el("p", "tr-notes-hidden", st.notes.hidden), "body"));
    return box;
  }

  /* -------------------------------------------------- IDE shell */
  var ICONS = {
    files: ["M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z", "M14 3v5h5"],
    search: ["M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z", "M20 20l-4.8-4.8"],
    branch: ["M6 3v12", "M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z", "M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z", "M18 9a9 9 0 0 1-9 9"],
    run: ["M7 4v16l13-8z"],
    blocks: ["M4 4h7v7H4z", "M13 13h7v7h-7z", "M4 13h7v7H4z", "M15 3l6 6-6 6-6-6z"],
    send: ["M4 12l16-8-6 16-2-7z"],
    chev: ["M7 10l5 5 5-5"],
    lock: ["M7 11V8a5 5 0 0 1 10 0v3", "M5 11h14v10H5z"]
  };
  function treeOf(files) {
    var root = { dirs: {}, files: [] };
    Object.keys(files).sort().forEach(function (path) {
      var parts = path.split("/"), node = root;
      for (var k = 0; k < parts.length - 1; k++) node = node.dirs[parts[k]] = node.dirs[parts[k]] || { dirs: {}, files: [] };
      node.files.push({ name: parts[parts.length - 1], path: path });
    });
    return root;
  }
  function picker(cls, label) {
    var b = el("span", "ide-pick " + cls);
    b.setAttribute("aria-label", label);
    var name = el("span", "ide-pick-name");
    b.appendChild(name);
    b.appendChild(svg(ICONS.chev, "ide-chev"));
    return { box: b, name: name };
  }
  function ideShell(st, project) {
    var s = { id: st.id, st: st };
    var wrap = el("div", "ide-wrap");
    var ide = el("div", "ide");
    ide.setAttribute("role", "region");
    ide.setAttribute("aria-label", "Agent session for " + st.step + ", played as an animation");
    var title = el("div", "ide-titlebar");
    title.setAttribute("aria-hidden", "true");
    title.appendChild(el("span", "ide-menus", "File  Edit  Selection  View  Go  Run  Terminal  Help"));
    title.appendChild(el("span", "ide-search", project));
    title.appendChild(el("span", "ide-win"));
    ide.appendChild(title);

    var main = el("div", "ide-main");
    var act = el("nav", "ide-activity");
    act.setAttribute("aria-hidden", "true");
    ["files", "search", "branch", "run", "blocks"].forEach(function (k, i) { var b = el("span", "ide-act" + (i === 0 ? " is-on" : "")); b.appendChild(svg(ICONS[k])); act.appendChild(b); });
    main.appendChild(act);

    var explorer = el("aside", "ide-explorer");
    explorer.setAttribute("aria-label", "Project files");
    explorer.appendChild(el("p", "ide-pane-h", "Explorer"));
    explorer.appendChild(el("p", "ide-proj", project.toUpperCase()));
    s.tree = el("ul", "ide-tree");
    explorer.appendChild(s.tree);
    main.appendChild(explorer);

    var editor = el("section", "ide-editor");
    editor.setAttribute("aria-label", "Editor");
    s.tabs = el("div", "ide-tabs");
    s.crumbs = el("div", "ide-crumbs");
    var code = el("div", "ide-code");
    s.lines = el("ol", "ide-lines");
    code.appendChild(s.lines);
    s.code = code;
    editor.appendChild(s.tabs);
    editor.appendChild(s.crumbs);
    editor.appendChild(code);
    main.appendChild(editor);

    var chat = el("section", "ide-chat");
    chat.setAttribute("aria-label", "Agent chat");
    var ch = el("div", "ide-chat-h");
    ch.appendChild(el("span", "ide-chat-t", "Chat"));
    var usage = el("div", "ide-usage");
    usage.setAttribute("role", "meter");
    usage.setAttribute("aria-valuemin", "0");
    usage.setAttribute("aria-valuemax", "100");
    s.usageName = el("span", "ide-usage-name");
    var bar = el("span", "ide-usage-bar");
    s.usageFill = el("i");
    bar.appendChild(s.usageFill);
    s.usagePct = el("span", "ide-usage-pct");
    usage.appendChild(s.usageName);
    usage.appendChild(bar);
    usage.appendChild(s.usagePct);
    s.usage = usage;
    ch.appendChild(usage);
    chat.appendChild(ch);
    s.log = el("div", "ide-log");
    chat.appendChild(s.log);
    var composer = el("div", "ide-composer");
    s.input = el("div", "ide-input");
    s.input.setAttribute("role", "textbox");
    s.input.setAttribute("aria-readonly", "true");
    s.input.setAttribute("aria-label", "Prompt, preset for this step");
    composer.appendChild(s.input);
    var row = el("div", "ide-bar");
    var mode = picker("ide-pick--mode", "Chat mode");
    mode.name.textContent = "Agent";
    row.appendChild(mode.box);
    s.model = picker("ide-pick--model", "Model");
    s.effort = picker("ide-pick--effort", "Effort");
    row.appendChild(s.model.box);
    row.appendChild(s.effort.box);
    var lock = el("span", "ide-lock");
    lock.appendChild(svg(ICONS.lock));
    lock.appendChild(document.createTextNode("Preset"));
    row.appendChild(lock);
    s.send = el("span", "ide-send");
    s.send.setAttribute("aria-label", "Send");
    s.send.appendChild(svg(ICONS.send));
    row.appendChild(s.send);
    composer.appendChild(row);
    chat.appendChild(composer);
    main.appendChild(chat);
    ide.appendChild(main);

    var status = el("div", "ide-status");
    status.setAttribute("aria-hidden", "true");
    status.appendChild(el("span", null, "main"));
    status.appendChild(el("span", null, "0 problems"));
    s.statusPos = el("span", "ide-status-r");
    s.statusLang = el("span");
    s.statusModel = el("span");
    status.appendChild(s.statusPos);
    status.appendChild(s.statusLang);
    status.appendChild(s.statusModel);
    ide.appendChild(status);

    s.menu = el("div", "ide-menu");
    s.menu.setAttribute("aria-hidden", "true");
    s.menu.hidden = true;
    ide.appendChild(s.menu);
    s.toast = el("div", "ide-toast", "Copied to clipboard");
    s.toast.hidden = true;
    ide.appendChild(s.toast);
    /* The highlight: an outline with a label that marks what the agent just produced. */
    s.focus = el("div", "ide-focus");
    s.focus.setAttribute("aria-hidden", "true");
    s.focusLabel = el("span", "ide-focus-l");
    s.focus.appendChild(s.focusLabel);
    s.focus.hidden = true;
    ide.appendChild(s.focus);
    s.cursor = el("div", "ide-cursor");
    s.cursor.setAttribute("aria-hidden", "true");
    s.cursor.appendChild(svg(["M5 3l14 9-6.5 1.6L9 20z"]));
    ide.appendChild(s.cursor);

    s.ide = ide;
    wrap.appendChild(ide);
    wrap.appendChild(controlsFor(s));
    s.wrap = wrap;
    return s;
  }

  /* -------------------------------------------------- the player's controls */
  function controlsFor(s) {
    var bar = el("div", "ide-player");
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Animation controls");
    s.playBtn = el("button", "ide-ctl ide-ctl--play");
    s.playBtn.type = "button";
    s.playIcon = el("span", "ide-ctl-ic");
    s.playBtn.appendChild(s.playIcon);
    s.playBtn.addEventListener("click", function () { if (s.playing) pause(s); else { if (s.t >= s.duration) seek(s, 0); play(s); } });
    var again = el("button", "ide-ctl ide-ctl--replay");
    again.type = "button";
    again.setAttribute("aria-label", "Replay from the start");
    again.appendChild(svg(["M4 4v6h6", "M5.5 15a7.5 7.5 0 1 0 1.8-7.8L4 10"]));
    again.addEventListener("click", function () { seek(s, 0); play(s); });
    s.seekBar = el("input", "ide-seek");
    s.seekBar.type = "range";
    s.seekBar.min = "0";
    s.seekBar.step = "10";
    s.seekBar.setAttribute("aria-label", "Position in the animation");
    s.seekBar.addEventListener("input", function () { s.started = true; s.autoPaused = false; seek(s, parseFloat(s.seekBar.value) || 0); });
    s.time = el("span", "ide-time");
    var speeds = el("div", "ide-speed");
    speeds.setAttribute("role", "group");
    speeds.setAttribute("aria-label", "Playback speed");
    s.speedBtns = SPEEDS.map(function (x) {
      var b = el("button", null, x + "x");
      b.type = "button";
      b.setAttribute("data-speed", String(x));
      b.addEventListener("click", function () { setSpeed(s, x); });
      speeds.appendChild(b);
      return b;
    });
    bar.appendChild(s.playBtn);
    bar.appendChild(again);
    bar.appendChild(s.seekBar);
    bar.appendChild(s.time);
    bar.appendChild(speeds);
    return bar;
  }
  function paintControls(s) {
    s.playBtn.setAttribute("aria-label", s.playing ? "Pause" : s.t >= s.duration ? "Play again" : "Play");
    s.playBtn.setAttribute("data-state", s.playing ? "playing" : "paused");
    s.seekBar.value = String(Math.round(s.t));
    s.seekBar.setAttribute("aria-valuetext", clock(s.t) + " of " + clock(s.duration));
    s.time.textContent = clock(s.t) + " / " + clock(s.duration);
    s.speedBtns.forEach(function (b) { b.setAttribute("aria-pressed", parseFloat(b.getAttribute("data-speed")) === s.speed ? "true" : "false"); });
    s.wrap.setAttribute("data-state", s.t >= s.duration ? "done" : s.t > 0 ? "running" : "ready");
  }

  /* -------------------------------------------------- the frame state */
  function setPicker(s, provider, tier, effort) {
    var id = tier && models.tiers[tier] ? models.tiers[tier][provider] : null;
    s.cur = { provider: provider, tier: tier, effort: effort, model: id };
    s.model.name.textContent = id ? modelName(id) : "Auto";
    s.effort.name.textContent = effort ? cap(effort) : "Medium";
    s.statusModel.textContent = id ? modelName(id) : "";
  }
  function setUsage(s, provider, pct) {
    pct = Math.max(0, Math.min(100, Math.round(pct)));
    s.usageName.textContent = provider + " usage";
    s.usageFill.style.width = pct + "%";
    s.usagePct.textContent = pct + "%";
    s.usage.setAttribute("aria-valuenow", String(pct));
    s.usage.setAttribute("aria-label", provider + " usage, " + pct + " percent of the limit");
    s.usage.setAttribute("data-level", pct >= 100 ? "full" : pct >= 80 ? "high" : "ok");
    s.usageNow = { provider: provider, pct: pct };
  }
  function paintTree(s) {
    s.tree.textContent = "";
    function walk(node, ul, depth) {
      Object.keys(node.dirs).sort().forEach(function (name) {
        var li = el("li", "ide-dir");
        var row = el("span", "ide-row", name);
        row.style.paddingLeft = (10 + depth * 12) + "px";
        li.appendChild(row);
        var sub = el("ul");
        walk(node.dirs[name], sub, depth + 1);
        li.appendChild(sub);
        ul.appendChild(li);
      });
      node.files.forEach(function (f) {
        var li = el("li");
        var b = el("button", "ide-file", f.name);
        b.type = "button";
        b.style.paddingLeft = (10 + depth * 12) + "px";
        b.setAttribute("data-path", f.path);
        if (s.status[f.path]) { b.setAttribute("data-status", s.status[f.path] === "A" ? "created" : "modified"); b.appendChild(el("span", "ide-mark", s.status[f.path])); }
        if (f.path === s.view.path) b.setAttribute("aria-current", "true");
        b.addEventListener("click", function () { openFile(s, f.path); });
        li.appendChild(b);
        ul.appendChild(li);
      });
    }
    walk(treeOf(s.files), s.tree, 0);
  }
  function ensureTab(s, path) {
    if (s.tabList.indexOf(path) === -1) s.tabList.push(path);
    s.tabs.textContent = "";
    s.tabList.forEach(function (p) {
      var t = el("span", "ide-tab", p.split("/").pop());
      t.setAttribute("data-path", p);
      if (p === s.view.path) t.setAttribute("aria-selected", "true");
      if (s.status[p]) t.appendChild(el("span", "ide-mark", s.status[p]));
      s.tabs.appendChild(t);
    });
  }
  function showLines(s, path, rows) {
    s.lines.textContent = "";
    rows.forEach(function (r) {
      var li = el("li");
      if (r.op) li.setAttribute("data-op", r.op);
      if (r.cls) li.className = r.cls;
      colour(li, r.text, path);
      if (!r.text) li.appendChild(document.createTextNode("​"));
      s.lines.appendChild(li);
    });
    s.statusPos.textContent = "Ln " + Math.max(1, rows.length) + ", Col 1";
  }
  function viewFile(s, path) {
    if (s.view.path !== path) { s.view.path = path; s.view.key = null; }
    ensureTab(s, path);
    s.crumbs.textContent = path.split("/").join("  >  ");
    s.statusLang.textContent = langOf(path);
  }
  function openFile(s, path) {
    viewFile(s, path);
    var key = path + "#" + (s.files[path] || "").length;
    if (s.view.key !== key) {
      s.view.key = key;
      showLines(s, path, (s.files[path] || "").split("\n").map(function (t) { return { text: t }; }));
      s.code.scrollTop = 0;
      paintTree(s);
    }
  }
  function reset(s) {
    s.files = {};
    Object.keys(s.before).forEach(function (p) { s.files[p] = s.before[p]; });
    s.status = {};
    s.nodes = {};
    s.tabList = [];
    s.view = { path: null, key: null };
    s.log.textContent = "";
    s.log.appendChild(el("p", "ide-hint", "New agent session in " + s.project + ". The prompt and model are preset for this step."));
    s.input.textContent = "";
    s.input.appendChild(el("span", "ide-ph", "Ask the agent, or type / for a command"));
    s.menu.hidden = true;
    s.toast.hidden = true;
    s.focus.hidden = true;
    s.cursor.style.opacity = "0";
    s.cursor.classList.remove("is-down");
    s.cursorKey = "start";
    s.seen = {};
    setPicker(s, s.init.provider, s.init.tier, s.init.effort);
    setUsage(s, s.init.provider, s.init.usage);
    s.ide.setAttribute("data-provider", s.init.provider);
    openFile(s, s.firstFile);
    s.t = 0;
    s.idx = 0;
  }
  function ensure(s, key, make) { if (!s.nodes[key]) s.nodes[key] = make(); return s.nodes[key]; }
  function scrollLog(s) { s.log.scrollTop = s.log.scrollHeight; }

  /* -------------------------------------------------- cursor */
  function point(s, key) {
    var root = s.ide.getBoundingClientRect(), target = null;
    if (key === "start") return { x: root.width - 40, y: root.height - 30 };
    if (key === "model") target = s.model.box;
    else if (key === "effort") target = s.effort.box;
    else if (key === "input") target = s.input;
    else if (key === "send") target = s.send;
    else if (key === "copy") { var cs = s.log.querySelectorAll(".ide-copy"); target = cs.length ? cs[cs.length - 1] : s.send; }
    else if (key.indexOf("opt:") === 0) target = s.menu.querySelector('[data-value="' + key.slice(4) + '"]') || s.menu;
    /* A target that has gone (a closed menu's option) keeps the place the cursor last saw it, so
       the next move starts where the cursor stopped, never from the middle of the IDE. */
    s.seen = s.seen || {};
    if (!target || !target.getClientRects().length) return s.seen[key] || s.seen.last || { x: root.width - 40, y: root.height - 30 };
    var r = target.getBoundingClientRect();
    var x = key === "input" ? r.left + Math.min(60, r.width / 3) : r.left + r.width / 2;
    s.seen[key] = s.seen.last = { x: x - root.left, y: r.top + r.height / 2 - root.top };
    return s.seen[key];
  }
  function placeCursor(s, a, b, p) {
    var A = point(s, a), B = point(s, b), q = ease(p);
    s.cursor.style.opacity = "1";
    s.cursor.style.transform = "translate(" + Math.round(A.x + (B.x - A.x) * q) + "px," + Math.round(A.y + (B.y - A.y) * q) + "px)";
  }

  /* -------------------------------------------------- the model and effort menu */
  function openMenu(s, kind, at, provider) {
    s.menu.textContent = "";
    s.menu.setAttribute("data-kind", kind);
    if (kind === "effort") {
      s.menu.appendChild(el("p", "ide-menu-h", "Effort"));
      EFFORTS.forEach(function (e) { var o = el("div", "ide-opt", cap(e)); o.setAttribute("data-value", e); if (s.cur.effort === e) o.setAttribute("aria-selected", "true"); s.menu.appendChild(o); });
    } else {
      var groups = provider === s.cur.provider ? [provider] : [s.cur.provider, provider];
      groups.forEach(function (prov) {
        var full = s.usageNow && s.usageNow.provider === prov && s.usageNow.pct >= 100;
        s.menu.appendChild(el("p", "ide-menu-h", prov + (full ? ": usage limit reached" : "")));
        TIERS.forEach(function (tier) {
          var id = models.tiers[tier] && models.tiers[tier][prov];
          if (!id) return;
          var o = el("div", "ide-opt");
          o.appendChild(el("span", null, modelName(id)));
          o.appendChild(el("small", null, tier));
          o.setAttribute("data-value", prov + "|" + tier);
          if (full) o.setAttribute("data-off", "true");
          if (s.cur.model === id) o.setAttribute("aria-selected", "true");
          s.menu.appendChild(o);
        });
      });
    }
    s.menu.hidden = false;
    var root = s.ide.getBoundingClientRect(), r = at.getBoundingClientRect();
    var w = s.menu.offsetWidth, h = s.menu.offsetHeight;
    var left = Math.max(8, Math.min(root.width - w - 8, r.left - root.left));
    var top = r.top - root.top - h - 6;
    if (top < 8) top = r.bottom - root.top + 6;
    s.menu.style.left = Math.round(left) + "px";
    s.menu.style.top = Math.round(top) + "px";
  }

  /* -------------------------------------------------- chat messages */
  function userMessage(s, key, command, argument, plain) {
    return ensure(s, key, function () {
      var m = el("div", "ide-msg ide-msg--user");
      m.appendChild(el("p", "ide-who", "You"));
      var p = el("p", "ide-said");
      if (plain) p.appendChild(document.createTextNode(plain));
      else { p.appendChild(el("span", "ide-cmd", command)); if (argument) p.appendChild(el("span", "ide-arg", " " + argument)); }
      m.appendChild(p);
      var hint = s.log.querySelector(".ide-hint");
      if (hint) hint.remove();
      s.log.appendChild(m);
      return m;
    });
  }
  function agentBlock(s, key) {
    return ensure(s, key, function () {
      var m = el("div", "ide-msg ide-msg--agent");
      m.appendChild(el("p", "ide-who", modelName(s.cur.model)));
      var ol = el("ol", "ide-steps");
      m.appendChild(ol);
      m.steps = ol;
      s.log.appendChild(m);
      return m;
    });
  }
  function typeInput(s, command, argument, plain, p) {
    s.input.textContent = "";
    if (plain) { s.input.appendChild(document.createTextNode(p > 0 ? plain : "")); return; }
    var total = command.length + (argument ? argument.length + 1 : 0);
    var n = Math.round(total * p);
    s.input.appendChild(el("span", "ide-cmd", command.slice(0, n)));
    if (argument && n > command.length) s.input.appendChild(el("span", "ide-arg", " " + argument.slice(0, n - command.length - 1)));
    if (p < 1) s.input.appendChild(el("span", "ide-caret"));
  }
  function clearInput(s) {
    s.input.textContent = "";
    s.input.appendChild(el("span", "ide-ph", "Ask the agent, or type / for a command"));
  }

  /* -------------------------------------------------- the highlight */
  function unionRect(els) {
    var r = null;
    els.forEach(function (e) {
      if (!e || !e.getClientRects().length) return;
      var b = e.getBoundingClientRect();
      r = r ? { left: Math.min(r.left, b.left), top: Math.min(r.top, b.top), right: Math.max(r.right, b.right), bottom: Math.max(r.bottom, b.bottom) } : { left: b.left, top: b.top, right: b.right, bottom: b.bottom };
    });
    return r;
  }
  /* The key content of the latest reply: its first table, code block, or list, with the heading
     just above it; a reply with none of these is marked whole. */
  function replyFocus(x) {
    var replies = x.log.querySelectorAll(".ide-reply");
    if (!replies.length) return [];
    var kids = Array.prototype.slice.call(replies[replies.length - 1].children).filter(function (k) { return !k.hidden; });
    for (var i = 0; i < kids.length; i++) {
      if (/^(TABLE|PRE|UL|OL)$/.test(kids[i].tagName)) {
        return i > 0 && /^H[34]$/.test(kids[i - 1].tagName) ? [kids[i - 1], kids[i]] : [kids[i]];
      }
    }
    return kids;
  }
  function showFocus(x, where, label, p, keep) {
    var targets, box;
    if (where === "reply") {
      targets = replyFocus(x);
      box = x.log;
      if (targets.length) x.log.scrollTop = Math.max(0, targets[0].offsetTop - x.log.offsetTop - 8);
    } else {
      targets = Array.prototype.slice.call(x.lines.querySelectorAll("li.ide-added"));
      if (!targets.length) targets = [x.lines];
      box = x.code;
      if (targets[0] !== x.lines) x.code.scrollTop = Math.max(0, x.code.scrollTop + targets[0].getBoundingClientRect().top - x.code.getBoundingClientRect().top - 40);
      else x.code.scrollTop = 0;
    }
    var r = unionRect(targets), b = box.getBoundingClientRect(), root = x.ide.getBoundingClientRect();
    if (!r || p >= 1 && !keep) { x.focus.hidden = true; return; }
    var pad = 4, left = Math.max(r.left - pad, b.left + 3), top = Math.max(r.top - pad, b.top + 3);
    var right = Math.min(r.right + pad, b.right - 3), bottom = Math.min(r.bottom + pad, b.bottom - 3);
    x.focus.hidden = false;
    x.focus.style.left = Math.round(left - root.left) + "px";
    x.focus.style.top = Math.round(top - root.top) + "px";
    x.focus.style.width = Math.max(20, Math.round(right - left)) + "px";
    x.focus.style.height = Math.max(20, Math.round(bottom - top)) + "px";
    /* The outline draws in over the first fifth of the mark; the label follows. */
    var grow = Math.min(1, p / 0.2);
    x.focus.style.opacity = String(keep ? 1 : grow);
    x.focus.style.setProperty("--draw", String(grow));
    x.focusLabel.textContent = label;
  }
  function hideFocus(x) { x.focus.hidden = true; }

  /* -------------------------------------------------- compile a session script into timed actions */
  function compile(s) {
    var T = [], t = 0, files = {}, cursor = "start", pick = null, usage = 0, n = 0;
    Object.keys(s.before).forEach(function (p) { files[p] = s.before[p]; });
    function add(dur, fn) { T.push({ t0: t, t1: t + dur, fn: fn }); t += dur; }
    function move(key) { var from = cursor; cursor = key; add(620, function (x, p) { placeCursor(x, from, key, p); }); }
    function click(key) { add(240, function (x, p) { placeCursor(x, key, key, 1); x.cursor.classList.toggle("is-down", p < 0.6); }); }
    function wait(ms) { add(ms, null); }
    s.script.forEach(function (a, ai) {
      if (a.do !== "reply") add(0, hideFocus);
      if (a.do === "pick") {
        var prov = a.provider, tier = a.tier, effort = a.effort, u = a.usage, nc = !!a.newchat;
        if (nc) add(0, function (x) {
          x.log.textContent = "";
          x.nodes = {};
          x.log.appendChild(el("p", "ide-hint ide-hint--new", "New chat. Paste the handoff to continue where the last session stopped."));
          x.ide.setAttribute("data-provider", prov);
        });
        move("model"); click("model");
        add(0, function (x) { openMenu(x, "model", x.model.box, prov); });
        wait(380);
        move("opt:" + prov + "|" + tier); click("opt:" + prov + "|" + tier);
        add(0, function (x) { x.menu.hidden = true; setPicker(x, prov, tier, x.cur.effort); setUsage(x, prov, u); });
        wait(260);
        move("effort"); click("effort");
        add(0, function (x) { openMenu(x, "effort", x.effort.box); });
        wait(320);
        move("opt:" + effort); click("opt:" + effort);
        add(0, function (x) { x.menu.hidden = true; setPicker(x, prov, tier, effort); });
        wait(240);
        pick = a;
        usage = u;
      } else if (a.do === "prompt" || a.do === "paste") {
        var cmd = a.command || "", arg = a.argument || "", plain = a.do === "paste" ? a.text : null, key = "u" + ai;
        move("input"); click("input");
        if (plain) add(420, function (x, p) { typeInput(x, "", "", plain, p > 0.3 ? 1 : 0); });
        else add(Math.min(3200, 520 + cmd.length * 70 + arg.length * 16), function (x, p) { typeInput(x, cmd, arg, null, p); });
        wait(320);
        move("send"); click("send");
        add(0, function (x) { clearInput(x); userMessage(x, key, cmd, arg, plain); scrollLog(x); });
        wait(380);
      } else if (a.do === "work") {
        var block = "w" + ai, u0 = usage, u1 = a.usage, steps = a.steps, durs = [];
        steps.forEach(function (st) {
          var lines = (st.content || "").split("\n").length;
          durs.push(st.kind === "write" ? Math.min(3400, 500 + lines * 70) : st.kind === "edit" ? Math.min(3600, 900 + lines * 50) : st.kind === "think" ? 1100 : st.kind === "read" ? 800 : 1000);
        });
        var total = durs.reduce(function (x, y) { return x + y; }, 0), done = 0;
        steps.forEach(function (st, k) {
          var from = files[st.file], to = st.content, ops = st.kind === "edit" ? diff((from || "").split("\n"), to.split("\n")) : null;
          var ua = u0 + (u1 - u0) * (done / total), ub = u0 + (u1 - u0) * ((done + durs[k]) / total);
          done += durs[k];
          add(durs[k], function (x, p) {
            var blockEl = agentBlock(x, block);
            var row = ensure(x, block + "s" + k, function () {
              var li = el("li", "ide-step");
              li.setAttribute("data-kind", st.kind);
              li.appendChild(el("span", "ide-step-k", STEP_KINDS[st.kind]));
              li.appendChild(el("span", "ide-step-l", st.label));
              if (st.output) { var out = el("pre", "ide-step-out", st.output); li.appendChild(out); li.out = out; }
              blockEl.steps.appendChild(li);
              return li;
            });
            row.setAttribute("data-live", p < 1 ? "true" : "false");
            if (row.out) row.out.hidden = p < 0.35;
            setUsage(x, x.cur.provider, ua + (ub - ua) * p);
            if (st.kind === "read") openFile(x, st.file);
            else if (st.kind === "write") writeLive(x, st.file, to, p);
            else if (st.kind === "edit") editLive(x, st.file, from || "", to, ops, p);
            scrollLog(x);
          });
          if (st.file && (st.kind === "write" || st.kind === "edit")) {
            files[st.file] = to;
            if (st.mark) { var lbl = st.mark; add(1500, function (x, p) { showFocus(x, "code", lbl, p, false); }); }
          }
        });
        usage = u1;
      } else if (a.do === "reply") {
        var rkey = "r" + ai, text = a.text, count = markdown(text).length;
        add(380 + count * 260, function (x, p) {
          var blockEl = x.nodes["w" + (ai - 1)] || agentBlock(x, "rb" + ai);
          var box = ensure(x, rkey, function () {
            var r = el("div", "ide-reply");
            markdown(text).forEach(function (node) {
              if (node.tagName === "PRE") { var c = el("span", "ide-copy", "Copy"); c.setAttribute("aria-hidden", "true"); node.appendChild(c); }
              r.appendChild(node);
            });
            blockEl.appendChild(r);
            return r;
          });
          var k = Math.ceil(box.children.length * Math.max(0, (p - 0.1) / 0.9));
          for (var i = 0; i < box.children.length; i++) box.children[i].hidden = i >= k;
          scrollLog(x);
        });
        var mlabel = a.mark;
        add(1800, function (x, p) { showFocus(x, "reply", mlabel, p, true); });
      } else if (a.do === "limit") {
        var ltext = a.text;
        add(0, function (x) {
          setUsage(x, x.cur.provider, 100);
          ensure(x, "l" + ai, function () {
            var m = el("div", "ide-limit");
            m.setAttribute("role", "status");
            m.appendChild(el("span", "ide-limit-ic", "!"));
            m.appendChild(el("span", null, ltext));
            x.log.appendChild(m);
            return m;
          });
          scrollLog(x);
        });
        wait(1600);
      } else if (a.do === "copy") {
        move("copy"); click("copy");
        add(1100, function (x, p) { x.toast.hidden = p >= 1; var cs = x.log.querySelectorAll(".ide-copy"); if (cs.length) cs[cs.length - 1].textContent = "Copied"; });
      }
      n += 1;
    });
    wait(500);
    s.T = T;
    s.duration = t;
    s.after = files;
  }

  function writeLive(s, path, content, p) {
    if (!(path in s.files)) { s.files[path] = ""; s.status[path] = "A"; s.view.key = null; }
    viewFile(s, path);
    var rows = content.split("\n"), k = p >= 1 ? rows.length : Math.floor(rows.length * p);
    var key = path + "@w" + k;
    if (s.view.key !== key) {
      s.view.key = key;
      showLines(s, path, rows.slice(0, k).map(function (t, i) { return { text: t, cls: i === k - 1 && p < 1 ? "ide-type" : null }; }));
      s.code.scrollTop = s.code.scrollHeight;
      paintTree(s);
    }
    if (p >= 1) { s.files[path] = content; s.view.key = path + "#" + content.length; s.code.scrollTop = 0; }
  }
  function editLive(s, path, from, to, ops, p) {
    if (!s.status[path]) { s.status[path] = "M"; s.view.key = null; }
    viewFile(s, path);
    var removed = ops.filter(function (o) { return o[0] === "-"; }).length, added = ops.filter(function (o) { return o[0] === "+"; }).length;
    var strike = p < 0.3 ? Math.ceil(removed * p / 0.3) : removed, grow = p < 0.3 ? 0 : p >= 1 ? added : Math.floor(added * (p - 0.3) / 0.7);
    var key = path + "@e" + strike + "/" + grow + (p >= 1 ? "!" : "");
    if (s.view.key === key) return;
    s.view.key = key;
    var rows = [], ks = 0, kg = 0, first = -1;
    ops.forEach(function (o) {
      if (o[0] === "=") rows.push({ text: o[1] });
      else if (o[0] === "-") { if (p < 1) { ks += 1; rows.push({ text: o[1], op: "del", cls: ks <= strike ? "ide-strike" : null }); if (first < 0) first = rows.length - 1; } }
      else { kg += 1; if (kg <= grow) { rows.push({ text: o[1], op: "add", cls: kg === grow && p < 1 ? "ide-type" : "ide-added" }); if (first < 0) first = rows.length - 1; } }
    });
    showLines(s, path, rows);
    var li = s.lines.children[Math.max(0, first)];
    if (li) s.code.scrollTop = Math.max(0, li.offsetTop - 60);
    paintTree(s);
    if (p >= 1) s.files[path] = to;
  }

  /* -------------------------------------------------- playback */
  var players = [], raf = 0, last = 0;
  function seek(s, t) {
    t = Math.max(0, Math.min(s.duration, t));
    if (t < s.t || s.idx == null) reset(s);
    while (s.idx < s.T.length && s.T[s.idx].t1 <= t) { var a = s.T[s.idx]; if (a.fn) a.fn(s, 1); s.idx += 1; }
    if (s.idx < s.T.length && s.T[s.idx].t0 <= t && s.T[s.idx].fn) { var c = s.T[s.idx]; c.fn(s, (t - c.t0) / Math.max(1, c.t1 - c.t0)); }
    s.t = t;
    paintControls(s);
  }
  function frame(now) {
    var dt = last ? Math.min(100, now - last) : 16, any = false;
    last = now;
    players.forEach(function (s) {
      if (!s.playing) return;
      var next = s.t + dt * s.speed;
      if (next >= s.duration) { s.playing = false; seek(s, s.duration); }
      else { any = true; seek(s, next); }
    });
    if (any) raf = window.requestAnimationFrame(frame);
    else { raf = 0; last = 0; }
  }
  function play(s) {
    s.started = true;
    s.autoPaused = false;
    s.playing = true;
    paintControls(s);
    if (!raf) { last = 0; raf = window.requestAnimationFrame(frame); }
  }
  function pause(s) { s.playing = false; paintControls(s); }
  function setSpeed(s, x) { if (SPEEDS.indexOf(x) !== -1) { s.speed = x; paintControls(s); } }
  function watch(s) {
    if (!("IntersectionObserver" in window)) return;
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.intersectionRatio >= 0.5) { if (!REDUCED && (!s.started || s.autoPaused) && s.t < s.duration) play(s); }
        else if (e.intersectionRatio < 0.15 && s.playing) { pause(s); s.autoPaused = true; }
      });
    }, { threshold: [0, 0.15, 0.5] }).observe(s.ide);
  }

  /* -------------------------------------------------- build */
  var models = null;
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
    /* The project evolves through the story: each step starts from what earlier steps wrote. */
    var first = null;
    story.stages.forEach(function (st) { if (!first && st.script) st.script.forEach(function (a) { if (!first && a.do === "pick") first = a; }); });
    var tree = {}, carry = { provider: story.defaultProvider, tier: null, effort: "medium", usage: first ? first.usage : 0 };
    story.project.files.forEach(function (f) { tree[f.path] = f.code; });
    story.stages.forEach(function (st) {
      var section = sectionFor(st.id);
      var box = section && section.querySelector(".container");
      if (!box || st.kind === "intro") return;
      var heading = box.querySelector("h1, h2");
      var host = box.querySelector("[data-ss-id]");
      box.insertBefore(headFor(st, heading, story.workflow), box.firstChild);
      if (st.kind === "play") {
        var notes = notesFor(st);
        if (host) box.insertBefore(notes, host); else box.appendChild(notes);
        var after = ty(el("p", "tr-after", st.after), "body");
        if (host && host.nextSibling) box.insertBefore(after, host.nextSibling); else box.appendChild(after);
        return;
      }
      var s = ideShell(st, story.project.name);
      s.project = story.project.name;
      s.script = st.script;
      s.before = {};
      Object.keys(tree).forEach(function (p) { s.before[p] = tree[p]; });
      s.firstFile = tree["README.md"] != null ? "README.md" : Object.keys(tree)[0];
      s.init = { provider: carry.provider, tier: carry.tier, effort: carry.effort, usage: carry.usage };
      s.speed = 1;
      s.playing = false;
      compile(s);
      box.appendChild(s.wrap);
      box.appendChild(whyFor(st));
      s.seekBar.max = String(Math.round(s.duration));
      reset(s);
      seek(s, REDUCED ? s.duration : 0);
      if (REDUCED) s.started = true;
      watch(s);
      players.push(s);
      tree = s.after;
      st.script.forEach(function (a) { if (a.do === "pick") carry = { provider: a.provider, tier: a.tier, effort: a.effort, usage: a.usage }; else if (a.do === "work") carry.usage = a.usage; else if (a.do === "limit") carry.usage = 100; });
    });
    function find(id) { var f = null; players.forEach(function (x) { if (x.st.id === id) f = x; }); return f; }
    return {
      story: story,
      modelName: modelName,
      players: function () { return players.map(function (x) { return x.st.id; }); },
      rebalance: function () {},
      /* For scripts and tests: drive a step's player and read its state. */
      play: function (id) { var x = find(id); if (x) play(x); return !!x; },
      pause: function (id) { var x = find(id); if (x) pause(x); return !!x; },
      /* A seek counts as a start: a player someone has scrubbed never autoplays over it. */
      seek: function (id, ms) { var x = find(id); if (x) { x.started = true; pause(x); seek(x, ms); } return !!x; },
      finish: function (id) { var x = find(id); if (x) { x.started = true; pause(x); seek(x, x.duration); } return !!x; },
      speed: function (id, v) { var x = find(id); if (x) setSpeed(x, v); return x ? x.speed : null; },
      state: function (id) {
        var x = find(id);
        if (!x) return null;
        return { t: x.t, duration: x.duration, playing: !!x.playing, speed: x.speed, done: x.t >= x.duration,
          provider: x.cur.provider, tier: x.cur.tier, effort: x.cur.effort, model: x.cur.model, modelName: x.cur.model ? modelName(x.cur.model) : null,
          usage: x.usageNow ? x.usageNow.pct : null, usageProvider: x.usageNow ? x.usageNow.provider : null };
      }
    };
  }
  function whyFor(st) {
    var names = [], tier = null, effort = null;
    st.script.forEach(function (a) {
      if (a.do !== "pick") return;
      var n = modelName(models.tiers[a.tier][a.provider]);
      if (names.indexOf(n) === -1) names.push(n);
      tier = a.tier; effort = a.effort;
    });
    var p = ty(el("p", "tr-why"), "body-sm");
    p.appendChild(el("b", null, names.join(", then ")));
    p.appendChild(document.createTextNode(", " + tier + " tier, " + effort + " effort. " + st.why));
    return p;
  }

  return { render: render, modelName: modelName };
})();
