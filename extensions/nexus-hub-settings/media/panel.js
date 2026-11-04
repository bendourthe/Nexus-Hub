// The Nexus-Hub Settings panel (webview side).
//
// It draws the view model the extension host sends, and posts back small request
// messages. It never builds markup from a string: every value from the engine is set
// with textContent or a plain attribute, so a hostile model id or file value cannot
// become markup or script. The host validates every request again.
//
// Two rules keep the page usable from the keyboard and by screen reader. While the host
// is busy a control is marked aria-disabled and ignores clicks but stays focusable and
// keeps its place, because a control that is really disabled cannot hold focus and the
// next render would then leave focus on the page body. And a notice is spoken through
// two live regions that exist before any text is put in them, because text inside an
// element that is created with its text is usually not announced.
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else {
    api.boot(root);
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  var ICONS = { check: "icon-check", dot: "icon-dot", warning: "icon-warning", lock: "icon-lock", info: "icon-info", x: "icon-x", question: "icon-question" };

  function createPanel(doc, post) {
    var app = doc.getElementById("app");
    var drafts = {};
    var starts = {};
    var openSources = {};
    var announced = "";
    var model = null;
    var sequence = 0;

    function el(tag, attrs, kids) {
      var node = doc.createElement(tag);
      var props = attrs || {};
      Object.keys(props).forEach(function (name) {
        var value = props[name];
        if (value === null || value === undefined || value === false) {
          return;
        }
        if (name === "text") {
          node.textContent = value;
        } else if (name === "class") {
          node.setAttribute("class", value);
        } else if (name === "on") {
          Object.keys(value).forEach(function (type) {
            node.addEventListener(type, value[type]);
          });
        } else {
          node.setAttribute(name, value === true ? "" : String(value));
        }
      });
      (kids || []).forEach(function (kid) {
        if (kid) {
          node.appendChild(kid);
        }
      });
      return node;
    }

    function text(tag, value, cls) {
      return el(tag, { text: value, class: cls });
    }

    function uid(prefix) {
      sequence += 1;
      return prefix + "-" + sequence;
    }

    /** Really disabled: nothing can change, so nothing needs focus. */
    function locked() {
      return !model || model.readOnly;
    }

    /** Waiting for the host: controls keep focus and ignore clicks. */
    function busy() {
      return !!(model && model.busy);
    }

    function badge(b) {
      return el("span", { class: "badge tone-" + b.tone }, [
        el("span", { class: "icon " + (ICONS[b.icon] || "icon-dot"), "aria-hidden": "true" }),
        el("span", { text: b.text }),
      ]);
    }

    function blocked(extra) {
      return busy() || !!(extra && extra.ready && !extra.ready());
    }

    // extra: cls, aria (a longer accessible name that starts with the visible text), keepEnabled (never really
    // disabled: Refresh must work in the error and untrusted states), ready (a function: is there a value to send).
    function button(label, focus, onClick, extra) {
      var opts = extra || {};
      return el("button", {
        type: "button",
        text: label,
        "data-focus": focus,
        "aria-label": opts.aria,
        disabled: opts.keepEnabled ? false : locked(),
        "aria-disabled": blocked(opts) ? "true" : null,
        class: opts.cls,
        on: {
          click: function (event) {
            if (blocked(opts)) {
              event.preventDefault();
              return;
            }
            onClick(event);
          },
        },
      });
    }

    /** A label above its control; an action, when given, sits on the same line as the control. */
    function labeled(labelText, control, id, action) {
      var line = action ? el("div", { class: "inline" }, [control, action]) : control;
      return el("div", { class: "field" }, [el("label", { for: id, text: labelText }), line]);
    }

    function choiceLabel(control, choice) {
      return control.weakeningChoices.indexOf(choice) >= 0 ? choice + " (lowers a safety barrier)" : choice;
    }

    function draftValue(key, fallback) {
      return Object.prototype.hasOwnProperty.call(drafts, key) ? drafts[key] : fallback;
    }

    /** The value a choice starts at: the one the tool already has, else a placeholder (or the only choice). */
    function startFor(control, current) {
      if (current && control.choices.indexOf(current) >= 0) {
        return current;
      }
      return control.choices.length === 1 ? control.choices[0] : "";
    }

    /** Keep a Set button's aria-disabled in step with whether its field holds a value. */
    function syncSet(key) {
      var node = app.querySelector('[data-focus="set:' + key + '"]');
      if (!node) {
        return;
      }
      if (busy() || String(draftValue(key, starts[key]) || "").trim() === "") {
        node.setAttribute("aria-disabled", "true");
      } else {
        node.removeAttribute("aria-disabled");
      }
    }

    function select(control, key, focus, start, labelText, action) {
      var id = uid("sel");
      starts[key] = start;
      var current = draftValue(key, start);
      var placeholder = control.choices.length > 1 && control.choices.indexOf(current) < 0;
      var node = el("select", {
        id: id,
        "data-focus": focus,
        disabled: locked(),
        "aria-disabled": busy() ? "true" : null,
        on: { change: function (event) { drafts[key] = event.target.value; syncSet(key); } },
      });
      if (placeholder) {
        node.appendChild(el("option", { value: "", text: "Choose a value" }));
      }
      control.choices.forEach(function (choice) {
        node.appendChild(el("option", { value: choice, text: choiceLabel(control, choice) }));
      });
      node.value = control.choices.indexOf(current) >= 0 ? current : placeholder ? "" : control.choices[0];
      return labeled(labelText, node, id, action);
    }

    /**
     * Known model ids are offered as small buttons under the field rather than a datalist: a datalist
     * opens a native popup over the rows below it, and buttons stay inside the row and reach the keyboard.
     */
    function suggestionsNode(row, key, ids, label) {
      return el("div", { class: "suggestions", role: "group", "aria-label": "Known model ids for " + row.toolLabel }, ids.map(function (name) {
        return button(name, "suggest:" + key + "|" + name, function () {
          drafts[key] = name;
          var field = app.querySelector('[data-focus="txt:' + clean(key) + '"]');
          if (field) {
            field.value = name;
          }
          syncSet(key);
        }, { cls: "suggestion", aria: name + " for " + row.toolLabel + " (" + label + ")" });
      }));
    }

    function textInput(control, row, key, action) {
      var id = uid("txt");
      var suggestions = control.suggestions[row.tool] || [];
      starts[key] = "";
      var input = el("input", {
        type: "text",
        id: id,
        placeholder: "opus, or a full model id",
        value: draftValue(key, ""),
        spellcheck: "false",
        autocomplete: "off",
        maxlength: "200",
        "data-focus": "txt:" + key,
        disabled: locked(),
        "aria-disabled": busy() ? "true" : null,
        on: { input: function (event) { drafts[key] = event.target.value; syncSet(key); } },
      });
      var field = labeled("Default model for " + row.toolLabel, input, id, action);
      if (suggestions.length > 0) {
        field.appendChild(suggestionsNode(row, key, suggestions, control.label));
      }
      return field;
    }

    function rowActions(control, row) {
      var kids = [];
      var key = control.id + "|" + row.tool;
      if (control.kind === "text" && control.perTool && row.canSet) {
        kids.push(textInput(control, row, key, button("Set", "set:" + key, function () {
          var value = (drafts[key] || "").trim();
          if (value) {
            post({ type: "set", control: control.id, value: value, tool: row.tool });
          }
        }, {
          cls: "primary",
          aria: "Set for " + row.toolLabel + " (" + control.label + ")",
          ready: function () { return (draftValue(key, "") || "").trim() !== ""; },
        })));
      }
      if (control.kind === "choice" && control.perToolOverride && row.canSet) {
        var start = startFor(control, row.value);
        kids.push(select(control, key, "pick:" + key, start, control.label + " only for " + row.toolLabel, button("Set", "set:" + key, function () {
          post({ type: "set", control: control.id, value: draftValue(key, start), tool: row.tool });
        }, {
          cls: "primary",
          aria: "Set only for " + row.toolLabel + " (" + control.label + ")",
          ready: function () { return !!draftValue(key, start); },
        })));
      }
      if (row.removable) {
        kids.push(el("div", { class: "override" }, [
          text("p", row.removable.reason, "hint"),
          button("Remove this override", "remove:" + key, function () {
            post({ type: "removeOverride", control: control.id, tool: row.tool });
          }, { cls: row.removable.weakens ? "danger" : "", aria: "Remove this override for " + row.toolLabel + " (" + control.label + ")" }),
        ]));
      }
      return kids;
    }

    function rowNode(control, row) {
      var title = row.toolLabel + (row.surface === "cli" ? "" : " (" + row.surfaceLabel + ")");
      var body = [];
      if (row.value) {
        body.push(el("p", { class: "value" }, [text("span", "Current value: ", "label"), text("code", row.value, "chip")]));
      }
      if (row.state === "overridden-by" && row.layerValue) {
        body.push(el("p", { class: "value" }, [text("span", "The overriding value is ", "label"), text("code", row.layerValue, "chip"), doc.createTextNode(".")]));
      }
      if (row.fix) {
        body.push(text("p", "To fix: " + row.fix, "fix"));
      }
      var key = control.id + "|" + row.tool + "|" + row.surface;
      if (row.state === "not-settable" || row.state === "tool-not-installed") {
        // Nothing here can be changed, so the reason is folded with the notes instead of filling the card.
        if (row.detail || row.caveats.length > 0) {
          body.push(notesNode(key, title, control.label, row.caveats, row.detail, row.state === "not-settable" ? "Why it cannot be set" : "Details"));
        }
      } else {
        if (row.detail) {
          body.push(text("p", row.detail, "detail"));
        }
        if (row.caveats.length > 0) {
          body.push(notesNode(key, title, control.label, row.caveats, null, null));
        }
      }
      return el("li", { class: "row state-" + row.state }, [el("div", { class: "row-head" }, [text("strong", title), badge(row.badge)])].concat(body, rowActions(control, row)));
    }

    /** Caveats are background that repeats across rows, so they start folded; an opened one stays open across renders. */
    function notesNode(key, title, controlLabel, caveats, lead, label) {
      var visible = label || (caveats.length === 1 ? "1 note" : caveats.length + " notes");
      var summary = text("summary", visible);
      summary.setAttribute("data-focus", "notes:" + key);
      summary.setAttribute("aria-label", visible + " for " + title + " (" + controlLabel + ")");
      var kids = [summary, lead ? text("p", lead, "detail") : null];
      if (caveats.length > 0) {
        kids.push(el("ul", { class: "caveats", "aria-label": "Notes for " + title }, caveats.map(function (c) { return text("li", c); })));
      }
      return remembered(el("details", { class: "notes", open: openSources["notes:" + key] === true }, kids), "notes:" + key);
    }

    /** Keep a details element open across renders once the person opened it. */
    function remembered(details, key) {
      details.addEventListener("toggle", function () {
        if (details.open) {
          openSources[key] = true;
        } else {
          delete openSources[key];
        }
      });
      return details;
    }

    function sourcesNode(control) {
      var items = control.sources.map(function (s) {
        var lines = [
          text("p", s.keyLine, "key"),
          text("p", s.admitted ? "Takes effect: " + s.takesEffect : "Not settable: " + s.reason, "detail"),
          text("p", "Source: " + s.source, "detail"),
        ];
        if (s.weakens) {
          lines.push(text("p", "This write lowers a safety barrier for some values.", "hint"));
        }
        if (s.notes) {
          lines.push(text("p", s.notes, "detail"));
        }
        if (s.layers.length > 0) {
          lines.push(el("ul", { class: "caveats", "aria-label": "What can override " + s.name }, s.layers.map(function (l) {
            return text("li", l.kind + ": " + l.locator + ". " + l.fix);
          })));
        }
        if (s.canOpen) {
          lines.push(button("Open source for " + s.name, "src:" + s.write, function () {
            post({ type: "openSource", control: control.id, write: s.write });
          }, { aria: "Open source for " + s.name + " (" + control.label + (s.name === s.owner ? "" : ", " + s.owner) + ")" }));
        }
        return el("li", { class: "source" }, lines);
      });
      var summary = text("summary", "Show sources and exact keys");
      summary.setAttribute("data-focus", "sources:" + control.id);
      summary.setAttribute("aria-label", "Show sources and exact keys for " + control.label);
      return remembered(el("details", { class: "sources", open: openSources[control.id] === true }, [summary, el("ul", {}, items)]), control.id);
    }

    function applyAll(control) {
      if (control.perTool || control.choices.length === 0 || !control.canApply) {
        return null;
      }
      var first = null;
      control.rows.forEach(function (row) {
        if (!first && row.canSet && control.choices.indexOf(row.value) >= 0) {
          first = row.value;
        }
      });
      var key = control.id + "|*";
      var start = startFor(control, first);
      return el("div", { class: "apply" }, [
        select(control, key, "pick:" + key, start, "Every tool", button("Apply to every tool", "set:" + key, function () {
          post({ type: "set", control: control.id, value: draftValue(key, start), tool: null });
        }, {
          cls: "primary",
          aria: "Apply to every tool (" + control.label + ")",
          ready: function () { return !!draftValue(key, start); },
        })),
      ]);
    }

    function controlNode(control) {
      var headingId = uid("h");
      var kids = [text("h2", control.label)];
      kids[0].setAttribute("id", headingId);
      if (control.neverWritten.length > 0) {
        kids.push(text("p", "Never written as a default: " + control.neverWritten.join(", ") + ".", "hint"));
      }
      var apply = applyAll(control);
      if (apply) {
        kids.push(apply);
      }
      kids.push(el("ul", { class: "rows", "aria-label": control.label + " by tool" }, control.rows.map(function (row) { return rowNode(control, row); })));
      kids.push(el("div", { class: "card-foot" }, [
        sourcesNode(control),
        button("Reset " + control.label + " to what was there before", "reset:" + control.id, function () {
          post({ type: "reset", control: control.id, tool: null });
        }, { cls: "link" }),
      ]));
      return el("section", { class: "card", "data-card": control.id, "aria-labelledby": headingId }, kids);
    }

    /** The preview of a High-effort, Full-auto session is reference material: its heading is the summary that unfolds it. */
    function outcomeNode(outcome) {
      if (outcome.rows.length === 0) {
        return null;
      }
      var head = el("tr", {}, ["Tool", "Effort", "Approval"].map(function (name) { return el("th", { scope: "col", text: name }); }));
      var rows = outcome.rows.map(function (row) {
        return el("tr", {}, [el("th", { scope: "row", text: row.label }), text("td", row.effort), text("td", row.posture)]);
      });
      var summary = el("summary", { "data-focus": "outcome" }, [el("h2", { id: "outcome-h", text: outcome.title })]);
      var kids = [summary, el("div", { class: "scroll" }, [el("table", {}, [el("caption", { text: outcome.title, class: "visually-hidden" }), el("thead", {}, [head]), el("tbody", {}, rows)])])];
      (outcome.notes || []).forEach(function (note) {
        kids.push(text("p", note, "hint small"));
      });
      var details = remembered(el("details", { class: "outcome", open: openSources.outcome === true }, kids), "outcome");
      return el("section", { class: "card", "data-card": "outcome", "aria-labelledby": "outcome-h" }, [details]);
    }

    /** The visible notice. It carries no live role: the live regions below speak it once. */
    function noticeNode(notice) {
      if (!notice) {
        return null;
      }
      var kids = [text("p", notice.text)];
      if (notice.lines && notice.lines.length > 0) {
        kids.push(el("ul", {}, notice.lines.map(function (line) { return text("li", line); })));
      }
      return el("div", { class: "notice level-" + notice.level, "data-level": notice.level }, kids);
    }

    function errorNode(error) {
      return el("section", { class: "card error-card", "data-card": "error", role: "alert" }, [
        text("h2", error.title),
        text("p", error.message),
        text("p", "Run this command in a terminal to see the same result:"),
        el("pre", {}, [text("code", error.command)]),
        text("p", error.fix),
      ]);
    }

    function headerNode(m) {
      var logo = app.getAttribute("data-logo");
      return el("header", {}, [
        el("div", { class: "title" }, [
          logo ? el("img", { src: logo, alt: "", width: "28", height: "28" }) : null,
          el("div", { class: "title-text" }, [
            text("h1", "Nexus-Hub Settings"),
            text("p", "VS Code profile: " + m.header.profile + ". Platform: " + m.header.platform + ".", "hint small"),
          ]),
          button("Refresh", "refresh", function () { post({ type: "refresh" }); }, { keepEnabled: true }),
        ]),
        text("p", m.header.note, "hint"),
      ]);
    }

    function liveRegion(id, role, politeness) {
      var found = doc.getElementById(id);
      if (found) {
        return found;
      }
      var created = el("div", { id: id, class: "visually-hidden", role: role, "aria-live": politeness, "aria-atomic": "true" });
      (doc.body || app.parentNode).appendChild(created);
      return created;
    }

    function sentence(line) {
      return /[.!?]$/.test(line) ? line : line + ".";
    }

    /** Speak a new notice once. A render while busy repeats the old notice, so it is skipped and re-arms the next one. */
    function announce(next) {
      var status = liveRegion("live-status", "status", "polite");
      var alert = liveRegion("live-alert", "alert", "assertive");
      if (next.busy) {
        announced = "";
        return;
      }
      var notice = next.notice;
      var message = notice ? [notice.text].concat(notice.lines || []).map(sentence).join(" ") : "";
      var key = notice ? notice.level + "|" + message : "";
      if (key === announced) {
        return;
      }
      announced = key;
      status.textContent = "";
      alert.textContent = "";
      if (notice) {
        (notice.level === "error" ? alert : status).textContent = message;
      }
    }

    function emptyNode(m) {
      return text("p", m.busy ? "Loading the current settings..." : "No settings were reported. Choose Refresh to read them again.", m.busy ? "hint" : "notice level-warn");
    }

    /** What had focus: its data-focus key, its card, and the caret of a text field. */
    function focusState() {
      var active = doc.activeElement;
      if (!active || !active.getAttribute || !app.contains(active)) {
        return null;
      }
      var key = active.getAttribute("data-focus");
      if (!key) {
        return null;
      }
      var card = active.closest ? active.closest("[data-card]") : null;
      var caret = typeof active.selectionStart === "number" && active.type === "text" ? [active.selectionStart, active.selectionEnd] : null;
      return { key: key, card: card ? card.getAttribute("data-card") : null, caret: caret };
    }

    function clean(value) {
      return String(value).replace(/["\\]/g, "");
    }

    /** Put focus back on the same control; failing that on the card's heading; failing that on Refresh. */
    function restoreFocus(state) {
      if (!state) {
        return;
      }
      var exact = app.querySelector('[data-focus="' + clean(state.key) + '"]');
      var target = exact;
      if (!target && state.card) {
        var heading = app.querySelector('[data-card="' + clean(state.card) + '"] h2');
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          target = heading;
        }
      }
      if (!target) {
        target = app.querySelector('[data-focus="refresh"]');
      }
      if (target && target.focus) {
        target.focus();
        if (target === exact && state.caret && target.setSelectionRange) {
          target.setSelectionRange(state.caret[0], state.caret[1]);
        }
      }
    }

    function render(next) {
      var focus = focusState();
      model = next;
      sequence = 0;
      starts = {};
      var kids = [headerNode(next), noticeNode(next.notice)];
      if (next.readOnlyReason && !next.error) {
        kids.push(text("p", next.readOnlyReason, "notice level-warn"));
      }
      if (next.error) {
        kids.push(errorNode(next.error));
      } else if (next.controls.length === 0) {
        kids.push(emptyNode(next));
      } else {
        kids.push(outcomeNode(next.outcome));
        next.controls.forEach(function (control) { kids.push(controlNode(control)); });
      }
      while (app.firstChild) {
        app.removeChild(app.firstChild);
      }
      kids.forEach(function (kid) { if (kid) { app.appendChild(kid); } });
      app.setAttribute("aria-busy", next.busy ? "true" : "false");
      restoreFocus(focus);
      announce(next);
    }

    function onMessage(message) {
      if (message && message.type === "render" && message.model) {
        render(message.model);
      }
    }

    return { render: render, onMessage: onMessage, drafts: drafts };
  }

  function boot(win) {
    var host = win.acquireVsCodeApi();
    var panel = createPanel(win.document, function (message) { host.postMessage(message); });
    win.addEventListener("message", function (event) { panel.onMessage(event.data); });
    host.postMessage({ type: "ready" });
    return panel;
  }

  return { createPanel: createPanel, boot: boot };
});
