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

  it("shows notices with the right live-region role and every line", () => {
    panel.render(fresh({ notice: { level: "error", text: "refused", lines: ["a", "b"] } }));
    expect(app.querySelector(".notice")?.getAttribute("role")).toBe("alert");
    expect([...app.querySelectorAll(".notice li")].map((li) => li.textContent)).toEqual(["a", "b"]);
    panel.render(fresh({ notice: { level: "info", text: "saved" } }));
    expect(app.querySelector(".notice")?.getAttribute("role")).toBe("status");
    panel.render(fresh({ notice: null }));
    expect(app.querySelector(".notice")).toBeNull();
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
    for (const section of app.querySelectorAll("section[aria-labelledby]")) {
      expect(document.getElementById(section.getAttribute("aria-labelledby")!)?.tagName).toBe("H2");
    }
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

describe("disabled states", () => {
  it("disables every action while read-only or busy, except refresh while idle", () => {
    panel.render(fresh({}, false));
    const buttons = [...app.querySelectorAll("button")];
    expect(buttons.filter((b) => b.hasAttribute("disabled") && b.textContent !== "Refresh").length).toBe(buttons.length - 1);
    expect([...app.querySelectorAll("select, input")].every((f) => f.hasAttribute("disabled"))).toBe(true);

    panel.render(fresh({ busy: true }));
    expect(app.getAttribute("aria-busy")).toBe("true");
    expect(button("Refresh").hasAttribute("disabled")).toBe(true);
    panel.render(fresh());
    expect(app.getAttribute("aria-busy")).toBe("false");
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
