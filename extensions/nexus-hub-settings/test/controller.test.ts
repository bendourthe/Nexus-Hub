import { beforeEach, describe, expect, it, vi } from "vitest";
import { ActionOutcome, ActionSpec, BridgeError } from "../src/cliBridge";
import { BridgeLike, ControllerDeps, SettingsController } from "../src/controller";
import type { ActionDoc, ActionResult, ExplainData, ShowReport } from "../src/types";
import { VSCODE_AUTO_APPROVE_WARNING, ViewModel } from "../src/viewModel";
import { explains, layers, showReport, withEditorWriteAdmitted } from "./fixtures";
import { stub } from "./vscode-stub";

const KEY = "chat.tools.global.autoApprove";

function result(over: Partial<ActionResult> = {}): ActionResult {
  return {
    tool: "claude", write: "claude.posture", file: "~/.claude/settings.json", key_path: ["permissions", "defaultMode"],
    status: "would-write", detail: "", new: { present: true, value: "bypassPermissions" }, ...over,
  };
}

function outcome(over: Partial<ActionDoc> = {}, exitCode = 0): ActionOutcome {
  return {
    exitCode,
    message: "",
    doc: { schema_version: 1, action: "set", exit_code: exitCode, confirmation: { required: false, kind: null }, results: [], editor_writes: [], ...over },
  };
}

class FakeBridge implements BridgeLike {
  report: ShowReport = showReport();
  all: Record<string, ExplainData> = explains();
  calls: string[] = [];
  actions: ActionSpec[] = [];
  recorded: unknown[] = [];
  showError: unknown;
  recordError: Error | undefined;
  actionError: unknown;
  handler: (spec: ActionSpec) => ActionOutcome | Promise<ActionOutcome> = () => outcome();

  async show(): Promise<ShowReport> {
    this.calls.push("show");
    if (this.showError) {
      throw this.showError;
    }
    return structuredClone(this.report);
  }
  async explain(control: string): Promise<ExplainData> {
    this.calls.push(`explain:${control}`);
    return structuredClone(this.all[control] as ExplainData);
  }
  async action(spec: ActionSpec): Promise<ActionOutcome> {
    this.actions.push(spec);
    if (this.actionError) {
      throw this.actionError;
    }
    return this.handler(spec);
  }
  async recordEditorWrite(payload: unknown): Promise<void> {
    if (this.recordError) {
      throw this.recordError;
    }
    this.recorded.push(payload);
  }
  describe(): string {
    return "python nexus_hub_cli.py settings show --json";
  }
}

let bridge: FakeBridge;
let confirm: ReturnType<typeof vi.fn>;
let open: ReturnType<typeof vi.fn>;
let trusted: boolean;

function make(over: Partial<ControllerDeps> = {}): SettingsController {
  return new SettingsController({
    bridge,
    ui: { confirm: confirm as never, openExternal: open as never },
    inspect: (key) => layers(key, { registered: stub.defaults[key] !== undefined, globalValue: stub.user[key], workspaceValue: stub.workspace[key] }),
    isTrusted: () => trusted,
    project: () => "C:\\work\\project",
    profile: () => "Default",
    platform: "windows",
    ...over,
  });
}

beforeEach(() => {
  stub.reset();
  stub.defaults[KEY] = false;
  bridge = new FakeBridge();
  confirm = vi.fn(async () => true);
  open = vi.fn(async () => true);
  trusted = true;
});

describe("saved default synchronization", () => {
  it("reads live native acknowledgments into the same model exposed to the panel", async () => {
    const live = { connected: 2, applied: 2, reloadRequired: false }; const reader = vi.fn(async () => live);
    const controller = make({ liveEffort: reader }); const model = await controller.refresh();
    expect(reader).toHaveBeenCalled(); expect(model.liveEffort).toEqual(live);
  });
  function shared(value = "ultra"): void {
    const row = structuredClone(bridge.report.records.find((r) => r.control === "effort" && r.tool === "claude")!);
    bridge.report.records.push({ ...row, tool: "internal", value, state: "in-effect", writes: [] });
    bridge.all.effort!.control.values = ["low", "medium", "high", "xhigh", "max", "ultra"];
  }

  it("reapplies native drift once per distinct value without repeated attempts on a locked default", async () => {
    shared();
    const row = bridge.report.records.find((r) => r.control === "effort" && r.tool === "claude")!;
    Object.assign(row, { matches_default: false, mapped_effort: "max", value: "high", state: "in-effect" });
    bridge.handler = (spec) => outcome({ results: [result({ status: spec.dryRun ? "would-write" : "written" })] });
    const controller = make();
    await controller.synchronizeDefaults();
    expect(bridge.actions.filter((a) => !a.dryRun)).toHaveLength(1);
    await controller.synchronizeDefaults();
    expect(bridge.actions.filter((a) => !a.dryRun)).toHaveLength(1);
    row.value = "medium";
    await controller.synchronizeDefaults();
    expect(bridge.actions.filter((a) => !a.dryRun)).toHaveLength(2);
  });

  it("synchronizes editor overrides for a matching native default and refuses changes without trust", async () => {
    shared();
    bridge.report.records.filter((r) => r.control === "effort" && r.tool !== "internal").forEach((row) => { row.matches_default = true; });
    const sync = vi.fn().mockResolvedValue({ changed: [], issues: [] });
    const controller = make({ syncEditorEffort: sync });
    await controller.synchronizeDefaults();
    expect(sync).toHaveBeenCalledOnce();
    expect(bridge.actions).toHaveLength(0);
    trusted = false;
    await controller.synchronizeDefaults();
    expect(sync).toHaveBeenCalledOnce();
  });

  it("retries unchanged native drift after a transient failure and on explicit Refresh", async () => {
    shared();
    Object.assign(bridge.report.records.find((r) => r.control === "effort" && r.tool === "claude")!, { matches_default: false, mapped_effort: "max", value: "high", state: "in-effect" });
    bridge.actionError = new Error("temporary write failure");
    const controller = make();
    await controller.synchronizeDefaults();
    expect(controller.current().status).toBe("error");
    bridge.actionError = undefined;
    bridge.handler = (spec) => outcome({ results: [result({ status: spec.dryRun ? "would-write" : "written" })] });
    await controller.synchronizeDefaults();
    expect(bridge.actions.filter((a) => !a.dryRun)).toHaveLength(1);
    await controller.handle({ type: "refresh" });
    expect(bridge.actions.filter((a) => !a.dryRun)).toHaveLength(2);
  });
});

describe("reading", () => {
  it("shows the engine's truth and reads each control's description once", async () => {
    const controller = make();
    const model = await controller.refresh();

    expect(model.status).toBe("ready");
    expect(model.controls).toHaveLength(5);
    expect(bridge.calls.filter((c) => c.startsWith("explain:"))).toHaveLength(5);

    await controller.refresh();
    expect(bridge.calls.filter((c) => c.startsWith("explain:"))).toHaveLength(5);
    await controller.refresh(true);
    expect(bridge.calls.filter((c) => c.startsWith("explain:"))).toHaveLength(10);
  });

  it("shows one error card with the command to run, and no controls, when the command line fails", async () => {
    bridge.showError = new BridgeError("timeout", "timed out after 15 seconds", "python x settings show --json", "Run it in a terminal.");
    const controller = make();

    const model = await controller.refresh();

    expect(model).toMatchObject({ status: "error", controls: [], readOnly: true });
    expect(model.error).toMatchObject({ title: "The Nexus-Hub command timed out", command: "python x settings show --json", fix: "Run it in a terminal." });

    bridge.showError = undefined;
    expect((await controller.refresh()).status).toBe("ready");
  });

  it("uses the bridge's own command when an error carries none, and handles a non-bridge failure", async () => {
    bridge.showError = new BridgeError("no-python", "no python", "", "Install Python.");
    expect((await make().refresh()).error).toMatchObject({ title: "Python 3 was not found", command: "python nexus_hub_cli.py settings show --json" });
    bridge.showError = new Error("kaboom");
    expect((await make().refresh()).error).toMatchObject({ title: "The Nexus-Hub command failed", message: "kaboom" });
    bridge.showError = "text only";
    expect((await make().refresh()).error?.message).toBe("text only");
    bridge.showError = new BridgeError("argument", "bad", "c", "f");
    expect((await make().refresh()).error?.title).toBe("The request was not valid");
  });

  it("answers ready by loading once and by returning the current model afterwards", async () => {
    const controller = make();
    await controller.handle({ type: "ready" });
    const count = bridge.calls.length;
    await controller.handle({ type: "ready" });
    expect(bridge.calls.length).toBe(count);
    await controller.handle({ type: "refresh" });
    expect(bridge.calls.length).toBeGreaterThan(count);
  });

  it("marks the model untrusted when the workspace is not trusted", async () => {
    trusted = false;
    expect((await make().refresh()).readOnly).toBe(true);
  });
});

describe("serialization and busy state", () => {
  it("runs operations one at a time and publishes busy then idle", async () => {
    const controller = make();
    const seen: boolean[] = [];
    const subscription = controller.onChange((model) => seen.push(model.busy));
    const order: string[] = [];
    bridge.handler = async (spec) => {
      order.push(`start:${spec.action}:${spec.dryRun ? "dry" : "real"}`);
      await new Promise((resolve) => setTimeout(resolve, 15));
      order.push(`end:${spec.action}:${spec.dryRun ? "dry" : "real"}`);
      return outcome({ results: [result()] });
    };

    await Promise.all([
      controller.handle({ type: "set", control: "effort", value: "high", tool: null }),
      controller.handle({ type: "set", control: "effort", value: "low", tool: null }),
    ]);

    expect(order).toEqual([
      "start:set:dry", "end:set:dry", "start:set:real", "end:set:real",
      "start:set:dry", "end:set:dry", "start:set:real", "end:set:real",
    ]);
    expect(seen[0]).toBe(true);
    expect(seen.at(-1)).toBe(false);
    subscription.dispose();
    subscription.dispose();
    const count = seen.length;
    await controller.refresh();
    expect(seen.length).toBe(count);
  });

  it("keeps the queue alive after a failure", async () => {
    const controller = make();
    bridge.showError = new Error("first");
    await controller.refresh();
    bridge.showError = undefined;
    expect((await controller.refresh()).status).toBe("ready");
  });
});

describe("set", () => {
  it("plans with --dry-run, writes, and re-reads, without asking when nothing weakens safety", async () => {
    bridge.handler = () => outcome({ results: [result({ tool: "codex", write: "codex.effort", key_path: ["model_reasoning_effort"], status: "would-write" })] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "effort", value: "high", tool: null });

    expect(bridge.actions.map((a) => [a.action, a.dryRun ?? false, a.token === undefined])).toEqual([["set", true, true], ["set", false, true]]);
    expect(bridge.actions.every((a) => a.project === "C:\\work\\project")).toBe(true);
    expect(confirm).not.toHaveBeenCalled();
    expect(model.notice).toMatchObject({ level: "info", text: "Default effort saved. Mapped to native defaults for new sessions." });
  });

  it("asks first for a safety-weakening change, listing keys, VS Code's warning, and the Cannot remove items", async () => {
    bridge.handler = (spec) => outcome({ confirmation: { required: true, kind: spec.dryRun ? null : "confirmed" }, results: [result()] });
    const controller = make();
    await controller.refresh();

    await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    const request = confirm.mock.calls[0]![0] as { message: string; detail: string; confirmLabel: string };
    expect(request.message).toBe("Lower a safety barrier?");
    expect(request.detail).toContain("permissions.defaultMode");
    expect(request.detail).toContain(`"${VSCODE_AUTO_APPROVE_WARNING}"`);
    expect(request.detail).toContain("Still prompts or blocks (Claude Code):");
    expect(request.detail).toContain("Explicit ask rules and deny rules");
    expect(request.detail).toContain("A session that is already running keeps its current mode.");
    expect(bridge.actions[1]?.token).toEqual({ action: "set", control: "posture", value: "full-auto", tool: null });
  });

  it("writes nothing when the person cancels the confirmation", async () => {
    confirm.mockResolvedValue(false);
    bridge.handler = () => outcome({ confirmation: { required: true, kind: null }, results: [result()] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(bridge.actions).toHaveLength(1);
    expect(bridge.actions[0]?.dryRun).toBe(true);
    expect(model.notice).toMatchObject({ level: "info", text: "Cancelled. Nothing was written." });
    expect(stub.updates).toEqual([]);
  });

  it("omits the VS Code warning for a control other than posture", async () => {
    bridge.handler = () => outcome({ confirmation: { required: true, kind: null }, results: [result({ tool: "internal", write: "internal.git_guardrails", file: "~/.nexus-hub/guardrails.json", key_path: ["block_git_bypass_flags"], new: { present: true, value: false } })] });
    const controller = make();
    await controller.refresh();

    await controller.handle({ type: "set", control: "git_guardrails", value: "off", tool: null });

    const detail = (confirm.mock.calls[0]![0] as { detail: string }).detail;
    expect(detail).not.toContain("auto-approve switch");
    expect(detail).toContain("block_git_bypass_flags = false");
  });

  it("shows the engine's refusal (an agent session, or no person present) as an error", async () => {
    bridge.handler = (spec) => (spec.dryRun ? outcome({ confirmation: { required: true, kind: null }, results: [result()] }) : { exitCode: 3, doc: null, message: "nexus-hub settings: refused: CLAUDECODE is set" });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(model.notice).toMatchObject({ level: "error", text: expect.stringContaining("refused: CLAUDECODE is set") });
  });

  it("reports a planning failure from the command line", async () => {
    bridge.handler = () => ({ exitCode: 2, doc: null, message: "nexus-hub settings: unknown control" });
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "set", control: "effort", value: "high", tool: null })).notice).toMatchObject({ level: "error" });
  });

  it("explains when nothing can be written, listing every cell's reason", async () => {
    bridge.handler = () => outcome({ results: [result({ status: "not-settable", detail: "No Proof Record: not installed" }), result({ tool: "codex", write: "codex.effort", key_path: ["model_reasoning_effort"], status: "tool-not-installed", detail: "Codex is not installed" })] }, 4);
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "effort", value: "high", tool: null });

    expect(model.notice).toMatchObject({ level: "warn", text: "Nothing can be written for this choice." });
    expect(model.notice?.lines?.[0]).toContain("not settable: No Proof Record");
    expect(model.notice?.lines?.[1]).toContain("not installed: Codex is not installed");
    expect(bridge.actions).toHaveLength(1);
  });

  it("reports a partial write as a warning with every cell's status", async () => {
    bridge.handler = (spec) => outcome({ results: [result({ status: spec.dryRun ? "would-write" : "written" }), result({ tool: "codex", status: spec.dryRun ? "would-write" : "refused", detail: "config.toml does not parse" })] }, spec.dryRun ? 0 : 1);
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "effort", value: "high", tool: null });

    expect(model.notice).toMatchObject({ level: "warn" });
    expect(model.notice?.text).toContain("Some settings could not be applied");
    expect(model.notice?.lines?.join("\n")).toContain("refused: config.toml does not parse");
  });

  it("turns a command-line crash into the error card", async () => {
    bridge.actionError = new BridgeError("exit", "crashed", "python cli", "Fix it.");
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "set", control: "effort", value: "high", tool: null })).status).toBe("error");
  });
});

describe("VS Code writes", () => {
  const editorWrite = { tool: "vscode-copilot", write: "vscode-copilot.auto_approve", key: KEY, key_path: [KEY], value: true, weakens_safety: true, takes_effect: "next" };

  function admitted() {
    const variant = withEditorWriteAdmitted();
    bridge.report = variant.report;
    bridge.all = variant.explains;
    bridge.handler = (spec) => outcome({ confirmation: { required: true, kind: spec.dryRun ? null : "confirmed" }, results: [result()], editor_writes: [editorWrite] });
  }

  it("applies the engine's editor writes at the user layer and records each previous value", async () => {
    admitted();
    stub.user[KEY] = false;
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(stub.user[KEY]).toBe(true);
    expect(bridge.recorded).toEqual([{ write: "vscode-copilot.auto_approve", previous: { present: true, value: false }, new: true, profile: "Default" }]);
    expect(String((confirm.mock.calls[0]![0] as { detail: string }).detail)).toContain(`VS Code user settings  ${KEY} = true`);
    expect(model.notice?.level).toBe("info");
  });

  it("aborts before the engine writes a file when a workspace value would beat the user value", async () => {
    admitted();
    stub.workspace[KEY] = false;
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(model.notice).toMatchObject({ level: "warn", text: expect.stringContaining("overridden-by workspace setting") });
    expect(bridge.actions.map((a) => a.dryRun)).toEqual([true]);
    expect(confirm).not.toHaveBeenCalled();
    expect(stub.updates).toEqual([]);
  });

  it("skips a key whose extension is not installed and says so", async () => {
    admitted();
    bridge.handler = (spec) => outcome({ confirmation: { required: false, kind: null }, results: [result({ status: spec.dryRun ? "would-write" : "written" })], editor_writes: [editorWrite] });
    delete stub.defaults[KEY];
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "ask", tool: null });

    expect(model.notice?.lines?.some((l) => l.startsWith("skipped:") && l.includes("not installed or is disabled"))).toBe(true);
    expect(stub.updates).toEqual([]);
  });

  it("rolls back the file writes when VS Code refuses a key, and reports it", async () => {
    admitted();
    stub.failUpdate.add(KEY);
    bridge.handler = (spec) => {
      if (spec.action === "reset") {
        return outcome({ action: "reset", results: [result({ status: "restored" })], editor_restores: [] });
      }
      return outcome({ confirmation: { required: true, kind: spec.dryRun ? null : "confirmed" }, results: [result()], editor_writes: [editorWrite] });
    };
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(bridge.actions.map((a) => `${a.action}:${a.dryRun ? "dry" : "real"}`)).toEqual(["set:dry", "set:real", "reset:real"]);
    expect(bridge.actions[2]?.token).toEqual({ action: "reset", control: "posture", value: null, tool: null }); // the undo carries its own confirmation
    expect(model.notice).toMatchObject({ level: "error", text: expect.stringContaining("rolled back the changes it made for posture") });
    expect(model.notice?.lines?.join("\n")).toContain("restored");
    expect(KEY in stub.user).toBe(false);
  });

  it("rolls back when recording an editor write fails, putting the key back first", async () => {
    admitted();
    stub.user[KEY] = false;
    bridge.recordError = new BridgeError("exit", "record failed", "c", "f");
    bridge.handler = (spec) => (spec.action === "reset" ? outcome({ action: "reset", results: [], editor_restores: [] }) : outcome({ confirmation: { required: true, kind: null }, results: [result()], editor_writes: [editorWrite] }));
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null });

    expect(stub.user[KEY]).toBe(false);
    expect(model.notice?.text).toContain("could not be recorded");
    expect(bridge.actions.at(-1)?.action).toBe("reset");
  });

  it("reports an error card when the rollback itself cannot run", async () => {
    admitted();
    stub.failUpdate.add(KEY);
    bridge.handler = (spec) => outcome({ confirmation: { required: true, kind: null }, results: [result()], editor_writes: [editorWrite] });
    const controller = make();
    await controller.refresh();
    const original = bridge.action.bind(bridge);
    bridge.action = async (spec) => {
      if (spec.action === "reset") {
        throw new BridgeError("timeout", "slow", "c", "f");
      }
      return original(spec);
    };

    expect((await controller.handle({ type: "set", control: "posture", value: "full-auto", tool: null })).status).toBe("error");
  });
});

describe("reset", () => {
  const restoreEntry = { tool: "vscode-copilot", write: "vscode-copilot.auto_approve", key: KEY, key_path: [KEY], restore: { present: false }, was: { present: true, value: true }, profile: null };

  it("restores the files through the engine and the editor keys through the panel", async () => {
    stub.user[KEY] = true;
    bridge.handler = () => outcome({ action: "reset", results: [result({ status: "restored" })], editor_restores: [restoreEntry] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "reset", control: "posture", tool: null });

    expect(KEY in stub.user).toBe(false);
    expect(model.notice).toMatchObject({ level: "info", text: "Reset posture to what was there before." });
  });

  it("warns when an editor key changed since and was left alone", async () => {
    stub.user[KEY] = false;
    bridge.handler = () => outcome({ action: "reset", results: [result({ status: "restored" })], editor_restores: [restoreEntry] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "reset", control: "posture", tool: "claude" });

    expect(model.notice?.level).toBe("warn");
    expect(model.notice?.lines?.some((l) => l.includes("changed after Nexus-Hub wrote it"))).toBe(true);
    expect(bridge.actions[0]).toMatchObject({ action: "reset", tool: "claude" });
  });

  it("plans the reset first and asks no one when it only puts back a safe value", async () => {
    bridge.handler = (spec) => outcome({ action: "reset", confirmation: { required: false, kind: null }, results: [result({ status: spec.dryRun ? "would-restore" : "restored" })], editor_restores: [] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "reset", control: "effort", tool: null });

    expect(bridge.actions.map((a) => [a.action, a.dryRun ?? false, a.token === undefined])).toEqual([["reset", true, true], ["reset", false, true]]);
    expect(confirm).not.toHaveBeenCalled();
    expect(model.notice).toMatchObject({ level: "info", text: "Reset effort to what was there before." });
  });

  it("asks before putting back a value that lowers a safety barrier, then sends the confirmation with the reset", async () => {
    bridge.handler = (spec) =>
      outcome({
        action: "reset",
        confirmation: { required: true, kind: null },
        results: [result({ status: spec.dryRun ? "would-restore" : "restored", previous: { present: true, value: "bypassPermissions" }, new: { present: true, value: "default" } })],
        editor_restores: [],
      });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "reset", control: "posture", tool: "claude" });

    const request = confirm.mock.calls[0]![0] as { message: string; detail: string; confirmLabel: string };
    expect(request.message).toBe("Put back a lower safety barrier?");
    expect(request.detail).toContain('permissions.defaultMode -> "bypassPermissions"');
    expect(request.detail).toContain("Still prompts or blocks (Claude Code)");
    expect(bridge.actions[0]).toMatchObject({ action: "reset", dryRun: true });
    expect(bridge.actions[0]?.token).toBeUndefined();
    expect(bridge.actions[1]).toMatchObject({ action: "reset", token: { action: "reset", control: "posture", value: null, tool: "claude" } });
    expect(bridge.actions[1]?.dryRun).toBeUndefined();
    expect(model.notice).toMatchObject({ level: "info", text: "Reset posture to what was there before." });
  });

  it("restores nothing and writes no confirmation when the person cancels", async () => {
    confirm.mockResolvedValue(false);
    bridge.handler = (spec) => outcome({ action: "reset", confirmation: { required: true, kind: null }, results: [result({ status: "would-restore", previous: { present: true, value: "bypassPermissions" } })], editor_restores: [] });
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "reset", control: "posture", tool: null });

    expect(bridge.actions).toHaveLength(1);
    expect(bridge.actions[0]?.dryRun).toBe(true);
    expect(model.notice).toMatchObject({ level: "info", text: "Cancelled. Nothing was restored." });
  });

  it("names a VS Code key that a reset would put back", async () => {
    bridge.handler = () => outcome({ action: "reset", confirmation: { required: true, kind: null }, results: [result({ status: "would-editor-restore" })], editor_restores: [restoreEntry] });
    stub.user[KEY] = true;
    const controller = make();
    await controller.refresh();

    await controller.handle({ type: "reset", control: "posture", tool: null });

    expect((confirm.mock.calls[0]![0] as { detail: string }).detail).toContain(`VS Code user settings  ${KEY} -> (not set)`);
  });

  it("shows the engine's refusal when a reset is not allowed", async () => {
    bridge.handler = (spec) => (spec.dryRun ? outcome({ action: "reset", confirmation: { required: true, kind: null }, results: [result({ status: "would-restore", previous: { present: true, value: "bypassPermissions" } })] }) : { exitCode: 3, doc: null, message: "refused: CLAUDECODE is set" });
    const controller = make();
    await controller.refresh();

    expect((await controller.handle({ type: "reset", control: "posture", tool: null })).notice).toMatchObject({ level: "error", text: "refused: CLAUDECODE is set" });
  });

  it("says when there is nothing to reset", async () => {
    bridge.handler = () => outcome({ action: "reset", results: [], editor_restores: [] }, 4);
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "reset", control: "effort", tool: null })).notice?.text).toContain("Nothing to reset");
  });

  it("reports a refused key (changed on disk since) as a warning", async () => {
    bridge.handler = () => outcome({ action: "reset", results: [result({ status: "refused", detail: "changed since Nexus-Hub wrote it" })], editor_restores: [] }, 1);
    const controller = make();
    await controller.refresh();
    const model = await controller.handle({ type: "reset", control: "effort", tool: null });
    expect(model.notice?.level).toBe("warn");
    expect(model.notice?.lines?.[0]).toContain("refused: changed since");
  });

  it("surfaces an engine refusal or crash", async () => {
    bridge.handler = () => ({ exitCode: 2, doc: null, message: "unreadable record" });
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "reset", control: "effort", tool: null })).notice).toMatchObject({ level: "error", text: "unreadable record" });
    bridge.actionError = new BridgeError("exit", "crashed", "c", "f");
    expect((await controller.handle({ type: "reset", control: "effort", tool: null })).status).toBe("error");
  });
});

describe("remove override", () => {
  const removal = (status: string) => outcome({ action: "remove-override", results: [result({ tool: "claude", write: "claude.effort_env", file: "~/.claude/settings.json", key_path: ["env", "CLAUDE_CODE_EFFORT_LEVEL"], status })] });

  it("confirms, passes the one-time token, and removes the key", async () => {
    bridge.handler = (spec) => removal(spec.dryRun ? "would-remove" : "removed");
    const controller = make();
    await controller.refresh();

    const model = await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" });

    const request = confirm.mock.calls[0]![0] as { message: string; detail: string };
    expect(request.message).toBe("Remove this override?");
    expect(request.detail).toContain("env.CLAUDE_CODE_EFFORT_LEVEL");
    expect(request.detail).toContain("Reset restores it exactly as it was.");
    expect(request.detail).not.toContain("Still prompts or blocks");
    expect(bridge.actions[1]?.token).toEqual({ action: "remove-override", control: "effort", value: null, tool: "claude" });
    expect(model.notice).toMatchObject({ level: "info", text: "Removed the override for effort. New sessions only." });
  });

  it("lists the Cannot remove items when the removed key guards safety", async () => {
    const report = showReport();
    const record = report.records.find((r) => r.control === "effort" && r.tool === "claude")!;
    record.removable_override = { id: "claude.disable_bypass", weakens_safety: true, reason: "Blocks bypassPermissions." };
    bridge.report = report;
    bridge.handler = (spec) => removal(spec.dryRun ? "would-remove" : "removed");
    const controller = make();
    await controller.refresh();

    await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" });

    expect((confirm.mock.calls[0]![0] as { detail: string }).detail).toContain("Still prompts or blocks (Claude Code):");
  });

  it("writes nothing when cancelled, and reports a dry run that would remove nothing", async () => {
    confirm.mockResolvedValue(false);
    bridge.handler = (spec) => removal(spec.dryRun ? "would-remove" : "removed");
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).notice?.text).toBe("Cancelled. Nothing was removed.");
    expect(bridge.actions).toHaveLength(1);

    bridge.handler = () => removal("absent");
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).notice).toMatchObject({ level: "warn", text: "Nothing was removed." });
  });

  it("refuses when the row no longer offers a removal, and surfaces engine failures", async () => {
    const controller = make();
    await controller.refresh();
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "codex" })).notice?.text).toContain("no override to remove");

    bridge.handler = () => ({ exitCode: 2, doc: null, message: "unknown tool" });
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).notice?.level).toBe("error");

    bridge.handler = (spec) => (spec.dryRun ? removal("would-remove") : { exitCode: 3, doc: null, message: "refused: agent" });
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).notice?.text).toBe("refused: agent");

    bridge.actionError = new BridgeError("exit", "crash", "c", "f");
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).status).toBe("error");
  });

  it("reports a command crash during the real removal", async () => {
    const controller = make();
    await controller.refresh();
    let calls = 0;
    bridge.action = async (spec) => {
      calls += 1;
      if (calls === 1) {
        return removal("would-remove");
      }
      throw new BridgeError("timeout", "slow", "c", "f");
    };
    expect((await controller.handle({ type: "removeOverride", control: "effort", tool: "claude" })).status).toBe("error");
  });
});

describe("opening sources", () => {
  it("opens only an allowlisted https link the engine reported, never one from the webview", async () => {
    const controller = make();
    await controller.refresh();

    await controller.handle({ type: "openSource", control: "posture", write: "claude.posture" });
    expect(open).toHaveBeenCalledWith("https://code.claude.com/docs/en/permission-modes");

    const model: ViewModel = await controller.handle({ type: "openSource", control: "git_guardrails", write: "internal.git_guardrails" });
    expect(open).toHaveBeenCalledTimes(1);
    expect(model.notice?.text).toContain("cannot be opened");

    bridge.all.posture!.writes.find((w) => w.id === "claude.posture")!.source.url = "https://evil.example/x";
    await controller.refresh(true);
    await controller.handle({ type: "openSource", control: "posture", write: "claude.posture" });
    expect(open).toHaveBeenCalledTimes(1);
  });
});


describe("fresh Codex agent", () => {
  it("reads configuration again before opening the native composer", async () => {
    const openCodex = vi.fn(async () => { expect(bridge.calls.filter((c) => c === "show")).toHaveLength(2); });
    const controller = make({ codexAvailable: () => true, ui: { confirm: confirm as never, openExternal: open as never, openCodex } });
    await controller.refresh();
    await controller.handle({ type: "newCodex" });
    expect(openCodex).toHaveBeenCalledOnce();
  });
  it("does not open a composer if fresh configuration cannot be read", async () => {
    const openCodex = vi.fn(async () => {});
    const controller = make({ codexAvailable: () => true, ui: { confirm: confirm as never, openExternal: open as never, openCodex } });
    await controller.refresh();
    bridge.showError = new Error("read failed");
    expect((await controller.handle({ type: "newCodex" })).status).toBe("error");
    expect(openCodex).not.toHaveBeenCalled();
  });
  it("reports an explicit native launch failure", async () => {
    const controller = make({ codexAvailable: () => true, ui: { confirm: confirm as never, openExternal: open as never, openCodex: async () => { throw new Error("missing command"); } } });
    await controller.refresh();
    expect((await controller.handle({ type: "newCodex" })).notice).toMatchObject({ level: "error", text: expect.stringContaining("Could not open") });
  });
  it("uses the native action only when trusted and installed", async () => {
    const openCodex = vi.fn(async () => {});
    let available = true;
    const controller = make({ codexAvailable: () => available, ui: { confirm: confirm as never, openExternal: open as never, openCodex } });
    expect((await controller.refresh()).codexAvailable).toBe(true);
    await controller.handle({ type: "newCodex" });
    expect(openCodex).toHaveBeenCalledTimes(1);
    available = false;
    await controller.handle({ type: "newCodex" });
    trusted = false;
    available = true;
    await controller.handle({ type: "newCodex" });
    expect(openCodex).toHaveBeenCalledTimes(1);
    expect(bridge.actions).toHaveLength(0);
  });
});

it("does not write Fast mode on an unsupported editor through the action API", async () => {
  const write=vi.fn(async () => {});
  const controller=make({editorCapabilities:()=>({extensionSettings:false,fastMode:false}),setFastMode:write});
  await controller.handle({type:"setFastMode",value:true});
  expect(write).not.toHaveBeenCalled();
  expect(controller.current().editorCapabilities?.fastMode).toBe(false);
});
