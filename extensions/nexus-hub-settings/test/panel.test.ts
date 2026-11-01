// @vitest-environment happy-dom
import * as fs from "node:fs";
import { createRequire } from "node:module";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ViewModel, buildModel, errorModel } from "../src/viewModel";
import { explains, layers, showReport } from "./fixtures";

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const panelModule = require("../media/panel.js") as {
  createPanel(doc: Document, post: (m: unknown) => void): { render(m: ViewModel): void; onMessage(m: unknown): void; drafts: Record<string, string> };
  boot(win: unknown): unknown;
};

let posted: Record<string, unknown>[];
let app: HTMLElement;
let panel: ReturnType<typeof panelModule.createPanel>;

function fresh(over: Partial<ViewModel> = {}, trusted = true): ViewModel {
  return { ...buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted, profile: "Default" }), ...over };
}

function button(label: string | RegExp): HTMLButtonElement {
  const found = [...app.querySelectorAll("button")].find((b) => (typeof label === "string" ? b.textContent === label : label.test(b.textContent ?? "")));
  if (!found) {
    throw new Error(`no button ${String(label)}`);
  }
  return found;
}

function type(input: HTMLInputElement, value: string): void {
  input.value = value;
  input.dispatchEvent(new Event("input", { bubbles: true }));
}

function pick(select: HTMLSelectElement, value: string): void {
  select.value = value;
  select.dispatchEvent(new Event("change", { bubbles: true }));
}

beforeEach(() => {
  document.body.innerHTML = '<main id="app" data-logo="vscode-webview://x/logo.png"><p>Loading</p></main>';
  app = document.getElementById("app") as HTMLElement;
  posted = [];
  panel = panelModule.createPanel(document, (m) => void posted.push(m as Record<string, unknown>));
});

describe("rendering", () => {
  it("draws the header, the what-a-session-starts-with table, and one section per control", () => {
    panel.render(fresh());

    expect(app.querySelector("h1")?.textContent).toBe("Nexus-Hub Settings");
    expect(app.textContent).toContain("applies to new sessions only");
    expect(app.querySelector("img")?.getAttribute("alt")).toBe("");
    expect([...app.querySelectorAll("section.card h2")].map((h) => h.textContent)).toEqual([
      "If you choose High effort and Full auto, a new session starts as:",
      "Default effort",
      "Default model",
      "Approval posture",
      "Commit attribution off",
      "Git-guardrails mode",
    ]);
    const table = app.querySelector("table")!;
    expect([...table.querySelectorAll("th[scope='col']")].map((c) => c.textContent)).toEqual(["Tool", "Effort", "Approval"]);
    expect(table.textContent).toContain("approval_policy = never; sandbox_mode = workspace-write");
  });

  it("shows each row's state as text plus an icon, with the value, the fix, and the caveats", () => {
    panel.render(fresh());
    const effort = app.querySelectorAll("section.card")[1]!;
    const claude = [...effort.querySelectorAll("li.row")].find((r) => r.textContent?.includes("Claude Code"))!;

    expect(claude.querySelector(".badge")?.textContent).toContain("Overridden by env CLAUDE_CODE_EFFORT_LEVEL");
    expect(claude.querySelector(".badge .icon")?.getAttribute("aria-hidden")).toBe("true");
    expect(claude.textContent).toContain("The overriding value is high.");
    expect(claude.textContent).toContain("To fix: Unset CLAUDE_CODE_EFFORT_LEVEL");
    expect(claude.querySelector("ul.caveats")?.getAttribute("aria-label")).toBe("Notes for Claude Code");
    expect(effort.textContent).toContain("Never written as a default: max.");
    const notSettable = [...effort.querySelectorAll("li.row")].find((r) => r.textContent?.includes("GitHub Copilot CLI"))!;
    expect(notSettable.querySelector(".badge")?.textContent).toContain("Not settable");
    expect(notSettable.textContent).toContain("No Proof Record");
  });

  it("states the current value and a surface label for a VS Code row", () => {
    panel.render(fresh());
    const model = app.querySelectorAll("section.card")[2]!;
    expect(model.textContent).toContain("Current value: opus");
    expect(app.textContent).toContain("(VS Code)");
  });

  it("lists sources and exact keys behind a details element with an open-source button only for allowlisted links", () => {
    panel.render(fresh());
    const posture = app.querySelectorAll("section.card")[3]!;
    const details = posture.querySelector("details.sources")!;
    expect(details.querySelector("summary")?.textContent).toBe("Show sources and exact keys");
    expect(details.textContent).toContain("permissions.defaultMode in ~/.claude/settings.json");
    expect(details.textContent).toContain("Source: code.claude.com, fetched");
    button("Open source for permissions.defaultMode").click();
    expect(posted.at(-1)).toEqual({ type: "openSource", control: "posture", write: "claude.posture" });
    const git = app.querySelectorAll("section.card")[5]!;
    expect(git.textContent).toContain("Enforced by the git-guardrails hook");
    expect(git.querySelector("details button")).toBeNull();
  });

  it("renders the error card with the command in a code element and no controls", () => {
    panel.render(errorModel("Default", "windows", { title: "Nexus-Hub is not installed", message: "not found", command: "python cli settings show --json", fix: "Install it." }));
    expect(app.querySelector("[role='alert'] h2")?.textContent).toBe("Nexus-Hub is not installed");
    expect(app.querySelector("pre code")?.textContent).toBe("python cli settings show --json");
    expect(app.querySelector("select, input")).toBeNull();
    expect(app.querySelectorAll("section.card")).toHaveLength(1);
  });

  it("shows a notice with every line and speaks it once through a live region, not through the notice itself", () => {
    panel.render(fresh({ notice: { level: "error", text: "refused", lines: ["a", "b"] } }));
    expect(app.querySelector(".notice")?.getAttribute("role")).toBeNull();
    expect(app.querySelector(".notice")?.getAttribute("data-level")).toBe("error");
    expect([...app.querySelectorAll(".notice li")].map((li) => li.textContent)).toEqual(["a", "b"]);
    expect(live("live-alert").textContent).toBe("refused. a. b.");
    expect(live("live-status").textContent).toBe("");
    panel.render(fresh({ notice: { level: "info", text: "saved" } }));
    expect(live("live-status").textContent).toBe("saved.");
    expect(live("live-alert").textContent).toBe("");
    panel.render(fresh({ notice: null }));
    expect(app.querySelector(".notice")).toBeNull();
    expect(live("live-status").textContent).toBe("");
  });

  it("creates the two live regions itself when the page shell did not, with the right roles", () => {
    panel.render(fresh({ notice: { level: "info", text: "saved" } }));
    expect(live("live-status").className).toBe("visually-hidden");
    expect(live("live-status").getAttribute("role")).toBe("status");
    expect(live("live-status").getAttribute("aria-live")).toBe("polite");
    expect(live("live-alert").getAttribute("role")).toBe("alert");
    expect(live("live-alert").getAttribute("aria-live")).toBe("assertive");
    expect(document.querySelectorAll("#live-status").length).toBe(1);
  });

  it("does not speak the same notice twice, and speaks an identical one again after a new action", () => {
    panel.render(fresh({ notice: { level: "info", text: "saved" } }));
    expect(live("live-status").textContent).toBe("saved.");
    live("live-status").textContent = "(spoken)";
    panel.render(fresh({ notice: { level: "info", text: "saved" } })); // a refresh draws the same notice
    expect(live("live-status").textContent).toBe("(spoken)");
    panel.render(fresh({ busy: true, notice: { level: "info", text: "saved" } })); // the next action starts
    expect(live("live-status").textContent).toBe("(spoken)");
    panel.render(fresh({ notice: { level: "info", text: "saved" } })); // the next action ends with the same words
    expect(live("live-status").textContent).toBe("saved.");
  });

  it("explains a read-only panel", () => {
    panel.render(fresh({}, false));
    expect(app.textContent).toContain("not trusted");
    expect(app.querySelector("p.notice")).not.toBeNull();
  });
});

describe("safety of rendered values", () => {
  it("never turns engine or file values into markup", () => {
    const hostile = '<img src=x onerror="alert(1)"><script>alert(2)</script>';
    const model = fresh();
    const row = model.controls[0]!.rows[0]!;
    row.fix = hostile;
    row.detail = hostile;
    row.layerValue = hostile;
    row.value = hostile;
    row.caveats = [hostile];
    row.badge.text = hostile;
    model.controls[0]!.sources[0]!.notes = hostile;
    model.notice = { level: "warn", text: hostile, lines: [hostile] };
    model.header.profile = hostile;
    model.controls[1]!.suggestions.claude = [hostile];

    panel.render(model);

    expect(app.querySelector("img[src='x']")).toBeNull();
    expect(app.querySelector("script")).toBeNull();
    expect(app.querySelectorAll("[onerror]")).toHaveLength(0);
    expect(app.innerHTML).toContain("&lt;img src=x");
  });

  it("builds the page without any HTML-string API", () => {
    const source = fs.readFileSync(path.join(here, "..", "media", "panel.js"), "utf8");
    expect(source).not.toMatch(/innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\s*\(|new Function|setAttribute\(\s*["']on/);
    expect(source).toContain("textContent");
  });
});

describe("accessibility", () => {
  it("labels every field, names every section, and gives every button text", () => {
    panel.render(fresh());

    for (const field of app.querySelectorAll("select, input")) {
      const id = field.getAttribute("id")!;
      expect(id).toBeTruthy();
      expect(app.querySelector(`label[for='${id}']`)?.textContent?.length).toBeGreaterThan(0);
    }
    const sections = [...app.querySelectorAll("section.card:not(.error-card)")];
    expect(sections.length).toBeGreaterThan(0);
    for (const section of sections) {
      expect(section.getAttribute("aria-labelledby")).toBeTruthy();
      expect(document.getElementById(section.getAttribute("aria-labelledby")!)?.tagName).toBe("H2");
    }
    expect(app.querySelectorAll("[aria-labeledby]")).toHaveLength(0);
    for (const b of app.querySelectorAll("button")) {
      expect(b.textContent?.length).toBeGreaterThan(0);
      expect(b.getAttribute("type")).toBe("button");
      expect(b.getAttribute("data-focus")).toBeTruthy();
    }
    expect(new Set([...app.querySelectorAll("[id]")].map((n) => n.id)).size).toBe(app.querySelectorAll("[id]").length);
  });

  it("marks risky choices in words, not only color", () => {
    panel.render(fresh());
    const options = [...app.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toContain("full-auto (lowers a safety barrier)");
    expect(options).toContain("off (lowers a safety barrier)");
    expect(options).toContain("high");
  });

  it("keeps focus on the same control, and a typed draft, across a re-render", () => {
    panel.render(fresh());
    const input = app.querySelector("input[type='text']") as HTMLInputElement;
    type(input, "claude-opus-5-5");
    input.focus();
    expect(document.activeElement?.getAttribute("data-focus")).toBe("txt:model|claude");

    panel.render(fresh());

    expect(document.activeElement?.getAttribute("data-focus")).toBe("txt:model|claude");
    expect((app.querySelector("input[type='text']") as HTMLInputElement).value).toBe("claude-opus-5-5");
  });

  it("gives a text field a datalist of known ids only where the engine supplied them", () => {
    panel.render(fresh());
    const inputs = [...app.querySelectorAll("input[type='text']")] as HTMLInputElement[];
    const claude = inputs.find((i) => i.getAttribute("data-focus")?.endsWith("|claude"))!;
    const codex = inputs.find((i) => i.getAttribute("data-focus")?.endsWith("|codex"))!;
    expect(document.getElementById(claude.getAttribute("list")!)?.querySelectorAll("option").length).toBeGreaterThan(0);
    expect(codex.hasAttribute("list")).toBe(false);
    expect(claude.getAttribute("autocomplete")).toBe("off");
    expect(claude.getAttribute("maxlength")).toBe("200");
  });
});

describe("keyboard focus across an action", () => {
  function focused(): string | null {
    return document.activeElement?.getAttribute("data-focus") ?? null;
  }

  it.each([
    ["Refresh", "refresh"],
    ["Apply to every tool", "set:effort|*"],
    ["Set only for Codex", "set:effort|codex"],
    ["Reset Approval posture to what was there before", "reset:posture"],
    ["Remove this override", "remove:effort|claude"],
  ])("keeps focus on %s through the busy render and the idle render that follow a click", (label, key) => {
    panel.render(fresh());
    const target = button(label);
    target.focus();
    expect(focused()).toBe(key);

    panel.render(fresh({ busy: true }));
    expect(focused()).toBe(key);
    expect(document.activeElement?.tagName).toBe("BUTTON");
    panel.render(fresh());

    expect(focused()).toBe(key);
    expect(document.activeElement).not.toBe(document.body);
  });

  it("keeps focus on a select and a text field, and the caret in the text field, through the busy cycle", () => {
    panel.render(fresh());
    const select = app.querySelector("select[data-focus='pick:effort|codex']") as HTMLSelectElement;
    select.focus();
    panel.render(fresh({ busy: true }));
    panel.render(fresh());
    expect(focused()).toBe("pick:effort|codex");

    const input = app.querySelector("input[type='text']") as HTMLInputElement;
    type(input, "claude-opus-5-5");
    input.focus();
    input.setSelectionRange(3, 7);
    panel.render(fresh({ busy: true }));
    panel.render(fresh());
    const again = app.querySelector("input[type='text']") as HTMLInputElement;
    expect(document.activeElement).toBe(again);
    expect([again.selectionStart, again.selectionEnd]).toEqual([3, 7]);
    expect(again.value).toBe("claude-opus-5-5");
  });

  it("moves focus to the card heading when the focused control no longer exists, never to the page body", () => {
    panel.render(fresh());
    button("Remove this override").focus();
    const after = fresh();
    after.controls[0]!.rows.forEach((row) => (row.removable = null));

    panel.render(after);

    const heading = app.querySelector("section[data-card='effort'] h2") as HTMLElement;
    expect(document.activeElement).toBe(heading);
    expect(heading.getAttribute("tabindex")).toBe("-1");
  });

  it("falls back to Refresh when the whole card is gone", () => {
    panel.render(fresh());
    button("Reset Approval posture to what was there before").focus();
    const after = fresh();
    after.controls = after.controls.filter((c) => c.id !== "posture");

    panel.render(after);

    expect(focused()).toBe("refresh");
  });

  it("does not take focus when nothing in the panel had it", () => {
    panel.render(fresh());
    (document.body as HTMLElement).focus();
    panel.render(fresh({ busy: true }));
    panel.render(fresh());
    expect(document.activeElement).toBe(document.body);
  });

  it("keeps the sources a person opened open across a render, and the others closed", () => {
    panel.render(fresh());
    const details = [...app.querySelectorAll("details.sources")] as HTMLDetailsElement[];
    details[1]!.open = true;
    details[1]!.dispatchEvent(new Event("toggle"));

    panel.render(fresh({ busy: true }));
    panel.render(fresh());

    const open = [...app.querySelectorAll("details.sources")].map((d) => (d as HTMLDetailsElement).open);
    expect(open).toEqual([false, true, false, false, false]);

    const again = app.querySelectorAll("details.sources")[1] as HTMLDetailsElement;
    again.open = false;
    again.dispatchEvent(new Event("toggle"));
    panel.render(fresh());
    expect([...app.querySelectorAll("details.sources")].some((d) => (d as HTMLDetailsElement).open)).toBe(false);
  });

  it("keeps focus on the summary of an open sources element", () => {
    panel.render(fresh());
    (app.querySelectorAll("details.sources summary")[2] as HTMLElement).focus();
    panel.render(fresh({ busy: true }));
    panel.render(fresh());
    expect(focused()).toBe("sources:posture");
  });
});

describe("choices that start empty and names that stay distinct", () => {
  it("does not preselect a value for a row whose own value is overridden: a placeholder is chosen instead", () => {
    panel.render(fresh());
    const effort = app.querySelectorAll("section.card")[1]!;
    const claude = effort.querySelector("select[data-focus='pick:effort|claude']") as HTMLSelectElement;

    expect(claude.value).toBe("");
    expect([...claude.options].map((o) => o.textContent)).toEqual(["Choose a value", "low", "medium", "high", "xhigh"]);
    const set = effort.querySelector("button[data-focus='set:effort|claude']") as HTMLButtonElement;
    expect(set.getAttribute("aria-disabled")).toBe("true");
    set.click();
    expect(posted).toEqual([]);

    pick(claude, "low");
    expect(set.hasAttribute("aria-disabled")).toBe(false);
    set.click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "effort", value: "low", tool: "claude" });
  });

  it("starts a row that already has a value at that value, with no placeholder", () => {
    panel.render(fresh());
    const codex = app.querySelector("select[data-focus='pick:effort|codex']") as HTMLSelectElement;
    expect(codex.value).toBe("high");
    expect([...codex.options].map((o) => o.textContent)).not.toContain("Choose a value");
  });

  it("starts apply-to-every-tool with a placeholder when no tool has a value to start from", () => {
    const model = fresh();
    model.controls[0]!.rows.forEach((row) => (row.value = null));
    panel.render(model);
    const all = app.querySelector("select[data-focus='pick:effort|*']") as HTMLSelectElement;
    expect(all.value).toBe("");
    const apply = app.querySelector("button[data-focus='set:effort|*']") as HTMLButtonElement;
    apply.click();
    expect(posted).toEqual([]);
    pick(all, "medium");
    apply.click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "effort", value: "medium", tool: null });
  });

  it("disables a model Set button until the field holds a value", () => {
    panel.render(fresh());
    const set = app.querySelector("button[data-focus='set:model|codex']") as HTMLButtonElement;
    const input = app.querySelector("input[data-focus='txt:model|codex']") as HTMLInputElement;
    expect(set.getAttribute("aria-disabled")).toBe("true");
    type(input, "gpt-6.2");
    expect(set.hasAttribute("aria-disabled")).toBe(false);
    type(input, "   ");
    expect(set.getAttribute("aria-disabled")).toBe("true");
  });

  it("gives every repeated action a name that says which control it belongs to, starting with its visible text", () => {
    panel.render(fresh());
    const names = [...app.querySelectorAll("button, summary")].map((b) => b.getAttribute("aria-label") ?? b.textContent ?? "");
    expect(new Set(names).size).toBe(names.length);
    for (const b of app.querySelectorAll("button, summary")) {
      const label = b.getAttribute("aria-label");
      if (label) {
        expect(label.startsWith((b.textContent ?? "").trim())).toBe(true);
      }
    }
  });

  it("names a source button after the tool when the catalog documents no key", () => {
    const model = fresh();
    const source = model.controls[0]!.sources.find((s) => s.canOpen)!;
    source.name = "VS Code Copilot Chat (VS Code)";
    source.owner = "VS Code Copilot Chat (VS Code)";
    source.keyLine = "No documented key for VS Code Copilot Chat (VS Code)";
    panel.render(model);
    expect(button("Open source for VS Code Copilot Chat (VS Code)")).toBeTruthy();
    expect(app.textContent).toContain("No documented key for VS Code Copilot Chat (VS Code)");
    expect(app.textContent).not.toContain("<none documented>");
  });

  it("writes the Not settable reasons once, under the table", () => {
    panel.render(fresh());
    const table = app.querySelector("table")!;
    expect(table.textContent).not.toContain("No Proof Record");
    const notes = [...app.querySelectorAll("section.card")[0]!.querySelectorAll("p.hint")].map((p) => p.textContent ?? "");
    expect(notes.length).toBeGreaterThan(0);
    expect(notes.every((n) => n.startsWith("Not settable for "))).toBe(true);
    const outcome = app.querySelectorAll("section.card")[0]!.textContent ?? "";
    for (const note of notes) {
      expect(outcome.split(note).length - 1).toBe(1);
    }
  });

  it("does not repeat the new-sessions line on every card", () => {
    panel.render(fresh());
    expect([...app.querySelectorAll("section.card p.hint")].filter((p) => p.textContent === "New sessions only.")).toHaveLength(0);
    expect(app.querySelector("header")?.textContent).toContain("applies to new sessions only");
  });

  it("says plainly when there is nothing to show instead of drawing an empty page", () => {
    panel.render(fresh({ controls: [], outcome: { title: "t", rows: [], notes: [] } }));
    expect(app.textContent).toContain("No settings were reported. Choose Refresh to read them again.");
    panel.render(fresh({ controls: [], outcome: { title: "t", rows: [], notes: [] }, busy: true }));
    expect(app.textContent).toContain("Loading the current settings...");
    expect(app.textContent).not.toContain("No settings were reported");
  });

  it("makes the secondary buttons plain and only the actions that write primary", () => {
    panel.render(fresh());
    const primary = [...app.querySelectorAll("button.primary")].map((b) => b.getAttribute("data-focus"));
    expect(primary.length).toBeGreaterThan(0);
    expect(primary.every((key) => key!.startsWith("set:"))).toBe(true);
    expect(button("Refresh").classList.contains("primary")).toBe(false);
    expect(button("Reset Approval posture to what was there before").classList.contains("primary")).toBe(false);
  });
});

describe("requests the panel posts", () => {
  it("applies a posture to every tool, using the chosen value", () => {
    panel.render(fresh());
    const posture = app.querySelectorAll("section.card")[3]!;
    const select = posture.querySelector("select") as HTMLSelectElement;
    pick(select, "full-auto");
    (posture.querySelector("button[data-focus='set:posture|*']") as HTMLButtonElement).click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "posture", value: "full-auto", tool: null });
  });

  it("starts the apply-all choice at the value the first settable tool already has", () => {
    panel.render(fresh());
    const posture = app.querySelectorAll("section.card")[3]!;
    expect((posture.querySelector("select") as HTMLSelectElement).value).toBe("accept-edits");
  });

  it("sets effort for one tool only", () => {
    panel.render(fresh());
    const effort = app.querySelectorAll("section.card")[1]!;
    const select = effort.querySelector("select[data-focus='pick:effort|codex']") as HTMLSelectElement;
    expect(select.value).toBe("high");
    pick(select, "low");
    button("Set only for Codex").click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "effort", value: "low", tool: "codex" });
  });

  it("sets a model per tool from the typed value, and ignores an empty one", () => {
    panel.render(fresh());
    button("Set for Codex").click();
    expect(posted).toEqual([]);
    const input = app.querySelector("input[data-focus='txt:model|codex']") as HTMLInputElement;
    type(input, "  gpt-6-astra  ");
    button("Set for Codex").click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "model", value: "gpt-6-astra", tool: "codex" });
  });

  it("offers remove-override only where the engine reported one, and reset and refresh everywhere", () => {
    panel.render(fresh());
    expect([...app.querySelectorAll("button")].filter((b) => b.textContent === "Remove this override")).toHaveLength(1);
    button("Remove this override").click();
    expect(posted.at(-1)).toEqual({ type: "removeOverride", control: "effort", tool: "claude" });
    button("Reset Approval posture to what was there before").click();
    expect(posted.at(-1)).toEqual({ type: "reset", control: "posture", tool: null });
    button("Refresh").click();
    expect(posted.at(-1)).toEqual({ type: "refresh" });
  });

  it("styles a safety-lowering removal as a danger action", () => {
    const model = fresh();
    model.controls[0]!.rows[0]!.removable = { tool: "claude", weakens: true, reason: "Blocks bypass." };
    panel.render(model);
    expect(button("Remove this override").getAttribute("class")).toBe("danger");
  });

  it("applies attribution and guardrails with their single or paired choices", () => {
    panel.render(fresh());
    const attribution = app.querySelectorAll("section.card")[4]!;
    expect((attribution.querySelector("select") as HTMLSelectElement).options).toHaveLength(1);
    (attribution.querySelector("button[data-focus='set:attribution|*']") as HTMLButtonElement).click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "attribution", value: "off", tool: null });
  });
});

function live(id: string): HTMLElement {
  return document.getElementById(id) as HTMLElement;
}

describe("disabled states", () => {
  it("really disables every action but Refresh when read-only, so nothing can change", () => {
    panel.render(fresh({}, false));
    const buttons = [...app.querySelectorAll("button")];
    expect(buttons.filter((b) => b.hasAttribute("disabled") && b.textContent !== "Refresh").length).toBe(buttons.length - 1);
    expect(button("Refresh").hasAttribute("disabled")).toBe(false);
    expect([...app.querySelectorAll("select, input")].every((f) => f.hasAttribute("disabled"))).toBe(true);
  });

  it("keeps Refresh enabled in the error state, where nothing else can be used", () => {
    panel.render(errorModel("Default", "windows", { title: "Nexus-Hub is not installed", message: "not found", command: "python cli", fix: "Install it." }));
    expect(button("Refresh").hasAttribute("disabled")).toBe(false);
    expect(button("Refresh").getAttribute("aria-disabled")).toBeNull();
    button("Refresh").click();
    expect(posted.at(-1)).toEqual({ type: "refresh" });
  });

  it("marks every control aria-disabled while busy but leaves it focusable, and ignores clicks", () => {
    panel.render(fresh({ busy: true }));
    expect(app.getAttribute("aria-busy")).toBe("true");
    const buttons = [...app.querySelectorAll("button")];
    expect(buttons.every((b) => !b.hasAttribute("disabled") && b.getAttribute("aria-disabled") === "true")).toBe(true);
    expect([...app.querySelectorAll("select, input")].every((f) => !f.hasAttribute("disabled") && f.getAttribute("aria-disabled") === "true")).toBe(true);
    for (const b of buttons) {
      b.click();
    }
    expect(posted).toEqual([]);
    panel.render(fresh());
    expect(app.getAttribute("aria-busy")).toBe("false");
    expect(button("Refresh").getAttribute("aria-disabled")).toBeNull();
  });

  it("does not offer apply for a control with no settable tool", () => {
    const model = fresh();
    model.controls[4]!.canApply = false;
    panel.render(model);
    expect(app.querySelector("button[data-focus='set:git_guardrails|*']")).toBeNull();
  });
});

describe("messages and boot", () => {
  it("renders only well-formed render messages", () => {
    panel.onMessage({ type: "render", model: fresh() });
    expect(app.querySelector("h1")).not.toBeNull();
    document.body.innerHTML = '<main id="app"></main>';
    app = document.getElementById("app") as HTMLElement;
    panel = panelModule.createPanel(document, () => undefined);
    panel.onMessage({ type: "render" });
    panel.onMessage({ type: "other", model: fresh() });
    panel.onMessage(null);
    expect(app.querySelector("h1")).toBeNull();
  });

  it("omits the logo when the host gave none", () => {
    document.body.innerHTML = '<main id="app"></main>';
    app = document.getElementById("app") as HTMLElement;
    panel = panelModule.createPanel(document, () => undefined);
    panel.render(fresh());
    expect(app.querySelector("img")).toBeNull();
  });

  it("boots by asking the host for the first render and listening for models", () => {
    const post = vi.fn();
    const listeners: Record<string, (e: { data: unknown }) => void> = {};
    const win = { document, acquireVsCodeApi: () => ({ postMessage: post }), addEventListener: (type: string, cb: (e: { data: unknown }) => void) => void (listeners[type] = cb) };

    panelModule.boot(win);

    expect(post).toHaveBeenCalledWith({ type: "ready" });
    listeners.message!({ data: { type: "render", model: fresh() } });
    expect(app.querySelector("h1")).not.toBeNull();
    (button("Refresh") as HTMLButtonElement).click();
    expect(post).toHaveBeenLastCalledWith({ type: "refresh" });
  });
});
