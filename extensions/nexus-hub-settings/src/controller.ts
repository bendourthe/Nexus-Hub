import { ActionOutcome, ActionSpec, BridgeError } from "./cliBridge";
import {
  EditorLayers,
  EditorWriteError,
  RestoreReport,
  applyEditorWrites,
  inspectKey,
  precheckEditorWrites,
  restoreEditorWrites,
} from "./editorWrites";
import { Incoming } from "./messages";
import { ActionDoc, ActionResult, EditorRestore, EditorWrite, ExplainData, ShowReport } from "./types";
import {
  ErrorCard,
  Notice,
  VSCODE_AUTO_APPROVE_WARNING,
  ViewModel,
  buildModel,
  emptyModel,
  errorModel,
  isAllowedSource,
  summarizePreferences,
} from "./viewModel";

/**
 * The panel's brain, independent of any webview. It asks the engine for the truth
 * (`show`, `explain`), asks it to plan each change (`--dry-run`), checks every VS Code
 * key before the engine writes a file, asks a person to confirm anything that lowers a
 * safety barrier, then writes, records, and re-reads. Operations are serialized.
 */

export interface BridgeLike {
  show(project?: string): Promise<ShowReport>;
  explain(control: string, project?: string): Promise<ExplainData>;
  action(spec: ActionSpec): Promise<ActionOutcome>;
  recordEditorWrite(payload: { write: string; previous: { present: boolean; value?: unknown }; new: unknown; profile?: string }): Promise<void>;
  describe(args?: string[]): string;
}

export interface ConfirmRequest {
  message: string;
  detail: string;
  confirmLabel: string;
}

export interface UiLike {
  confirm(request: ConfirmRequest): Promise<boolean>;
  openExternal(url: string): Promise<boolean>;
}

export interface ControllerDeps {
  bridge: BridgeLike;
  ui: UiLike;
  inspect?: (key: string) => EditorLayers;
  isTrusted: () => boolean;
  project: () => string | undefined;
  profile: () => string;
  platform: string;
}

const MAX_LINES = 14;

const STATUS_TEXT: Record<string, string> = {
  written: "written",
  unchanged: "already set",
  "would-write": "would be written",
  "would-keep": "already set",
  removed: "removed",
  "would-remove": "would be removed",
  absent: "not present",
  restored: "restored",
  "editor-restore": "restored by the panel",
  deleted: "removed (the file was created by Nexus-Hub)",
  "not-settable": "not settable",
  "tool-not-installed": "not installed",
};

function statusLine(result: ActionResult, label: (tool: string) => string): string {
  const key = result.key_path ? result.key_path.join(".") : result.write;
  const text = STATUS_TEXT[result.status] ?? result.status;
  const detail = result.detail && !["written", "unchanged", "would-write", "would-keep"].includes(result.status) ? `: ${result.detail}` : "";
  return `${label(result.tool)}: ${key} - ${text}${detail}`;
}

function bridgeCard(error: unknown, command: string): ErrorCard {
  if (error instanceof BridgeError) {
    const title: Record<string, string> = {
      "no-install": "Nexus-Hub is not installed",
      "no-python": "Python 3 was not found",
      timeout: "The Nexus-Hub command timed out",
      spawn: "The Nexus-Hub command could not start",
      exit: "The Nexus-Hub command failed",
      json: "The Nexus-Hub command returned unexpected output",
      argument: "The request was not valid",
    };
    return { title: title[error.kind] ?? "The Nexus-Hub command failed", message: error.message, command: error.command || command, fix: error.fix };
  }
  return { title: "The Nexus-Hub command failed", message: error instanceof Error ? error.message : String(error), command, fix: "Reload the window and try again." };
}

export class SettingsController {
  private model: ViewModel;
  private report: ShowReport | null = null;
  private explains: Record<string, ExplainData> = {};
  private chain: Promise<unknown> = Promise.resolve();
  private readonly listeners: ((model: ViewModel) => void)[] = [];
  private readonly inspect: (key: string) => EditorLayers;

  constructor(private readonly deps: ControllerDeps) {
    this.inspect = deps.inspect ?? inspectKey;
    this.model = emptyModel(deps.profile(), deps.platform);
  }

  current(): ViewModel {
    return this.model;
  }

  onChange(listener: (model: ViewModel) => void): { dispose(): void } {
    this.listeners.push(listener);
    return {
      dispose: () => {
        const at = this.listeners.indexOf(listener);
        if (at >= 0) {
          this.listeners.splice(at, 1);
        }
      },
    };
  }

  private emit(): void {
    for (const listener of this.listeners) {
      listener(this.model);
    }
  }

  private enqueue<T>(work: () => Promise<T>): Promise<T> {
    const run = this.chain.then(async () => {
      this.model = { ...this.model, busy: true };
      this.emit();
      try {
        return await work();
      } finally {
        this.model = { ...this.model, busy: false };
        this.emit();
      }
    });
    this.chain = run.catch(() => undefined);
    return run;
  }

  /** Re-read everything from the engine. `full` also re-reads the catalog descriptions. */
  refresh(full = false): Promise<ViewModel> {
    return this.enqueue(() => this.reload(null, full));
  }

  handle(message: Incoming): Promise<ViewModel> {
    return this.enqueue(async () => {
      switch (message.type) {
        case "ready":
          return this.model.controls.length > 0 || this.model.status === "error" ? this.model : this.reload(null, true);
        case "refresh":
          return this.reload(null, true);
        case "set":
          return this.doSet(message.control, message.value, message.tool);
        case "reset":
          return this.doReset(message.control, message.tool);
        case "removeOverride":
          return this.doRemoveOverride(message.control, message.tool);
        case "openSource":
          return this.doOpenSource(message.control, message.write);
      }
    });
  }

  private label(tool: string): string {
    return this.report?.tools[tool]?.label ?? (tool === "internal" ? "Nexus-Hub" : tool);
  }

  private async reload(notice: Notice | null, full: boolean): Promise<ViewModel> {
    const profile = this.deps.profile();
    const project = this.deps.project();
    try {
      const report = await this.deps.bridge.show(project);
      const ids = [...new Set(report.records.map((record) => record.control))];
      if (full || ids.some((id) => !this.explains[id])) {
        const fetched = await Promise.all(ids.map(async (id) => [id, await this.deps.bridge.explain(id, project)] as const));
        this.explains = Object.fromEntries(fetched);
      }
      this.report = report;
      this.model = buildModel({ report, explains: this.explains, inspect: this.inspect, trusted: this.deps.isTrusted(), profile, notice });
    } catch (error) {
      this.report = null;
      this.model = errorModel(profile, this.deps.platform, bridgeCard(error, this.deps.bridge.describe()), notice);
    }
    return this.model;
  }

  private done(notice: Notice): Promise<ViewModel> {
    return this.reload(notice, false);
  }

  private fail(text: string, lines?: string[]): Promise<ViewModel> {
    return this.done({ level: "error", text, ...(lines ? { lines } : {}) });
  }

  private async attempt(spec: ActionSpec): Promise<{ outcome: ActionOutcome } | { error: Promise<ViewModel> }> {
    try {
      return { outcome: await this.deps.bridge.action({ ...spec, project: this.deps.project() }) };
    } catch (error) {
      this.report = null;
      return { error: Promise.resolve((this.model = errorModel(this.deps.profile(), this.deps.platform, bridgeCard(error, this.deps.bridge.describe())))) };
    }
  }

  private confirmText(control: string, doc: ActionDoc, editor: EditorWrite[]): ConfirmRequest {
    const lines = (doc.results ?? [])
      .filter((r) => ["would-write", "would-keep", "would-remove"].includes(r.status))
      .map((r) => `${this.label(r.tool)}: ${r.file}  ${(r.key_path ?? []).join(".")}${r.new?.present ? ` = ${JSON.stringify(r.new.value)}` : " (removed)"}`);
    lines.push(...editor.map((w) => `${this.label(w.tool)}: VS Code user settings  ${w.key} = ${JSON.stringify(w.value)}`));
    const tools = [...new Set([...(doc.results ?? []).filter((r) => !["not-settable", "tool-not-installed", "refused", "skipped"].includes(r.status)).map((r) => r.tool), ...editor.map((w) => w.tool)])];
    const parts = ["This change lowers a safety barrier for NEW sessions. Nexus-Hub will write:", ...lines.map((l) => `  - ${l}`)];
    if (control === "posture") {
      parts.push("", `VS Code's own warning for the auto-approve switch: "${VSCODE_AUTO_APPROVE_WARNING}".`);
    }
    for (const tool of tools) {
      const cannot = this.report?.tools[tool]?.cannot_remove ?? [];
      if (cannot.length > 0) {
        parts.push("", `Still prompts or blocks (${this.label(tool)}):`, ...cannot.map((item) => `  - ${item}`));
      }
    }
    parts.push("", "A session that is already running keeps its current mode.");
    return { message: "Lower a safety barrier?", detail: parts.join("\n"), confirmLabel: "Apply change" };
  }

  private async doSet(control: string, value: string, tool: string | null): Promise<ViewModel> {
    const planned = await this.attempt({ action: "set", control, value, tool, dryRun: true });
    if ("error" in planned) {
      return planned.error;
    }
    const plan = planned.outcome;
    if (!plan.doc) {
      return this.fail(plan.message);
    }
    const editor = plan.doc.editor_writes ?? [];
    const pre = precheckEditorWrites(editor, this.inspect);
    if (!pre.ok) {
      return this.done({ level: "warn", text: pre.message });
    }
    const results = plan.doc.results ?? [];
    const writable = results.some((r) => r.status === "would-write" || r.status === "would-keep") || pre.apply.length > 0;
    if (!writable) {
      return this.done({ level: "warn", text: "Nothing can be written for this choice.", lines: results.map((r) => statusLine(r, (t) => this.label(t))).slice(0, MAX_LINES) });
    }
    const required = plan.doc.confirmation?.required === true;
    if (required && !(await this.deps.ui.confirm(this.confirmText(control, plan.doc, pre.apply)))) {
      return this.done({ level: "info", text: "Cancelled. Nothing was written." });
    }
    const written = await this.attempt({ action: "set", control, value, tool, token: required ? { action: "set", control, value, tool } : undefined });
    if ("error" in written) {
      return written.error;
    }
    const out = written.outcome;
    if (!out.doc) {
      return this.fail(out.message);
    }
    const lines = (out.doc.results ?? []).map((r) => statusLine(r, (t) => this.label(t)));
    try {
      await applyEditorWrites(pre.apply, (write, previous) =>
        this.deps.bridge.recordEditorWrite({ write: write.write, previous, new: write.value, profile: this.deps.profile() }),
      this.inspect);
    } catch (error) {
      return this.rollback(control, tool, error);
    }
    lines.push(...pre.skipped.map((s) => `skipped: ${s.reason}`));
    const label = this.model.controls.find((item) => item.id === control)?.label ?? control;
    const exitNote = out.exitCode === 0 ? "" : " Some settings could not be applied.";
    const refreshed = await this.done({ level: out.exitCode === 0 ? "info" : "warn", text: `${label} saved.${exitNote}`, lines: lines.slice(0, MAX_LINES) });
    if (control === "effort" && tool === null && !refreshed.error) {
      const summary = summarizePreferences(refreshed);
      const confirmed = summary.effort === value;
      this.model = { ...refreshed, notice: { level: !confirmed || summary.needsAttention || out.exitCode !== 0 ? "warn" : "info", text: confirmed ? `Default effort saved.${exitNote} ${summary.effortStatus}` : "The saved effort could not be confirmed. Refresh and try again.", lines: lines.slice(0, MAX_LINES) } };
    }
    return this.model;
  }

  /** A VS Code write failed after the engine wrote files: undo the control and say so. */
  private async rollback(control: string, tool: string | null, error: unknown): Promise<ViewModel> {
    const reason = error instanceof EditorWriteError || error instanceof Error ? error.message : String(error);
    // The panel undoes its own change a moment after the person approved it, so this reset carries its own confirmation.
    const reset = await this.attempt({ action: "reset", control, tool, token: { action: "reset", control, value: null, tool } });
    if ("error" in reset) {
      return reset.error;
    }
    const doc = reset.outcome.doc;
    const reports = await restoreEditorWrites(doc?.editor_restores ?? [], this.deps.profile(), this.inspect);
    const lines = [...(doc?.results ?? []).map((r) => statusLine(r, (t) => this.label(t))), ...reports.map((r) => r.detail)];
    return this.fail(`${reason} Nexus-Hub rolled back the changes it made for ${control}.`, lines.slice(0, MAX_LINES));
  }

  /** What the person is asked before a reset puts back a value that lowers a safety barrier. */
  private confirmResetText(doc: ActionDoc): ConfirmRequest {
    const prior = (state: { present: boolean; value?: unknown } | undefined): string => (state?.present ? JSON.stringify(state.value) : "(not set)");
    const lines = (doc.results ?? [])
      .filter((r) => r.status === "would-restore")
      .map((r) => `${this.label(r.tool)}: ${r.file}  ${(r.key_path ?? []).join(".")} -> ${prior(r.previous)}`);
    lines.push(...(doc.editor_restores ?? []).map((e) => `${this.label(e.tool)}: VS Code user settings  ${e.key} -> ${prior(e.restore)}`));
    const parts = ["Putting these values back lowers a safety barrier for NEW sessions. Nexus-Hub will write:", ...lines.map((l) => `  - ${l}`)];
    const tools = [...new Set((doc.results ?? []).filter((r) => r.status === "would-restore").map((r) => r.tool))];
    for (const tool of tools) {
      const cannot = this.report?.tools[tool]?.cannot_remove ?? [];
      if (cannot.length > 0) {
        parts.push("", `Still prompts or blocks (${this.label(tool)}):`, ...cannot.map((item) => `  - ${item}`));
      }
    }
    parts.push("", "A session that is already running keeps its current mode.");
    return { message: "Put back a lower safety barrier?", detail: parts.join("\n"), confirmLabel: "Reset" };
  }

  private async doReset(control: string, tool: string | null): Promise<ViewModel> {
    const planned = await this.attempt({ action: "reset", control, tool, dryRun: true });
    if ("error" in planned) {
      return planned.error;
    }
    if (!planned.outcome.doc) {
      return this.fail(planned.outcome.message);
    }
    if ((planned.outcome.doc.results ?? []).length === 0) {
      return this.done({ level: "info", text: `Nothing to reset: Nexus-Hub has no recorded change for ${control}.` });
    }
    const required = planned.outcome.doc.confirmation?.required === true;
    if (required && !(await this.deps.ui.confirm(this.confirmResetText(planned.outcome.doc)))) {
      return this.done({ level: "info", text: "Cancelled. Nothing was restored." });
    }
    const reset = await this.attempt({ action: "reset", control, tool, token: required ? { action: "reset", control, value: null, tool } : undefined });
    if ("error" in reset) {
      return reset.error;
    }
    const out = reset.outcome;
    if (!out.doc) {
      return this.fail(out.message);
    }
    const restores: EditorRestore[] = out.doc.editor_restores ?? [];
    const reports: RestoreReport[] = await restoreEditorWrites(restores, this.deps.profile(), this.inspect);
    if ((out.doc.results ?? []).length === 0) {
      return this.done({ level: "info", text: `Nothing to reset: Nexus-Hub has no recorded change for ${control}.` });
    }
    const lines = [...(out.doc.results ?? []).map((r) => statusLine(r, (t) => this.label(t))), ...reports.filter((r) => r.status !== "restored").map((r) => r.detail)];
    const clean = out.exitCode === 0 && reports.every((r) => r.status === "restored");
    return this.done({ level: clean ? "info" : "warn", text: clean ? `Reset ${control} to what was there before.` : `Reset ${control}: some keys were left as you have them.`, lines: lines.slice(0, MAX_LINES) });
  }

  private async doRemoveOverride(control: string, tool: string): Promise<ViewModel> {
    const row = this.model.controls.find((c) => c.id === control)?.rows.find((r) => r.tool === tool && r.removable !== null);
    if (!row?.removable) {
      return this.done({ level: "warn", text: "There is no override to remove for that tool." });
    }
    const planned = await this.attempt({ action: "remove-override", control, tool, dryRun: true });
    if ("error" in planned) {
      return planned.error;
    }
    if (!planned.outcome.doc) {
      return this.fail(planned.outcome.message);
    }
    const results = planned.outcome.doc.results ?? [];
    if (!results.some((r) => r.status === "would-remove")) {
      return this.done({ level: "warn", text: "Nothing was removed.", lines: results.map((r) => statusLine(r, (t) => this.label(t))).slice(0, MAX_LINES) });
    }
    const cannot = row.removable.weakens ? (this.report?.tools[tool]?.cannot_remove ?? []) : [];
    const detail = [
      `Nexus-Hub will remove this key. ${row.removable.reason}`,
      ...results.filter((r) => r.status === "would-remove").map((r) => `  - ${this.label(r.tool)}: ${r.file}  ${(r.key_path ?? []).join(".")}`),
      "Reset restores it exactly as it was.",
      ...(cannot.length > 0 ? ["", `This lowers a safety barrier. Still prompts or blocks (${this.label(tool)}):`, ...cannot.map((item) => `  - ${item}`)] : []),
    ].join("\n");
    if (!(await this.deps.ui.confirm({ message: "Remove this override?", detail, confirmLabel: "Remove override" }))) {
      return this.done({ level: "info", text: "Cancelled. Nothing was removed." });
    }
    const removed = await this.attempt({ action: "remove-override", control, tool, token: { action: "remove-override", control, value: null, tool } });
    if ("error" in removed) {
      return removed.error;
    }
    if (!removed.outcome.doc) {
      return this.fail(removed.outcome.message);
    }
    const lines = (removed.outcome.doc.results ?? []).map((r) => statusLine(r, (t) => this.label(t)));
    return this.done({ level: removed.outcome.exitCode === 0 ? "info" : "warn", text: `Removed the override for ${control}. New sessions only.`, lines: lines.slice(0, MAX_LINES) });
  }

  private async doOpenSource(control: string, write: string): Promise<ViewModel> {
    const url = this.explains[control]?.writes.find((w) => w.id === write)?.source.url;
    if (!isAllowedSource(url)) {
      return this.done({ level: "warn", text: "That source cannot be opened from the panel." });
    }
    await this.deps.ui.openExternal(url);
    return this.model;
  }
}
