import { describe, expect, it } from "vitest";
import type { State } from "../src/types";
import {
  NEW_SESSIONS_NOTE,
  SOURCE_HOSTS,
  badgeFor,
  buildModel,
  emptyModel,
  errorModel,
  isAllowedSource,
  outcomeNotes,
  outcomeRows,
  overlayEditorRow,
  summarizePreferences,
} from "../src/viewModel";
import { EDITOR_REASON, explains, layers, showReport, withEditorWriteAdmitted } from "./fixtures";

const STATES: State[] = ["in-effect", "tool-default", "overridden-by", "not-settable", "not-covered", "unverified-for-version", "tool-not-installed", "cannot-detect"];

function model() {
  return buildModel({ report: showReport(), explains: explains(), inspect: (key) => layers(key), trusted: true, profile: "Default" });
}

describe("native effort equivalence", () => {
  it("uses engine mapping readback instead of comparing portable and native names", () => {
    const view = model();
    const effort = view.controls.find((c) => c.id === "effort")!;
    effort.choices.push("ultra");
    const row = effort.rows.find((r) => r.tool === "claude")!;
    effort.rows = [
      { ...row, tool: "internal", value: "ultra", state: "in-effect" },
      { ...row, value: "max", state: "in-effect", matchesDefault: true, mappedEffort: "max" },
    ];
    expect(summarizePreferences(view)).toMatchObject({ effort: "ultra", needsAttention: false });
    effort.rows[1]!.matchesDefault = false;
    expect(summarizePreferences(view).needsAttention).toBe(true);
  });

  it("preserves mapped readback fields in the model", () => {
    const report = showReport();
    const row = report.records.find((r) => r.control === "effort" && r.tool === "claude")!;
    row.matches_default = true;
    row.mapped_effort = "max";
    const view = buildModel({ report, explains: explains(), inspect: (key) => layers(key), trusted: true, profile: "Default" });
    expect(view.controls.find((c) => c.id === "effort")!.rows.find((r) => r.tool === "claude")).toMatchObject({ matchesDefault: true, mappedEffort: "max" });
  });
});

describe("state to badge mapping", () => {
  it("gives every engine state a badge with text and an icon (no colour-only signal)", () => {
    for (const state of STATES) {
      const badge = badgeFor(state);
      expect(badge.text.length).toBeGreaterThan(0);
      expect(badge.icon.length).toBeGreaterThan(0);
    }
  });

  it("names the layer, the uncovered models, and the version in the badge text", () => {
    expect(badgeFor("overridden-by", null, "env X (shell)").text).toBe("Overridden by env X (shell)");
    expect(badgeFor("overridden-by").text).toBe("Overridden by");
    expect(badgeFor("not-covered", "claude-opus-5-5").text).toBe("Not covered claude-opus-5-5");
    expect(badgeFor("unverified-for-version", "9.9").text).toBe("Unverified for version 9.9");
    expect(badgeFor("in-effect", "ignored").text).toBe("In effect");
  });

  it("maps each show record to exactly one badge naming its state", () => {
    const view = model();
    for (const control of view.controls) {
      for (const row of control.rows) {
        const record = showReport().records.find((r) => r.control === control.id && r.tool === row.tool && r.surface === row.surface)!;
        expect(row.state).toBe(record.state);
        expect(row.badge).toEqual(badgeFor(record.state, record.detail, record.layer));
      }
    }
  });
});

describe("building the model from engine output", () => {
  it("keeps catalog order and one control card per control", () => {
    expect(model().controls.map((c) => c.id)).toEqual(["effort", "model", "posture", "attribution", "git_guardrails"]);
  });

  it("surfaces the overriding layer, its value, the fix, and the remove button for the legacy variable", () => {
    const row = model().controls[0]!.rows.find((r) => r.tool === "claude")!;
    expect(row.state).toBe("overridden-by");
    expect(row.badge.text).toContain("env CLAUDE_CODE_EFFORT_LEVEL");
    expect(row.layerValue).toBe("high");
    expect(row.fix).toContain("Unset CLAUDE_CODE_EFFORT_LEVEL");
    expect(row.removable).toMatchObject({ tool: "claude", weakens: false });
    expect(row.canSet).toBe(true);
  });

  it("marks not-settable rows as not writable and keeps the reason", () => {
    const effort = model().controls[0]!;
    const copilot = effort.rows.find((r) => r.tool === "copilot-cli")!;
    expect(copilot.canSet).toBe(false);
    expect(copilot.detail).toContain("No Proof Record");
  });

  it("describes controls from the catalog: choices, free text, per-tool, and the weakening choices", () => {
    const [effort, modelControl, posture, attribution, git] = model().controls;
    expect(effort).toMatchObject({ kind: "choice", perTool: false, perToolOverride: true, neverWritten: ["max"] });
    expect(modelControl).toMatchObject({ kind: "text", perTool: true, choices: [] });
    expect(modelControl!.suggestions.claude!.length).toBeGreaterThan(0);
    expect(posture!.weakeningChoices).toEqual(["full-auto"]);
    expect(attribution!.choices).toEqual(["off"]);
    expect(git!.weakeningChoices).toEqual(["off"]);
    expect(git!.rows[0]!.toolLabel).toBe("Nexus-Hub (all tools)");
  });

  it("lists every write with its key, file, source host, and the overrides that can beat it", () => {
    const posture = model().controls[2]!;
    const claude = posture.sources.find((s) => s.write === "claude.posture")!;
    expect(claude).toMatchObject({ key: "permissions.defaultMode", admitted: true, canOpen: true, weakens: true });
    expect(claude.source).toContain("code.claude.com");
    expect(claude.layers.length).toBeGreaterThan(0);
    const gate = model().controls[4]!.sources[0]!;
    expect(gate.canOpen).toBe(false);
    expect(gate.source).toContain("docs/decisions");
    expect(gate.notes).toContain("Enforced by the git-guardrails hook");
    const blocked = posture.sources.find((s) => s.write === "copilot-cli.disable_bypass")!;
    expect(blocked.admitted).toBe(false);
    expect(blocked.reason).toContain("No Proof Record");
  });

  it("is read-only in an untrusted workspace and says why", () => {
    const view = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted: false, profile: "Work" });
    expect(view.readOnly).toBe(true);
    expect(view.readOnlyReason).toContain("not trusted");
    expect(view.header.profile).toBe("Work");
    expect(view.header.note).toBe(NEW_SESSIONS_NOTE);
  });

  it("omits a control the catalog could not explain rather than showing a partial card", () => {
    const partial = explains();
    delete partial.model;
    const view = buildModel({ report: showReport(), explains: partial, inspect: (k) => layers(k), trusted: true, profile: "Default" });
    expect(view.controls.map((c) => c.id)).not.toContain("model");
  });

  it("has an error state with one card and no controls, never cached values", () => {
    const view = errorModel("Default", "windows", { title: "t", message: "m", command: "c", fix: "f" });
    expect(view).toMatchObject({ status: "error", readOnly: true, controls: [], error: { command: "c" } });
    expect(emptyModel("Default", "linux").controls).toEqual([]);
  });

  it("falls back to the tool id and a placeholder source when the catalog names neither", () => {
    const report = showReport();
    delete report.tools.codex;
    const all = explains();
    const write = all.model!.writes.find((w) => w.id === "codex.model")!;
    write.source = {};
    write.source.url = "not a url";
    const view = buildModel({ report, explains: all, inspect: (k) => layers(k), trusted: true, profile: "Default" });
    const codexRow = view.controls.find((c) => c.id === "model")!.rows.find((r) => r.tool === "codex")!;
    expect(codexRow.toolLabel).toBe("codex");
    expect(view.controls.find((c) => c.id === "model")!.sources.find((s) => s.write === "codex.model")!.source).toContain("unknown host");
    write.source = {};
    const again = buildModel({ report, explains: all, inspect: (k) => layers(k), trusted: true, profile: "Default" });
    expect(again.controls.find((c) => c.id === "model")!.sources.find((s) => s.write === "codex.model")!.source).toBe("no source recorded");
  });
});

describe("the what-a-new-session-starts-with table", () => {
  it("is built from the catalog and states Not settable for cells without a proof", () => {
    const rows = outcomeRows(explains(), showReport());
    const byLabel = Object.fromEntries(rows.map((r) => [r.label, r]));
    expect(byLabel["Claude Code"]).toMatchObject({ effort: "modelSettings.<model-id>.effortLevel = high; effortLevel = high", posture: "permissions.defaultMode = bypassPermissions" });
    expect(byLabel.Codex).toMatchObject({ effort: "model_reasoning_effort = high", posture: "approval_policy = never; sandbox_mode = workspace-write" });
    expect(byLabel["GitHub Copilot CLI"]!.effort).toBe("Not settable");
    expect(byLabel["VS Code Copilot Chat (VS Code)"]!.posture).toBe("Not settable");
    expect(byLabel["Claude Code (VS Code)"]!.posture).toBe("Not settable");
  });

  it("writes each reason once under the table, naming every tool it applies to", () => {
    const notes = outcomeNotes(explains(), showReport());
    expect(notes.length).toBeGreaterThan(0);
    expect(new Set(notes).size).toBe(notes.length);
    expect(notes.every((n) => n.startsWith("Not settable for "))).toBe(true);
    const reasons = notes.map((n) => n.slice(n.indexOf(": ") + 2));
    expect(new Set(reasons).size).toBe(reasons.length);
    const view = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted: true, profile: "Default" });
    expect(view.outcome.notes).toEqual(notes);
  });

  it("never prints the no-key placeholder as if it were a key", () => {
    const view = buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted: true, profile: "Default" });
    const source = view.controls.find((c) => c.id === "effort")!.sources.find((s) => s.write === "vscode-copilot.effort")!;
    expect(source.key).toBe("<none documented>");
    expect(source.name).toBe("VS Code Copilot Chat (VS Code)");
    expect(source.keyLine).toBe("No documented key for VS Code Copilot Chat (VS Code)");
    const real = view.controls.find((c) => c.id === "effort")!.sources.find((s) => s.write === "claude.effort.top_level")!;
    expect(real.name).toBe("effortLevel");
    expect(real.keyLine).toContain("effortLevel in ~/.claude/settings.json");
  });

  it("says when a tool has no part in a control and when a choice maps to nothing", () => {
    const all = explains();
    all.effort!.writes = all.effort!.writes.filter((w) => w.tool !== "codex");
    const rows = outcomeRows(all, showReport());
    expect(rows.find((r) => r.label === "Codex")!.effort).toBe("Not part of this tool");
    const edited = explains();
    const write = edited.effort!.writes.find((w) => w.id === "codex.effort")!;
    delete write.value_map.high;
    expect(outcomeRows(edited, showReport()).find((r) => r.label === "Codex")!.effort).toBe("Not written for this choice");
  });

  it("prints a non-string mapped value as JSON", () => {
    const all = explains();
    const rows = outcomeRows({ ...all, posture: { ...all.posture!, writes: all.posture!.writes.map((w) => (w.id === "claude.posture" ? { ...w, value_map: { "full-auto": { a: 1 } } } : w)) } }, showReport());
    expect(rows.find((r) => r.label === "Claude Code")!.posture).toBe('permissions.defaultMode = {"a":1}');
  });
});

describe("VS Code rows the engine cannot read", () => {
  const { report, explains: all } = withEditorWriteAdmitted();
  const record = report.records.find((r) => r.control === "posture" && r.tool === "vscode-copilot")!;
  const writes = all.posture!.writes.filter((w) => w.id === "vscode-copilot.auto_approve");
  const KEY = "chat.tools.global.autoApprove";

  it("reads the user value and maps it back to the control value, with the policy caveat", () => {
    const row = overlayEditorRow(record, writes, () => layers(KEY, { globalValue: true }));
    expect(row).toMatchObject({ state: "in-effect", value: "full-auto" });
    expect(row.caveats.at(-1)).toContain("lock icon");
    expect(overlayEditorRow(record, writes, () => layers(KEY, { globalValue: false })).value).toBe("ask");
  });

  it("reports the tool default when nothing is set", () => {
    expect(overlayEditorRow(record, writes, () => layers(KEY))).toMatchObject({ state: "tool-default", value: null });
  });

  it("reports a workspace or folder value as the overriding layer with a fix", () => {
    const workspace = overlayEditorRow(record, writes, () => layers(KEY, { globalValue: true, workspaceValue: false }));
    expect(workspace).toMatchObject({ state: "overridden-by", layer: `VS Code workspace setting ${KEY}`, layerValue: "false" });
    expect(workspace.fix).toContain(".vscode/settings.json");
    expect(overlayEditorRow(record, writes, () => layers(KEY, { workspaceFolderValue: "x".repeat(200) })).layerValue).toHaveLength(80);
  });

  it("notes a value Nexus-Hub does not write, and treats an unregistered key as not installed", () => {
    const odd = overlayEditorRow(record, writes, () => layers(KEY, { globalValue: "weird" }));
    expect(odd.state).toBe("in-effect");
    expect(odd.value).toBe("weird");
    expect(odd.caveats.some((c) => c.includes("not a value Nexus-Hub writes"))).toBe(true);
    const missing = overlayEditorRow(record, writes, () => layers(KEY, { registered: false }));
    expect(missing).toMatchObject({ state: "tool-not-installed" });
    expect(missing.detail).toContain("not registered");
  });

  it("falls back to the engine's own fields when no write is admitted for the row", () => {
    expect(overlayEditorRow(record, [], () => layers(KEY))).toMatchObject({ state: "cannot-detect", detail: EDITOR_REASON });
  });

  it("is applied by the model to cannot-detect VS Code rows with an admitted write", () => {
    const view = buildModel({ report, explains: all, inspect: (key) => layers(key, { globalValue: true }), trusted: true, profile: "Default" });
    const row = view.controls.find((c) => c.id === "posture")!.rows.find((r) => r.tool === "vscode-copilot")!;
    expect(row).toMatchObject({ state: "in-effect", value: "full-auto", canSet: true });
  });
});

describe("source links", () => {
  it("allows only https links on the vendor documentation hosts", () => {
    expect(SOURCE_HOSTS.length).toBeGreaterThan(0);
    expect(isAllowedSource("https://code.claude.com/docs/en/settings")).toBe(true);
    expect(isAllowedSource("http://code.claude.com/docs")).toBe(false);
    expect(isAllowedSource("https://evil.example/docs")).toBe(false);
    expect(isAllowedSource("https://code.claude.com.evil.example/")).toBe(false);
    expect(isAllowedSource("https://user:pw@code.claude.com/")).toBe(false);
    expect(isAllowedSource("javascript:alert(1)")).toBe(false);
    expect(isAllowedSource("not a url")).toBe(false);
    expect(isAllowedSource(undefined)).toBe(false);
  });
});
