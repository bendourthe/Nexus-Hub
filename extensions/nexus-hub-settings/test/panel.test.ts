// @vitest-environment happy-dom
import * as fs from "node:fs";
import { createRequire } from "node:module";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ViewModel, buildModel, errorModel, summarizePreferences } from "../src/viewModel";
import { explains, layers, showReport } from "./fixtures";

const require = createRequire(import.meta.url);
const panelModule = require("../media/panel.js") as {
  createPanel(doc: Document, post: (m: unknown) => void): { render(m: ViewModel): void; onMessage(m: unknown): void; drafts: Record<string, string> };
  boot(win: unknown): unknown;
};
let posted: Record<string, unknown>[];
let app: HTMLElement;
let panel: ReturnType<typeof panelModule.createPanel>;

function fresh(over: Partial<ViewModel> = {}, trusted = true): ViewModel {
  const model = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted, profile: "Default" });
  const guard = model.controls.find((c) => c.id === "git_guardrails")!;
  for (const id of ["git_safety", "secret_scan", "edit_preservation", "large_file_warning"]) {
    model.controls.push({ ...guard, id, label: id, rows: guard.rows.map((row) => ({ ...row, value: "on", state: "in-effect" })) });
  }
  const effort = model.controls.find((c) => c.id === "effort")!;
  effort.choices = ["low", "medium", "high", "xhigh", "max", "ultra"];
  effort.rows.push({ ...effort.rows.find((row) => row.tool === "codex")!, tool: "internal", toolLabel: "Nexus-Hub", value: "high", state: "in-effect" });
  Object.assign(model, over);
  model.preferences = summarizePreferences(model);
  return model;
}
function button(label: string): HTMLButtonElement {
  const found = [...app.querySelectorAll<HTMLButtonElement>("button")].find((node) => node.textContent === label || (node.getAttribute("aria-labelledby") && app.querySelector("#" + node.getAttribute("aria-labelledby"))?.textContent === label));
  if (!found) { throw new Error(`Button not found: ${label}`); }
  return found;
}
function pick(value: string): void {
  app.querySelector<HTMLButtonElement>(`[role='radio'][data-value='${value}']`)?.click();
}
beforeEach(() => {
  document.body.innerHTML = '<main id="app" data-logo="vscode-webview://x/logo.png"></main><div id="live-status" role="status" aria-live="polite"></div><div id="live-alert" role="alert" aria-live="assertive"></div>';
  app = document.getElementById("app")!;
  posted = [];
  panel = panelModule.createPanel(document, (m) => void posted.push(m as Record<string, unknown>));
});

describe("shared settings view", () => {
  it.each(["low", "max", "ultra"])("saves %s and positions the endpoint fill", (value) => {
    const model = fresh();
    model.controls.find((c) => c.id === "effort")!.rows.find((row) => row.tool === "internal")!.value = value;
    model.preferences = summarizePreferences(model);
    panel.render(model);
    expect(app.querySelector("[aria-checked='true'][role='radio']")?.getAttribute("data-value")).toBe(value);
    expect(app.querySelector<HTMLElement>(".effort-choices")!.style.getPropertyValue("--effort-fill")).toBe(value === "low" ? "0%" : value === "ultra" ? "100%" : "80%");
    panel.render(fresh());
    pick(value);
    expect(posted.at(-1)).toEqual({ type: "set", control: "effort", value, tool: null });
  });
  it("shows one effort selector and five switches, without platform rows or model fields", () => {
    panel.render(fresh());
    expect(app.querySelector("h1")?.textContent).toBe("Nexus Settings");
    expect(app.querySelector("select")).toBeNull();
    expect(app.querySelectorAll("[role='radiogroup']")).toHaveLength(1);
    expect(app.querySelectorAll("[role='radio']")).toHaveLength(6);
    expect(app.querySelectorAll("button[role='switch']")).toHaveLength(5);
    expect(app.querySelector("table, input[type='text']")).toBeNull();
    expect(app.textContent).not.toMatch(/Claude Code|Codex|Copilot|Default model|attribution|Every tool|Current value|settings\.json/);
    expect(app.querySelector("img")?.getAttribute("src")).toBe("vscode-webview://x/logo.png");
    expect(app.querySelector("img")?.getAttribute("alt")).toBe("");
    expect(app.querySelector(".engine-update")).toBeNull();
    expect(app.querySelector(".effort-value")).toBeNull();
  });
  it("keeps all five guardrails visible when an old engine lacks four controls", () => {
    const oldModel = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted: true, profile: "Default" });
    panel.render(oldModel);
    const switches = [...app.querySelectorAll<HTMLButtonElement>("button[role='switch']")];
    expect(switches).toHaveLength(5);
    expect(switches.filter((node) => node.disabled)).toHaveLength(4);
    expect(button("Block Git bypass flags").disabled).toBe(false);
    expect(app.querySelectorAll(".engine-update")).toHaveLength(1);
    expect(app.querySelector(".engine-update")?.textContent).toBe("Update the Nexus-Hub settings engine to use all guardrail switches.");
    expect(document.getElementById("live-status")?.textContent).toContain("Update the Nexus-Hub settings engine");
    for (const node of switches.filter((item) => item.disabled)) { node.click(); }
    expect(posted).toEqual([]);
    expect(app.textContent).not.toMatch(/Claude Code|Codex|Copilot/);
  });
  it("starts at the saved shared choice instead of an overriding platform value", () => {
    const model = fresh();
    model.controls.find((c) => c.id === "effort")!.rows.find((row) => row.tool === "internal")!.value = "low";
    model.preferences = summarizePreferences(model);
    panel.render(model);
    expect(app.querySelector("[role='radio'][aria-checked='true']")?.getAttribute("data-value")).toBe("low");
    expect(app.querySelector("#effort-status")?.textContent).toContain("need synchronization");
  });
  it("auto-saves a changed effort once for all tools", () => {
    panel.render(fresh());
    pick("medium");
    expect(posted).toEqual([{ type: "set", control: "effort", value: "medium", tool: null }]);
    expect(app.querySelector(".save-state")?.textContent).toBe("Saving...");
    pick("low");
    expect(posted).toHaveLength(1);
  });
  it("keeps a native mapped effort in sync when a preference summary is absent", () => {
    const model = fresh();
    const effort = model.controls.find((c) => c.id === "effort")!;
    const shared = { ...effort.rows.find((row) => row.tool === "internal")!, value: "ultra" };
    const native = { ...effort.rows.find((row) => row.tool === "codex")!, value: "xhigh", state: "in-effect" as const, matchesDefault: true };
    effort.rows = [shared, native];
    delete model.preferences;
    panel.render(model);
    expect(app.querySelector("[role='radio'][aria-checked='true']")?.getAttribute("data-value")).toBe("ultra");
    expect(app.querySelector("#effort-status")?.textContent).toBe("Mapped to native defaults for new sessions.");
    expect(app.querySelector("#effort-status")?.classList.contains("attention")).toBe(false);
  });
  it("leaves the effort bar unselected when no shared or common default exists", () => {
    const model = fresh();
    model.controls.find((c) => c.id === "effort")!.rows.forEach((row) => { row.value = null; row.layerValue = null; });
    model.preferences = summarizePreferences(model);
    panel.render(model);
    expect(app.querySelector("[role='radio'][aria-checked='true']")).toBeNull();
    expect(app.querySelector("[role='radiogroup']")?.getAttribute("aria-labelledby")).toBe("effort-title");
  });
  it("does not send invalid choices", () => {
    const model = fresh();
    model.controls.find((c) => c.id === "effort")!.choices.push("bogus");
    panel.render(model);
    expect(app.querySelector("[data-value='bogus']")).toBeNull();
    pick("bogus");
    expect(posted).toEqual([]);
  });
  it("sends an explicit off request and waits for readback before changing a switch", () => {
    panel.render(fresh());
    const toggle = button("Git safety");
    expect(toggle.getAttribute("aria-checked")).toBe("true");
    toggle.click();
    expect(posted).toEqual([{ type: "set", control: "git_safety", value: "off", tool: null }]);
    expect(toggle.getAttribute("aria-checked")).toBe("true");
    toggle.click();
    expect(posted).toHaveLength(1);
    const changed = fresh();
    changed.controls.find((c) => c.id === "git_safety")!.rows[0]!.value = "off";
    panel.render(changed);
    expect(button("Git safety").getAttribute("aria-checked")).toBe("false");
  });
  it("keeps the existing bypass guard off by default and can enable it", () => {
    panel.render(fresh());
    const toggle = button("Block Git bypass flags");
    expect(toggle.getAttribute("aria-checked")).toBe("false");
    toggle.click();
    expect(posted.at(-1)).toEqual({ type: "set", control: "git_guardrails", value: "on", tool: null });
  });
  it("shows default-on guards as on before a preference has been written", () => {
    const model = fresh();
    const guard = model.controls.find((c) => c.id === "secret_scan")!;
    guard.rows[0]!.state = "tool-default";
    guard.rows[0]!.value = null;
    panel.render(model);
    expect(button("Secret scanning").getAttribute("aria-checked")).toBe("true");
  });
  it("disables unreadable guardrails instead of pretending their state is known", () => {
    const model = fresh();
    model.controls.find((c) => c.id === "secret_scan")!.rows[0]!.state = "cannot-detect";
    panel.render(model);
    expect(button("Secret scanning").disabled).toBe(true);
    button("Secret scanning").click();
    expect(posted).toEqual([]);
    expect(app.textContent).toContain("Unavailable. Refresh");
  });
  it("names every switch and associates its description", () => {
    panel.render(fresh());
    for (const toggle of app.querySelectorAll("[role='switch']")) {
      const name = app.querySelector("#" + toggle.getAttribute("aria-labelledby"));
      const description = app.querySelector("#" + toggle.getAttribute("aria-describedby"));
      expect(name?.textContent).toBeTruthy();
      expect(description?.textContent).toBeTruthy();
      expect(toggle.tagName).toBe("BUTTON");
    }
    expect(app.querySelector("[role='radiogroup']")?.getAttribute("aria-labelledby")).toBe("effort-title");
  });
  it("shows coverage limits as one short status, without a platform matrix", () => {
    panel.render(fresh());
    expect(app.querySelector("#effort-status")?.textContent).toContain("Some clients require a manual setting");
    expect(app.querySelector("table")).toBeNull();
  });
  it("does not repeat technical result lines in successful notices", () => {
    panel.render(fresh({ notice: { level: "info", text: "Saved.", lines: ["private setting detail"] } }));
    expect(app.querySelector(".notice")?.textContent).toBe("Saved.");
    expect(app.textContent).not.toContain("private setting detail");
  });
  it("keeps error details folded and inserts hostile data as text", () => {
    panel.render(fresh({ notice: { level: "error", text: '<img src=x onerror="bad()">', lines: ["<script>bad()</script>"] } }));
    expect(app.querySelector("script, img[src='x']")).toBeNull();
    expect(app.querySelector<HTMLDetailsElement>("details")!.open).toBe(false);
    expect(app.querySelector(".notice")?.textContent).toContain("<script>bad()</script>");
    expect(document.getElementById("live-alert")?.textContent).toContain("<img");
  });
  it("announces a notice once and clears it when the notice disappears", () => {
    panel.render(fresh({ notice: { level: "warn", text: "Not applied." } }));
    expect(document.getElementById("live-status")?.textContent).toBe("Not applied.");
    panel.render(fresh());
    expect(document.getElementById("live-status")?.textContent).toBe("");
  });
});

describe("workspace, busy and focus handling", () => {
  it("uses one tab stop and supports arrow, Home and End selection", () => {
    for (const [key, value] of [["ArrowRight", "xhigh"], ["ArrowLeft", "medium"], ["Home", "low"], ["End", "ultra"]]) {
      panel.render(fresh());
      const selected = app.querySelector<HTMLButtonElement>("[role='radio'][aria-checked='true']")!;
      expect(app.querySelectorAll("[role='radio'][tabindex='0']")).toHaveLength(1);
      selected.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
      expect(posted.at(-1)).toEqual({ type: "set", control: "effort", value, tool: null });
      expect(document.activeElement?.getAttribute("data-value")).toBe(value);
    }
  });
  it("does not save the current choice again", () => {
    panel.render(fresh());
    pick("high");
    expect(posted).toEqual([]);
  });
  it("allows only refresh in a read-only workspace", () => {
    panel.render(fresh({}, false));
    expect(app.textContent).toContain("Trust this workspace");
    expect([...app.querySelectorAll<HTMLButtonElement>("[role='switch']")].every((node) => node.disabled)).toBe(true);
    expect([...app.querySelectorAll<HTMLButtonElement>("[role='radio']")].every((node) => node.disabled)).toBe(true);
    button("Refresh").click();
    expect(posted).toEqual([{ type: "refresh" }]);
  });
  it("keeps controls focusable while busy and ignores all writes and refreshes", () => {
    panel.render(fresh({ busy: true }));
    expect(app.getAttribute("aria-busy")).toBe("true");
    expect([...app.querySelectorAll<HTMLButtonElement>("button")].every((node) => !node.disabled && node.getAttribute("aria-disabled") === "true")).toBe(true);
    for (const node of app.querySelectorAll<HTMLButtonElement>("button")) { node.click(); }
    pick("medium");
    expect(posted).toEqual([]);
  });
  it("keeps effort focus through saving and restores a cancelled choice from readback", () => {
    panel.render(fresh());
    app.querySelector<HTMLButtonElement>("[data-value='medium']")!.focus();
    pick("medium");
    panel.render(fresh({ busy: true }));
    expect(app.querySelector("[role='radio'][aria-checked='true']")?.getAttribute("data-value")).toBe("medium");
    panel.render(fresh({ notice: { level: "info", text: "Cancelled. Nothing was written." } }));
    expect(app.querySelector("[role='radio'][aria-checked='true']")?.getAttribute("data-value")).toBe("high");
    expect(document.activeElement?.getAttribute("data-focus")).toBe("effort:medium");
  });
  it("preserves switch focus across readback", () => {
    panel.render(fresh());
    button("Protect my edits").focus();
    panel.render(fresh({ busy: true }));
    panel.render(fresh());
    expect(document.activeElement?.getAttribute("data-focus")).toBe("toggle:edit_preservation");
  });
  it("falls back to refresh when the focused setting disappears", () => {
    panel.render(fresh());
    button("Protect my edits").focus();
    const model = fresh();
    model.controls = model.controls.filter((c) => c.id !== "edit_preservation");
    panel.render(model);
    expect(document.activeElement?.getAttribute("data-focus")).toBe("refresh");
  });
  it("does not take focus from outside the panel", () => {
    panel.render(fresh());
    (document.body as HTMLElement).focus();
    panel.render(fresh({ busy: true }));
    expect(document.activeElement).toBe(document.body);
  });
  it("shows an actionable error and leaves refresh available", () => {
    panel.render(errorModel("Default", "windows", { title: "Engine unavailable", message: "Could not read settings.", command: "python cli settings show", fix: "Install the engine." }));
    expect(app.querySelector("[role='alert'] h2")?.textContent).toBe("Engine unavailable");
    expect(app.querySelector("select, [role='switch']")).toBeNull();
    button("Refresh").click();
    expect(posted).toEqual([{ type: "refresh" }]);
  });
  it("distinguishes loading from an empty report", () => {
    panel.render(fresh({ controls: [], busy: true }));
    expect(app.textContent).toContain("Loading settings...");
    panel.render(fresh({ controls: [] }));
    expect(app.textContent).toContain("No settings were reported");
  });
});

describe("webview protocol", () => {
  it("ignores incomplete and unrelated render messages", () => {
    for (const message of [null, { type: "render" }, { type: "other", model: fresh() }, { type: "render", model: { controls: null } }]) { panel.onMessage(message); }
    expect(app.querySelector("h1")).toBeNull();
    panel.onMessage({ type: "render", model: fresh() });
    expect(app.querySelector("h1")).not.toBeNull();
  });
  it("boots once and asks the host to render", () => {
    const post = vi.fn();
    const listeners: Record<string, (event: { data: unknown }) => void> = {};
    panelModule.boot({ document, acquireVsCodeApi: () => ({ postMessage: post }), addEventListener: (name: string, cb: (event: { data: unknown }) => void) => void (listeners[name] = cb) });
    expect(post).toHaveBeenCalledWith({ type: "ready" });
    listeners.message!({ data: { type: "render", model: fresh() } });
    expect(app.querySelector("[role='radiogroup']")).not.toBeNull();
  });
  it("does not build HTML strings, invoke eval, or contact a network", () => {
    const source = fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), "../media/panel.js"), "utf8");
    expect(source).not.toMatch(/innerHTML|outerHTML|insertAdjacentHTML|\beval\(|\bfetch\(|XMLHttpRequest/);
  });
});
