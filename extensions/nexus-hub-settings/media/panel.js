// The webview draws trusted engine data as text and sends only allowlisted control values.
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) { module.exports = api; }
  else { api.boot(root); }
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";
  var GUARDS = [
    ["git_safety", "Git safety", "Block dangerous Git commands."],
    ["secret_scan", "Secret scanning", "Check writes for exposed credentials."],
    ["edit_preservation", "Protect my edits", "Check before overwriting changes."],
    ["large_file_warning", "Large-file warnings", "Warn before unusually large writes."],
    ["git_guardrails", "Block Git bypass flags", "Prevent skipping hooks or commit signing."],
  ];
  var ENGINE_UPDATE = "Update the Nexus-Hub settings engine to use all guardrail switches.";
  function createPanel(doc, post) {
    var app = doc.getElementById("app");
    var model = null;
    var pending = false;
    var drafts = {};
    var announced = "";
    var detailsOpen = false;
    var effortDetailsOpen = false;
    function el(tag, attrs, children) {
      var node = doc.createElement(tag);
      Object.keys(attrs || {}).forEach(function (key) {
        var value = attrs[key];
        if (value === undefined || value === null || value === false) { return; }
        if (key === "text") { node.textContent = value; }
        else { node.setAttribute(key, value === true ? "" : String(value)); }
      });
      (children || []).forEach(function (child) { if (child) { node.appendChild(child); } });
      return node;
    }
    function text(tag, value, cls) { return el(tag, { text: value, class: cls }); }
    function blocked() { return !model || model.readOnly || model.busy || pending; }
    function send(message) {
      if (blocked()) { return; }
      pending = true;
      app.querySelectorAll("select, button[data-setting]").forEach(function (control) { control.setAttribute("aria-disabled", "true"); });
      post(message);
    }
    function control(id) { return (model.controls || []).find(function (item) { return item.id === id; }); }
    function effective(row) { return row.state === "overridden-by" ? row.layerValue : row.value; }
    function preferences() {
      if (model.preferences) { return model.preferences; }
      var effort = control("effort");
      var shared = effort && effort.rows.find(function (row) { return row.tool === "internal"; });
      var native = effort ? effort.rows.filter(function (row) { return row.tool !== "internal" && row.installed !== false && row.state !== "tool-not-installed"; }) : [];
      var values = Array.from(new Set(native.filter(function (row) { return row.canSet; }).map(effective).filter(Boolean)));
      var chosen = shared && shared.value || (values.length === 1 ? values[0] : "");
      if (!effort || effort.choices.indexOf(chosen) < 0) { chosen = ""; }
      var conflict = !!(shared && ["cannot-detect", "unverified-for-version", "not-covered"].indexOf(shared.state) >= 0) || native.some(function (row) { return row.canSet && (["cannot-detect", "unverified-for-version", "not-covered"].indexOf(row.state) >= 0 || chosen && (row.matchesDefault === false || row.matchesDefault === undefined && effective(row) !== chosen)); });
      var unsupported = native.some(function (row) { return row.state === "not-settable"; });
      return { effort: chosen, needsAttention: !!conflict, effortStatus: conflict ? "Some defaults need synchronization. Choose an effort level to apply it again." : chosen ? "Mapped to native defaults for new sessions." : "Choose the default for new sessions." };
    }
    function button(label, key, action, attrs) {
      var node = el("button", Object.assign({ type: "button", text: label, "data-focus": key }, attrs || {}));
      node.addEventListener("click", action);
      return node;
    }
    function refreshButton() {
      return button("Refresh", "refresh", function () { if (!model.busy && !pending) { post({ type: "refresh" }); } }, { class: "refresh", "aria-disabled": model.busy || pending ? "true" : null });
    }
    function header() {
      return el("header", {}, [el("div", { class: "brand" }, [el("img", { src: app.getAttribute("data-logo"), alt: "", width: "32", height: "32" }), text("h1", "Nexus Hub")])]);
    }
    function effortDetails() {
      var node = el("details", { class: "settings-details", open: effortDetailsOpen || null }, [
        el("summary", { text: "Details", "data-focus": "details" }),
        text("p", "New sessions use the global effort level. Changing it also updates supported connected sessions. Manual session choices stay until the next global change or Apply to all."),
        compatibility(),
        text("p", "Enabled guardrails apply on the next hook run, including full-access mode. Coverage requires platform hooks."),
        text("p", "Refresh rereads settings and retries synchronization after external changes."),
        refreshButton(),
      ]);
      node.addEventListener("toggle", function () { effortDetailsOpen = node.open; });
      return node;
    }
    function effortSection(summary) {
      var c = control("effort");
      if (!c) { return null; }
      var current = model.busy && drafts.effort !== undefined ? drafts.effort : summary.effort;
      var labels = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high", max: "Max", ultra: "Ultra" };
      var choices = c.choices.filter(function (value) { return Object.prototype.hasOwnProperty.call(labels, value); });
      var selected = choices.indexOf(current);
      var group = el("div", { id: "effort", role: "radiogroup", class: "effort-choices", "aria-labelledby": "effort-title" });
      group.style.setProperty("--effort-fill", selected < 0 ? "0%" : selected / Math.max(1, choices.length - 1) * 100 + "%");
      choices.forEach(function (value, index) {
        var radio = button("", "effort:" + value, function () {
          if (blocked() || !c.canApply || value === current) { return; }
          drafts.effort = value;
          send({ type: "set", control: "effort", value: value, tool: null });
        }, { role: "radio", class: "effort-choice", "data-setting": "effort", "data-value": value, "aria-label": labels[value], "aria-checked": value === current ? "true" : "false", tabindex: index === (selected < 0 ? 0 : selected) ? "0" : "-1", disabled: model.readOnly || !c.canApply, "aria-disabled": model.busy || pending ? "true" : null });
        radio.appendChild(el("span", { class: "effort-dot", "aria-hidden": "true" }));
        radio.appendChild(text("span", labels[value], "effort-label"));
        radio.addEventListener("keydown", function (event) {
          if (blocked() || !c.canApply) { return; }
          var next = event.key === "ArrowRight" || event.key === "ArrowDown" ? (index + 1) % choices.length : event.key === "ArrowLeft" || event.key === "ArrowUp" ? (index + choices.length - 1) % choices.length : event.key === "Home" ? 0 : event.key === "End" ? choices.length - 1 : -1;
          if (next < 0) { return; }
          event.preventDefault();
          var target = group.querySelectorAll("button")[next];
          target.focus();
          target.click();
        });
        group.appendChild(radio);
      });
      return el("section", { class: "settings-section effort-section", "aria-labelledby": "effort-title" }, [
        el("div", { class: "section-heading" }, [el("h2", { id: "effort-title", text: "Global effort level" }), button("Apply to all", "applyAll", function () { send({ type: "applyAll" }); }, { class: "action-button", "data-setting": "applyAll", "aria-disabled": blocked() || !current ? "true" : null })]),
        group,
        sessionToggle("fast", "Fast mode", model.sessionDefaults && model.sessionDefaults.fastMode, "setFastMode", "May increase usage or cost."),
        effortDetails(),
      ]);
    }
    function guardState(c) {
      var row = c.rows.find(function (item) { return item.tool === "internal"; }) || c.rows[0];
      if (!row || !c.canApply || ["cannot-detect", "unverified-for-version", "not-covered"].indexOf(row.state) >= 0) { return { known: false, on: false }; }
      var value = effective(row);
      return { known: true, on: value === "on" || value === "true" || (row.state === "tool-default" && c.id !== "git_guardrails") };
    }
    function sessionToggle(id, label, value, type, hint) {
      var toggle = button("", "session:" + id, function () { if (!blocked()) { send({ type: type, value: value !== true }); } }, {role: "switch", class: "switch", "data-setting": id, "aria-checked": value === true ? "true" : "false", "aria-labelledby": "label-" + id, "aria-describedby": "description-" + id, disabled: model.readOnly, "aria-disabled": blocked() ? "true" : null});
      toggle.appendChild(el("span", {class: "switch-track", "aria-hidden": "true"}, [el("span", {class: "switch-thumb"})]));
      return el("div", {class: "setting-row session-row", title: value == null ? "No shared speed is set. Existing session speeds stay unchanged until chosen. Fast mode may increase usage or cost." : hint}, [el("div", {class: "setting-copy"}, [el("span", {id: "label-" + id, text: label, class: "setting-label"}), el("p", {id: "description-" + id, text: value == null ? "Not set; may cost more." : hint, class: "hint"})]), toggle]);
    }
    function editorSection() {
      if (!model.codexAvailable) { return null; }
      return el("section", {class: "settings-section editor-section", "aria-labelledby": "editor-title"}, [el("h2", {id: "editor-title", text: "Editor"}), sessionToggle("codexTabs", "Open Codex in tabs", !model.sessionDefaults || model.sessionDefaults.codexTabs !== false, "setCodexTabs", "Use editor tabs with a history button. Turn off for the activity pane.")]);
    }
    function guardRow(spec) {
      var installed = control(spec[0]);
      var c = installed || { id: spec[0], rows: [], canApply: false };
      var state = guardState(c);
      var label = "label-" + c.id;
      var description = "description-" + c.id;
      var toggle = button("", "toggle:" + c.id, function () {
        if (state.known) { send({ type: "set", control: c.id, value: state.on ? "off" : "on", tool: null }); }
      }, { role: "switch", class: "switch", "data-setting": c.id, "aria-checked": state.on ? "true" : "false", "aria-labelledby": label, "aria-describedby": description, "aria-disabled": model.busy || pending ? "true" : null, disabled: model.readOnly || !state.known });
      toggle.appendChild(el("span", { class: "switch-track", "aria-hidden": "true" }, [el("span", { class: "switch-thumb" })]));
      return el("li", { class: "setting-row" }, [
        el("div", { class: "setting-copy" }, [el("span", { id: label, class: "setting-label", text: spec[1] }), el("p", { id: description, class: "hint", text: !installed ? "Requires an engine update." : state.known ? spec[2] : "Unavailable. Refresh to check this guardrail." })]),
        toggle,
      ]);
    }
    function guardSection() {
      var rows = GUARDS.map(guardRow).filter(Boolean);
      if (!rows.length) { return null; }
      return el("section", { class: "settings-section guardrails-section", "aria-labelledby": "guardrails-title" }, [el("h2", { id: "guardrails-title", text: "Guardrails" }), el("ul", { class: "setting-list" }, rows)]);
    }
    function compatibility() {
      var node = el("footer", { class: "compatibility" }, [
        text("p", "Automatic effort: Claude Code, Codex, and qualified Cursor Agent builds."),
        text("p", "Manual effort: GitHub Copilot and Antigravity native agents. Cursor Auto and models without effort controls keep their native behavior."),
        text("p", "Older Codex clients map Max and Ultra to Extra high."),
      ]);
      return node;
    }
    function notice() {
      if (!model.notice) { return null; }
      var n = model.notice;
      if (n.level === "info") { return null; }
      var node = el("div", { class: "notice", "data-level": n.level }, [text("p", n.text)]);
      if (n.level !== "info" && n.lines && n.lines.length) {
        var detail = el("details", { open: detailsOpen || null }, [text("summary", "Technical details"), el("ul", {}, n.lines.slice(0, 8).map(function (line) { return text("li", line); }))]);
        detail.addEventListener("toggle", function () { detailsOpen = detail.open; });
        node.appendChild(detail);
      }
      return node;
    }
    function announce() {
      var missing = model.controls.length && !model.error && GUARDS.some(function (spec) { return !control(spec[0]); });
      var n = model.notice || (missing ? { level: "warn", text: ENGINE_UPDATE } : null);
      var value = n ? n.level + ":" + n.text : "";
      if (value === announced) { return; }
      announced = value;
      ["live-status", "live-alert"].forEach(function (id) { var region = doc.getElementById(id); if (region) { region.textContent = ""; } });
      if (n) { var region = doc.getElementById(n.level === "error" ? "live-alert" : "live-status"); if (region) { region.textContent = n.text; } }
    }
    function render(next) {
      var focused = doc.activeElement && app.contains(doc.activeElement) ? doc.activeElement.getAttribute("data-focus") : null;
      model = next;
      pending = false;
      if (!model.busy) { delete drafts.effort; }
      app.setAttribute("aria-busy", model.busy ? "true" : "false");
      var children = [header()];
      if (model.error) {
        children.push(el("section", { class: "error-card", role: "alert" }, [text("h2", model.error.title), text("p", model.error.message), text("p", model.error.fix, "hint"), el("details", {}, [text("summary", "Technical details"), el("pre", {}, [text("code", model.error.command)])])]), refreshButton());
      } else if (!model.controls.length) {
        children.push(text("p", model.busy ? "Loading settings..." : "No settings were reported. Choose Refresh to try again.", "empty-state"), refreshButton());
      } else {
        if (model.readOnly) { children.push(text("p", "Trust this workspace to change settings.", "read-only")); }
        if (GUARDS.some(function (spec) { return !control(spec[0]); })) { children.push(el("p", { class: "notice engine-update", "data-level": "warn", text: ENGINE_UPDATE })); }
        children.push(notice(), effortSection(preferences()), guardSection(), editorSection(), el("section", { class: "settings-section version-section", "aria-labelledby": "version-title" }, [el("h2", { id: "version-title", text: "Version" }), el("div", { class: "version-row" }, [el("p", { class: "installed-version" }, [text("span", "Installed version: ", "version-label"), text("span", model.hubVersion || "Unknown", "version-number")]), button("Check for upgrades", "upgrade", function () { send({ type: "upgrade" }); }, { class: "action-button", "aria-disabled": blocked() ? "true" : null })])]));
      }
      app.replaceChildren.apply(app, children.filter(Boolean));
      if (focused) {
        var target = Array.from(app.querySelectorAll("[data-focus]")).find(function (node) { return node.getAttribute("data-focus") === focused && !node.disabled; }) || app.querySelector("[data-focus='details']") || app.querySelector("[data-focus='refresh']");
        if (target) { target.focus(); }
      }
      announce();
    }
    function onMessage(message) { if (message && message.type === "render" && message.model && Array.isArray(message.model.controls)) { render(message.model); } }
    return { render: render, onMessage: onMessage, drafts: drafts };
  }
  function boot(win) {
    var acquire = typeof win.acquireVsCodeApi === "function" ? win.acquireVsCodeApi : typeof acquireVsCodeApi === "function" ? acquireVsCodeApi : null;
    if (!acquire) { return null; }
    var vscode = acquire();
    var panel = createPanel(win.document, function (message) { vscode.postMessage(message); });
    win.addEventListener("message", function (event) { panel.onMessage(event.data); });
    vscode.postMessage({ type: "ready" });
    return panel;
  }
  return { createPanel: createPanel, boot: boot };
});
