import type { LiveEffortSummary } from "./liveEffort";
import type { UiEffortSummary } from "./vendorUi";
import type { SessionDefaults } from "./sessionDefaults";
import { isDeepStrictEqual } from "node:util";
import type { EditorLayers } from "./editorWrites";
import { ExplainData, ExplainWrite, ShowRecord, ShowReport, State, Surface } from "./types";

/**
 * Pure mapping from the engine's JSON to what the webview draws. Nothing here talks
 * to VS Code, the file system, or the command line, so the panel's states can be
 * checked against `nexus-hub settings show --json` row for row.
 */

/**
 * The vendor's own wording for the VS Code Copilot Chat auto-approve switch
 * (`chat.tools.global.autoApprove`), from the settings reference fetched 2026-10-30 and
 * recorded in docs/policy/settings-control-contract.md. The configuration API skips the
 * dialog VS Code shows when a person flips the switch, so the panel repeats the warning.
 */
export const VSCODE_AUTO_APPROVE_WARNING = "Automatically approve all tools - this setting disables critical security protections";

/** The only hosts the "Open source" action may open. Every host is a vendor documentation site. */
export const SOURCE_HOSTS: readonly string[] = [
  "code.claude.com",
  "platform.claude.com",
  "code.visualstudio.com",
  "docs.github.com",
  "developers.openai.com",
  "learn.chatgpt.com",
];

export function isAllowedSource(url: string | undefined): url is string {
  if (!url) {
    return false;
  }
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" && parsed.username === "" && parsed.password === "" && SOURCE_HOSTS.includes(parsed.hostname);
  } catch {
    return false;
  }
}

export type Tone = "ok" | "info" | "warn" | "muted" | "error";
export type Icon = "check" | "dot" | "warning" | "lock" | "info" | "x" | "question";

export interface Badge {
  text: string;
  icon: Icon;
  tone: Tone;
}

const BADGES: Record<State, { text: string; icon: Icon; tone: Tone }> = {
  "in-effect": { text: "In effect", icon: "check", tone: "ok" },
  "tool-default": { text: "Tool default", icon: "dot", tone: "info" },
  "overridden-by": { text: "Overridden by", icon: "warning", tone: "warn" },
  "not-settable": { text: "Not settable", icon: "lock", tone: "muted" },
  "not-covered": { text: "Not covered", icon: "warning", tone: "warn" },
  "unverified-for-version": { text: "Unverified for version", icon: "question", tone: "warn" },
  "tool-not-installed": { text: "Not installed", icon: "x", tone: "muted" },
  "cannot-detect": { text: "Cannot detect", icon: "question", tone: "warn" },
};

/** One state in, one badge out. The text names the state, so color is never the only signal. */
export function badgeFor(state: State, detail?: string | null, layer?: string | null): Badge {
  const base = BADGES[state];
  if (state === "overridden-by") {
    return { ...base, text: layer ? `${base.text} ${layer}` : base.text };
  }
  if ((state === "not-covered" || state === "unverified-for-version") && detail) {
    return { ...base, text: `${base.text} ${detail}` };
  }
  return { ...base };
}

export interface RowView {
  tool: string;
  installed?: boolean;
  toolLabel: string;
  surface: Surface;
  surfaceLabel: string;
  state: State;
  badge: Badge;
  value: string | null;
  layerValue: string | null;
  fix: string | null;
  detail: string | null;
  caveats: string[];
  /** The row's tool can be written for this control (set is allowed for it). */
  canSet: boolean;
  removable: { tool: string; weakens: boolean; reason: string } | null;
  matchesDefault?: boolean;
  mappedEffort?: string;
}

export interface SourceView {
  write: string;
  tool: string;
  surfaceLabel: string;
  file: string;
  key: string;
  takesEffect: string;
  admitted: boolean;
  reason: string | null;
  source: string;
  canOpen: boolean;
  weakens: boolean;
  notes: string | null;
  layers: { kind: string; locator: string; fix: string }[];
  /** What to call this write in a button or a list: its key, or the tool and surface when no key is documented. */
  name: string;
  /** The one-line description of where the write goes. */
  keyLine: string;
  /** The tool and surface that own the write, which tells apart two writes that share a key name. */
  owner: string;
}

export interface ControlView {
  id: string;
  label: string;
  kind: "choice" | "text";
  choices: string[];
  weakeningChoices: string[];
  suggestions: Record<string, string[]>;
  perTool: boolean;
  perToolOverride: boolean;
  neverWritten: string[];
  canApply: boolean;
  takesEffect: string;
  rows: RowView[];
  sources: SourceView[];
}

export interface OutcomeRow {
  tool: string;
  label: string;
  effort: string;
  posture: string;
}

export interface Notice {
  level: "info" | "warn" | "error";
  text: string;
  lines?: string[];
}

export interface ErrorCard {
  title: string;
  message: string;
  command: string;
  fix: string;
}

export interface ViewModel {
  status: "ready" | "error";
  readOnly: boolean;
  readOnlyReason: string | null;
  header: { profile: string; platform: string; project: string | null; note: string };
  controls: ControlView[];
  outcome: { title: string; rows: OutcomeRow[]; notes: string[] };
  error: ErrorCard | null;
  notice: Notice | null;
  busy: boolean;
  preferences?: PreferencesSummary;
  codexAvailable?: boolean;
  liveEffort?: LiveEffortSummary;
  uiEffort?: UiEffortSummary;
  hubVersion?: string;
  sessionDefaults?: SessionDefaults;
}

export interface PreferencesSummary {
  effort: string;
  effortStatus: string;
  needsAttention: boolean;
  guardsEnabled: number;
  guardsAvailable: number;
}

export const GUARDRAIL_IDS = ["git_safety", "secret_scan", "edit_preservation", "large_file_warning", "git_guardrails"] as const;

/** A preference is distinct from a platform's effective value. Never hide an override behind a saved choice. */
export function summarizePreferences(model: Pick<ViewModel, "controls">): PreferencesSummary {
  const control = model.controls.find((item) => item.id === "effort");
  const shared = control?.rows.find((row) => row.tool === "internal");
  const native = control?.rows.filter((row) => row.tool !== "internal" && row.installed !== false && row.state !== "tool-not-installed") ?? [];
  const effective = (row: RowView): string | null => row.state === "overridden-by" ? row.layerValue : row.value;
  const values = [...new Set(native.filter((row) => row.canSet).map(effective).filter((value): value is string => !!value))];
  const effort = shared?.value && control?.choices.includes(shared.value) ? shared.value : values.length === 1 && control?.choices.includes(values[0]!) ? values[0]! : "";
  const conflict = !!(shared && ["cannot-detect", "unverified-for-version", "not-covered"].includes(shared.state)) || native.some((row) => row.canSet && (["cannot-detect", "unverified-for-version", "not-covered"].includes(row.state) || (effort !== "" && (row.matchesDefault === false || (row.matchesDefault === undefined && effective(row) !== effort)))));
  const guards = model.controls.filter((item) => (GUARDRAIL_IDS as readonly string[]).includes(item.id));
  const available = guards.filter((item) => item.canApply && item.rows.some((row) => !["cannot-detect", "unverified-for-version"].includes(row.state)));
  const enabled = available.filter((item) => {
    const row = item.rows.find((value) => value.tool === "internal") ?? item.rows[0];
    const value = row ? effective(row) : null;
    return value === "on" || value === "true" || (row?.state === "tool-default" && item.id !== "git_guardrails");
  }).length;
  return {
    effort,
    effortStatus: conflict ? "Some defaults need synchronization. Choose an effort level to apply it again." : effort ? "Mapped to native defaults for new sessions." : "Choose the default for new sessions.",
    needsAttention: conflict || available.length !== guards.length,
    guardsEnabled: enabled,
    guardsAvailable: available.length,
  };
}

export const NEW_SESSIONS_NOTE = "Every default applies to new sessions only. A session that is already running keeps the value it started with.";
const OUTCOME_TITLE = "If you choose High effort and Full auto, a new session starts as:";
const PER_TOOL_OVERRIDE = new Set(["effort"]);
const TOOL_FALLBACK_LABEL: Record<string, string> = { internal: "Nexus-Hub (all tools)" };
const SURFACE_LABEL: Record<Surface, string> = { cli: "command line", "vscode-host": "VS Code", desktop: "desktop app" };
const ECHO_LIMIT = 80;
const POLICY_CAVEAT =
  "An organization policy can lock this VS Code setting and VS Code does not report policies to extensions. If the setting shows a lock icon in the Settings editor, your organization controls it.";

export function emptyModel(profile: string, platform: string): ViewModel {
  const model: ViewModel = {
    status: "ready",
    readOnly: false,
    readOnlyReason: null,
    header: { profile, platform, project: null, note: NEW_SESSIONS_NOTE },
    controls: [],
    outcome: { title: OUTCOME_TITLE, rows: [], notes: [] },
    error: null,
    notice: null,
    busy: false,
  };
  return model;
}

/** The panel's error state: one card, no controls, and no cached or default values shown as current. */
export function errorModel(profile: string, platform: string, error: ErrorCard, notice: Notice | null = null): ViewModel {
  return { ...emptyModel(profile, platform), status: "error", readOnly: true, readOnlyReason: "The Nexus-Hub command line could not be read.", error, notice };
}

export function joinKey(write: ExplainWrite): string {
  return write.key_path.join(".");
}

function echo(value: unknown): string {
  const text = typeof value === "string" ? value : JSON.stringify(value);
  const printable = [...text].map((char) => (char >= " " && char <= "~" ? char : "?")).join("");
  return printable.length <= ECHO_LIMIT ? printable : `${printable.slice(0, ECHO_LIMIT - 3)}...`;
}

function toolLabel(report: ShowReport, tool: string): string {
  return report.tools[tool]?.label ?? TOOL_FALLBACK_LABEL[tool] ?? tool;
}

function hostOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "unknown host";
  }
}

function sourceText(write: ExplainWrite): string {
  if (write.source.url) {
    return `${hostOf(write.source.url)}${write.source.fetched ? `, fetched ${write.source.fetched}` : ""}`;
  }
  return write.source.decision ?? "no source recorded";
}

/** The catalog's placeholder for a write that has no documented key. It is never shown as if it were a key. */
const NO_KEY = "<none documented>";

function sourcesFor(explain: ExplainData, report: ShowReport): SourceView[] {
  return explain.writes.map((write) => {
    const key = joinKey(write);
    const surface = SURFACE_LABEL[write.surface];
    const hasKey = key !== NO_KEY && key !== "";
    const where = `${toolLabel(report, write.tool)} (${surface})`;
    return {
      write: write.id,
      tool: write.tool,
      surfaceLabel: surface,
      file: write.file,
      key,
      takesEffect: write.takes_effect,
      admitted: write.admission === "admitted",
      reason: write.admission === "admitted" ? null : (write.not_settable_reason ?? null),
      source: sourceText(write),
      canOpen: isAllowedSource(write.source.url),
      weakens: write.weakens_safety,
      notes: write.notes ?? null,
      layers: write.override_layers.map((layer) => ({ kind: layer.kind, locator: layer.locator, fix: layer.fix })),
      owner: where,
      name: hasKey ? key : where,
      keyLine: hasKey ? `${key} in ${write.file} (${write.tool}, ${surface})` : `No documented key for ${where}`,
    };
  });
}

interface RowFields {
  state: State;
  value: string | null;
  layer: string | null;
  layerValue: string | null;
  fix: string | null;
  detail: string | null;
  caveats: string[];
}

/**
 * The engine cannot read VS Code settings, so it reports an installed, admitted
 * VS Code row as `cannot-detect` and leaves the reading to the panel. The panel reads
 * the key's layers and picks exactly one state. A workspace value wins over the user
 * value, so it is `overridden-by`. An organization policy is not exposed to
 * extensions, so it goes in the caveats with the lock-icon instruction.
 */
export function overlayEditorRow(record: ShowRecord, writes: ExplainWrite[], inspect: (key: string) => EditorLayers): RowFields {
  const primary = writes[0];
  const keep = { caveats: [...record.caveats, POLICY_CAVEAT] };
  if (!primary) {
    return { state: record.state, value: record.value, layer: record.layer, layerValue: record.layer_value, fix: record.fix, detail: record.detail, ...keep };
  }
  const key = joinKey(primary);
  const layers = inspect(key);
  if (!layers.registered) {
    return { state: "tool-not-installed", value: null, layer: null, layerValue: null, fix: null, detail: `${key} is not registered in this VS Code: install or enable the extension that provides it.`, caveats: record.caveats };
  }
  const shadow = layers.workspaceFolderValue !== undefined ? layers.workspaceFolderValue : layers.workspaceValue;
  if (shadow !== undefined) {
    return {
      state: "overridden-by",
      value: null,
      layer: `VS Code workspace setting ${key}`,
      layerValue: echo(shadow),
      fix: `Remove ${key} from the workspace settings (.vscode/settings.json or the .code-workspace file).`,
      detail: null,
      ...keep,
    };
  }
  if (layers.globalValue === undefined) {
    return { state: "tool-default", value: null, layer: null, layerValue: null, fix: null, detail: null, ...keep };
  }
  const chosen = Object.entries(primary.value_map)
    .filter(([, native]) => isDeepStrictEqual(native, layers.globalValue))
    .map(([name]) => name);
  const caveats = chosen.length === 0 ? [...keep.caveats, `${key} holds ${echo(layers.globalValue)}, which is not a value Nexus-Hub writes.`] : keep.caveats;
  return { state: "in-effect", value: chosen.length > 0 ? chosen.join("/") : echo(layers.globalValue), layer: null, layerValue: null, fix: null, detail: null, caveats };
}

function rowFor(record: ShowRecord, report: ShowReport, fields: RowFields): RowView {
  const settable = fields.state !== "not-settable" && fields.state !== "tool-not-installed";
  const badge = badgeFor(fields.state, fields.state === "overridden-by" ? null : fields.detail, fields.layer);
  return {
    tool: record.tool,
    installed: report.tools[record.tool]?.installed,
    toolLabel: toolLabel(report, record.tool),
    surface: record.surface,
    surfaceLabel: SURFACE_LABEL[record.surface],
    state: fields.state,
    badge,
    value: fields.value,
    layerValue: fields.layerValue,
    fix: fields.fix,
    detail: fields.detail,
    caveats: fields.caveats,
    canSet: settable,
    removable: record.removable_override
      ? { tool: record.tool, weakens: record.removable_override.weakens_safety, reason: record.removable_override.reason }
      : null,
    matchesDefault: record.matches_default,
    mappedEffort: record.mapped_effort,
  };
}

function valueMapText(write: ExplainWrite, choice: string): string | null {
  return choice in write.value_map ? JSON.stringify(write.value_map[choice]).replace(/^"|"$/g, "") : null;
}

/** A cell says only "Not settable"; the reason is written once under the table (`outcomeNotes`), not in every cell. */
function outcomeCell(writes: ExplainWrite[], choice: string): string {
  const admitted = writes.filter((w) => w.admission === "admitted");
  if (admitted.length === 0) {
    return "Not settable";
  }
  const parts = admitted.flatMap((w) => {
    const mapped = valueMapText(w, choice);
    return mapped === null ? [] : [`${joinKey(w)} = ${mapped}`];
  });
  return parts.length > 0 ? parts.join("; ") : "Not written for this choice";
}

/** The per-tool table of what a new session starts with, built from the catalog (never typed by hand). */
export function outcomeRows(explains: Record<string, ExplainData>, report: ShowReport): OutcomeRow[] {
  const effort = explains.effort?.writes ?? [];
  const posture = explains.posture?.writes ?? [];
  const keys: { tool: string; surface: Surface }[] = [];
  for (const write of [...effort, ...posture]) {
    if (!keys.some((k) => k.tool === write.tool && k.surface === write.surface)) {
      keys.push({ tool: write.tool, surface: write.surface });
    }
  }
  return keys.map(({ tool, surface }) => {
    const mine = (writes: ExplainWrite[]): ExplainWrite[] => writes.filter((w) => w.tool === tool && w.surface === surface);
    const suffix = surface === "cli" ? "" : ` (${SURFACE_LABEL[surface]})`;
    return {
      tool: `${tool}:${surface}`,
      label: `${toolLabel(report, tool)}${suffix}`,
      effort: mine(effort).length > 0 ? outcomeCell(mine(effort), "high") : "Not part of this tool",
      posture: mine(posture).length > 0 ? outcomeCell(mine(posture), "full-auto") : "Not part of this tool",
    };
  });
}

/** Why each tool is not settable, grouped by reason so a reason that applies to several tools is written once. */
export function outcomeNotes(explains: Record<string, ExplainData>, report: ShowReport): string[] {
  const byReason = new Map<string, string[]>();
  for (const write of [...(explains.effort?.writes ?? []), ...(explains.posture?.writes ?? [])]) {
    if (write.admission === "admitted" || !write.not_settable_reason) {
      continue;
    }
    const suffix = write.surface === "cli" ? "" : ` (${SURFACE_LABEL[write.surface]})`;
    const label = `${toolLabel(report, write.tool)}${suffix}`;
    const labels = byReason.get(write.not_settable_reason) ?? [];
    if (!labels.includes(label)) {
      labels.push(label);
    }
    byReason.set(write.not_settable_reason, labels);
  }
  return [...byReason.entries()].map(([reason, labels]) => `Not settable for ${labels.join(", ")}: ${reason}`);
}

function controlView(
  id: string,
  explain: ExplainData,
  report: ShowReport,
  records: ShowRecord[],
  inspect: (key: string) => EditorLayers,
): ControlView {
  const byId = new Map(explain.writes.map((w) => [w.id, w]));
  const rows = records.map((record) => {
    const writes = record.writes.flatMap((wid) => {
      const found = byId.get(wid);
      return found && found.admission === "admitted" ? [found] : [];
    });
    const overlay = record.surface === "vscode-host" && record.state === "cannot-detect" && writes.length > 0;
    const fields: RowFields = overlay
      ? overlayEditorRow(record, writes, inspect)
      : { state: record.state, value: record.value, layer: record.layer, layerValue: record.layer_value, fix: record.fix, detail: record.detail, caveats: record.caveats };
    return rowFor(record, report, fields);
  });
  const values = explain.control.values;
  const choices = Array.isArray(values) ? values : [];
  const weakening = new Set(explain.writes.filter((w) => w.admission === "admitted").flatMap((w) => w.weakening_values));
  return {
    id,
    label: explain.control.label,
    kind: Array.isArray(values) ? "choice" : "text",
    choices,
    weakeningChoices: choices.filter((choice) => weakening.has(choice)),
    suggestions: { claude: explain.claude_model_ids },
    perTool: explain.control.per_tool,
    perToolOverride: PER_TOOL_OVERRIDE.has(id),
    neverWritten: explain.control.never_written,
    canApply: rows.some((row) => row.canSet),
    takesEffect: "New sessions only.",
    rows,
    sources: sourcesFor(explain, report),
  };
}

export interface BuildInput {
  report: ShowReport;
  explains: Record<string, ExplainData>;
  inspect: (key: string) => EditorLayers;
  trusted: boolean;
  profile: string;
  notice?: Notice | null;
}

export function buildModel(input: BuildInput): ViewModel {
  const { report, explains, inspect } = input;
  const order: string[] = [];
  for (const record of report.records) {
    if (!order.includes(record.control)) {
      order.push(record.control);
    }
  }
  const controls = order.flatMap((id) => {
    const explain = explains[id];
    return explain ? [controlView(id, explain, report, report.records.filter((r) => r.control === id), inspect)] : [];
  });
  const model: ViewModel = {
    status: "ready",
    readOnly: !input.trusted,
    readOnlyReason: input.trusted ? null : "This workspace is not trusted, so the panel shows the current state and cannot change anything. Trust the workspace to change a default.",
    header: { profile: input.profile, platform: report.platform, project: report.project, note: NEW_SESSIONS_NOTE },
    controls,
    outcome: { title: OUTCOME_TITLE, rows: outcomeRows(explains, report), notes: outcomeNotes(explains, report) },
    error: null,
    notice: input.notice ?? null,
    busy: false,
  };
  model.preferences = summarizePreferences(model);
  return model;
}
