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
      var state = app.querySelector(".save-state");
      if (state) { state.textContent = "Saving..."; }
      post(message);
    }
    function control(id) { return (model.controls || []).find(function (item) { return item.id === id; }); }
    function effective(row) { return row.state === "overridden-by" ? row.layerValue : row.value; }
    function preferences() {
      if (model.preferences) { return model.preferences; }
      var effort = control("effort");
      var shared = effort && effort.rows.find(function (row) { return row.tool === "internal"; });
      var native = effort ? effort.rows.filter(function (row) { return row.tool !== "internal" && row.state !== "tool-not-installed"; }) : [];
      var values = Array.from(new Set(native.filter(function (row) { return row.canSet; }).map(effective).filter(Boolean)));
      var chosen = shared && shared.value || (values.length === 1 ? values[0] : "");
      if (!effort || effort.choices.indexOf(chosen) < 0) { chosen = ""; }
      var conflict = native.some(function (row) { return row.canSet && (["cannot-detect", "unverified-for-version", "not-covered"].indexOf(row.state) >= 0 || chosen && effective(row) !== chosen); });
      var unsupported = native.some(function (row) { return row.state === "not-settable"; });
      return { effort: chosen, needsAttention: !!(conflict || unsupported), effortStatus: conflict ? "Another setting overrides this default, or its application cannot be verified." : unsupported ? "Applied where supported. Some platforms cannot accept this default." : chosen ? "Applied to supported platforms for new sessions." : "Choose the default for new sessions." };
    }
    function button(label, key, action, attrs) {
      var node = el("button", Object.assign({ type: "button", text: label, "data-focus": key }, attrs || {}));
      node.addEventListener("click", action);
      return node;
    }
    function header() {
      var refresh = button("Refresh", "refresh", function () { if (!model.busy && !pending) { post({ type: "refresh" }); } }, { class: "refresh", "aria-disabled": model.busy || pending ? "true" : null });
      return el("header", {}, [
        el("div", { class: "brand" }, [el("img", { src: app.getAttribute("data-logo"), alt: "", width: "32", height: "32" }), el("div", {}, [text("h1", "Nexus Settings"), text("p", "Shared defaults and guardrails", "hint")])]),
        refresh,
      ]);
    }
    function effortSection(summary) {
      var c = control("effort");
      if (!c) { return null; }
      var select = el("select", { id: "effort", "data-focus": "effort", "data-setting": "effort", "aria-describedby": "effort-status", disabled: model.readOnly || !c.canApply, "aria-disabled": model.busy || pending ? "true" : null });
      var current = model.busy && drafts.effort !== undefined ? drafts.effort : summary.effort;
      if (!current) { select.appendChild(el("option", { value: "", text: "Choose a default", selected: true, disabled: true })); }
      var labels = { low: "Low", medium: "Medium", high: "High", xhigh: "Extra high" };
      c.choices.forEach(function (value) { select.appendChild(el("option", { value: value, text: labels[value] || value })); });
      select.value = current || "";
      select.addEventListener("change", function () {
        if (blocked() || !c.canApply || c.choices.indexOf(select.value) < 0) { select.value = current || ""; return; }
        drafts.effort = select.value;
        send({ type: "set", control: "effort", value: select.value, tool: null });
      });
      return el("section", { class: "settings-section effort-section", "aria-labelledby": "effort-title" }, [
        el("div", { class: "section-heading" }, [el("label", { id: "effort-title", for: "effort", text: "Default effort" }), text("span", model.busy || pending ? "Saving..." : "Auto-save", "save-state")]),
        select,
        el("p", { id: "effort-status", class: summary.needsAttention ? "application-status attention" : "application-status", text: summary.effortStatus }),
      ]);
    }
    function guardState(c) {
      var row = c.rows.find(function (item) { return item.tool === "internal"; }) || c.rows[0];
      if (!row || !c.canApply || ["cannot-detect", "unverified-for-version", "not-covered"].indexOf(row.state) >= 0) { return { known: false, on: false }; }
      var value = effective(row);
      return { known: true, on: value === "on" || value === "true" || (row.state === "tool-default" && c.id !== "git_guardrails") };
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
      return el("section", { class: "settings-section", "aria-labelledby": "guardrails-title" }, [el("h2", { id: "guardrails-title", text: "Guardrails" }), el("ul", { class: "setting-list" }, rows)]);
    }
    function notice() {
      if (!model.notice) { return null; }
      var n = model.notice;
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
        children.push(el("section", { class: "error-card", role: "alert" }, [text("h2", model.error.title), text("p", model.error.message), text("p", model.error.fix, "hint"), el("details", {}, [text("summary", "Technical details"), el("pre", {}, [text("code", model.error.command)])])]));
      } else if (!model.controls.length) {
        children.push(text("p", model.busy ? "Loading settings..." : "No settings were reported. Choose Refresh to try again.", "empty-state"));
      } else {
        if (model.readOnly) { children.push(text("p", "Trust this workspace to change settings.", "read-only")); }
        if (GUARDS.some(function (spec) { return !control(spec[0]); })) { children.push(el("p", { class: "notice engine-update", "data-level": "warn", text: ENGINE_UPDATE })); }
        children.push(notice(), effortSection(preferences()), guardSection(), text("p", "Effort applies to new sessions. Guardrails apply on the next hook run; full-access modes and hook overrides can bypass them.", "footnote"));
      }
      app.replaceChildren.apply(app, children.filter(Boolean));
      if (focused) {
        var target = Array.from(app.querySelectorAll("[data-focus]")).find(function (node) { return node.getAttribute("data-focus") === focused && !node.disabled; }) || app.querySelector("[data-focus='refresh']");
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
