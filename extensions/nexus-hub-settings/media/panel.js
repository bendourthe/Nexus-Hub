// The Nexus-Hub Settings panel (webview side).
//
// It draws the view model the extension host sends, and posts back small request
// messages. It never builds markup from a string: every value from the engine is set
// with textContent or a plain attribute, so a hostile model id or file value cannot
// become markup or script. The host validates every request again.
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

    function disabled() {
      return !model || model.readOnly || model.busy;
    }

    function badge(b) {
      return el("span", { class: "badge tone-" + b.tone }, [
        el("span", { class: "icon " + (ICONS[b.icon] || "icon-dot"), "aria-hidden": "true" }),
        el("span", { text: b.text }),
      ]);
    }

    function button(label, focus, onClick, extra) {
      return el("button", { type: "button", text: label, "data-focus": focus, disabled: disabled() || (extra && extra.off), class: extra && extra.cls, on: { click: onClick } });
    }

    function labeled(labelText, control, id) {
      return el("div", { class: "field" }, [el("label", { for: id, text: labelText }), control]);
    }

    function choiceLabel(control, choice) {
      return control.weakeningChoices.indexOf(choice) >= 0 ? choice + " (lowers a safety barrier)" : choice;
    }

    function draftValue(key, fallback) {
      return Object.prototype.hasOwnProperty.call(drafts, key) ? drafts[key] : fallback;
    }

    function select(control, key, focus, fallback, labelText) {
      var id = uid("sel");
      var current = draftValue(key, fallback);
      var node = el("select", { id: id, "data-focus": focus, disabled: disabled(), on: { change: function (event) { drafts[key] = event.target.value; } } });
      control.choices.forEach(function (choice) {
        var option = el("option", { value: choice, text: choiceLabel(control, choice) });
        if (choice === current) {
          option.setAttribute("selected", "");
        }
        node.appendChild(option);
      });
      node.value = control.choices.indexOf(current) >= 0 ? current : control.choices[0];
      return labeled(labelText, node, id);
    }

    function textInput(control, row, key) {
      var id = uid("txt");
      var suggestions = control.suggestions[row.tool] || [];
      var listId = suggestions.length > 0 ? uid("dl") : null;
      var input = el("input", {
        type: "text",
        id: id,
        list: listId,
        value: draftValue(key, ""),
        spellcheck: "false",
        autocomplete: "off",
        maxlength: "200",
        "data-focus": "txt:" + key,
        disabled: disabled(),
        on: { input: function (event) { drafts[key] = event.target.value; } },
      });
      var field = labeled("Default model for " + row.toolLabel + " (an alias such as opus, or a full model id)", input, id);
      if (listId) {
        field.appendChild(el("datalist", { id: listId }, suggestions.map(function (name) { return el("option", { value: name }); })));
      }
      return field;
    }

    function rowActions(control, row) {
      var kids = [];
      var key = control.id + "|" + row.tool;
      if (control.kind === "text" && control.perTool && row.canSet) {
        kids.push(textInput(control, row, key));
        kids.push(button("Set for " + row.toolLabel, "set:" + key, function () {
          var value = (drafts[key] || "").trim();
          if (value) {
            post({ type: "set", control: control.id, value: value, tool: row.tool });
          }
        }));
      }
      if (control.kind === "choice" && control.perToolOverride && row.canSet) {
        var start = control.choices.indexOf(row.value) >= 0 ? row.value : control.choices[0];
        kids.push(select(control, key, "pick:" + key, start, "Only for " + row.toolLabel));
        kids.push(button("Set only for " + row.toolLabel, "set:" + key, function () {
          post({ type: "set", control: control.id, value: draftValue(key, start), tool: row.tool });
        }));
      }
      if (row.removable) {
        kids.push(text("p", row.removable.reason, "hint"));
        kids.push(button("Remove this override", "remove:" + key, function () {
          post({ type: "removeOverride", control: control.id, tool: row.tool });
        }, { cls: row.removable.weakens ? "danger" : "" }));
      }
      return kids;
    }

    function rowNode(control, row) {
      var title = row.toolLabel + (row.surface === "cli" ? "" : " (" + row.surfaceLabel + ")");
      var body = [];
      if (row.value) {
        body.push(text("p", "Current value: " + row.value, "value"));
      }
      if (row.state === "overridden-by" && row.layerValue) {
        body.push(text("p", "The overriding value is " + row.layerValue + ".", "value"));
      }
      if (row.fix) {
        body.push(text("p", "To fix: " + row.fix, "fix"));
      }
      if (row.detail) {
        body.push(text("p", row.detail, "detail"));
      }
      if (row.caveats.length > 0) {
        body.push(el("ul", { class: "caveats", "aria-label": "Notes for " + title }, row.caveats.map(function (c) { return text("li", c); })));
      }
      return el("li", { class: "row" }, [el("div", { class: "row-head" }, [text("strong", title), badge(row.badge)])].concat(body, rowActions(control, row)));
    }

    function sourcesNode(control) {
      var items = control.sources.map(function (s) {
        var lines = [
          text("p", s.key + " in " + s.file + " (" + s.tool + ", " + s.surfaceLabel + ")", "key"),
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
          lines.push(el("ul", { class: "caveats", "aria-label": "What can override " + s.key }, s.layers.map(function (l) {
            return text("li", l.kind + ": " + l.locator + ". " + l.fix);
          })));
        }
        if (s.canOpen) {
          lines.push(button("Open source for " + s.key, "src:" + s.write, function () {
            post({ type: "openSource", control: control.id, write: s.write });
          }));
        }
        return el("li", { class: "source" }, lines);
      });
      return el("details", { class: "sources" }, [text("summary", "Show sources and exact keys"), el("ul", {}, items)]);
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
      return el("div", { class: "apply" }, [
        select(control, key, "pick:" + key, first || control.choices[0], control.label),
        button("Apply to every tool", "set:" + key, function () {
          post({ type: "set", control: control.id, value: draftValue(key, first || control.choices[0]), tool: null });
        }),
      ]);
    }

    function controlNode(control) {
      var headingId = uid("h");
      var kids = [text("h2", control.label)];
      kids[0].setAttribute("id", headingId);
      kids.push(text("p", control.takesEffect, "hint"));
      if (control.neverWritten.length > 0) {
        kids.push(text("p", "Never written as a default: " + control.neverWritten.join(", ") + ".", "hint"));
      }
      var apply = applyAll(control);
      if (apply) {
        kids.push(apply);
      }
      kids.push(el("ul", { class: "rows", "aria-label": control.label + " by tool" }, control.rows.map(function (row) { return rowNode(control, row); })));
      kids.push(el("div", { class: "actions" }, [
        button("Reset " + control.label + " to what was there before", "reset:" + control.id, function () {
          post({ type: "reset", control: control.id, tool: null });
        }),
      ]));
      kids.push(sourcesNode(control));
      return el("section", { class: "card", "aria-labeledby": headingId }, kids);
    }

    function outcomeNode(outcome) {
      if (outcome.rows.length === 0) {
        return null;
      }
      var head = el("tr", {}, ["Tool", "Effort", "Approval"].map(function (name) { return el("th", { scope: "col", text: name }); }));
      var rows = outcome.rows.map(function (row) {
        return el("tr", {}, [el("th", { scope: "row", text: row.label }), text("td", row.effort), text("td", row.posture)]);
      });
      return el("section", { class: "card", "aria-labeledby": "outcome-h" }, [
        el("h2", { id: "outcome-h", text: outcome.title }),
        el("div", { class: "scroll" }, [el("table", {}, [el("caption", { text: outcome.title, class: "visually-hidden" }), el("thead", {}, [head]), el("tbody", {}, rows)])]),
      ]);
    }

    function noticeNode(notice) {
      if (!notice) {
        return null;
      }
      var kids = [text("p", notice.text)];
      if (notice.lines && notice.lines.length > 0) {
        kids.push(el("ul", {}, notice.lines.map(function (line) { return text("li", line); })));
      }
      return el("div", { class: "notice level-" + notice.level, role: notice.level === "error" ? "alert" : "status" }, kids);
    }

    function errorNode(error) {
      return el("section", { class: "card error-card", role: "alert" }, [
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
        el("div", { class: "title" }, [logo ? el("img", { src: logo, alt: "", width: "28", height: "28" }) : null, text("h1", "Nexus-Hub Settings")]),
        text("p", m.header.note, "hint"),
        text("p", "VS Code profile: " + m.header.profile + ". Platform: " + m.header.platform + ".", "hint"),
        button("Refresh", "refresh", function () { post({ type: "refresh" }); }, { off: !!(model && model.busy) }),
      ]);
    }

    function render(next) {
      var focus = doc.activeElement && doc.activeElement.getAttribute ? doc.activeElement.getAttribute("data-focus") : null;
      model = next;
      sequence = 0;
      var kids = [headerNode(next), noticeNode(next.notice)];
      if (next.readOnlyReason && !next.error) {
        kids.push(text("p", next.readOnlyReason, "notice level-warn"));
      }
      if (next.error) {
        kids.push(errorNode(next.error));
      } else {
        kids.push(outcomeNode(next.outcome));
        next.controls.forEach(function (control) { kids.push(controlNode(control)); });
      }
      while (app.firstChild) {
        app.removeChild(app.firstChild);
      }
      kids.forEach(function (kid) { if (kid) { app.appendChild(kid); } });
      app.setAttribute("aria-busy", next.busy ? "true" : "false");
      if (focus) {
        var again = app.querySelector('[data-focus="' + focus.replace(/["\\]/g, "") + '"]');
        if (again && again.focus) {
          again.focus();
        }
      }
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
