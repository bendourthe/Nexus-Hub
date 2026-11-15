/**
 * Shapes of the JSON the `nexus-hub settings` command line prints.
 *
 * The engine (scripts/lib/settings_control/) is the only source of truth. These
 * types describe what the panel reads from it; the panel never invents a state.
 */

export type State =
  | "in-effect"
  | "tool-default"
  | "overridden-by"
  | "not-settable"
  | "not-covered"
  | "unverified-for-version"
  | "tool-not-installed"
  | "cannot-detect";

export type Surface = "cli" | "vscode-host" | "desktop";

export interface ToolInfo {
  label: string;
  installed: boolean;
  version: string | null;
  cannot_remove: string[];
}

export interface RemovableOverride {
  id: string;
  weakens_safety: boolean;
  reason: string;
}

export interface ShowRecord {
  control: string;
  tool: string;
  surface: Surface;
  state: State;
  value: string | null;
  native: unknown;
  layer: string | null;
  layer_value: string | null;
  fix: string | null;
  detail: string | null;
  caveats: string[];
  writes: string[];
  removable_override: RemovableOverride | null;
  /** Native mapping/readback supplied by the engine, including model-specific ceilings. */
  matches_default?: boolean;
  mapped_effort?: string;
}

export interface ShowReport {
  schema_version: 1;
  project: string | null;
  platform: "windows" | "macos" | "linux";
  tools: Record<string, ToolInfo>;
  records: ShowRecord[];
}

export interface Source {
  url?: string;
  fetched?: string;
  decision?: string;
}

export interface OverrideLayer {
  kind: string;
  locator: string;
  fix: string;
}

export interface ExplainWrite {
  id: string;
  kind: string;
  tool: string;
  surface: Surface;
  file: string;
  key_path: string[];
  values: unknown;
  value_map: Record<string, unknown>;
  takes_effect: string;
  proven_versions: { min?: string; max?: string };
  weakens_safety: boolean;
  weakening_values: string[];
  source: Source;
  admission: "admitted" | "not-settable";
  not_settable_reason?: string;
  notes?: string;
  override_layers: OverrideLayer[];
}

export interface ExplainControl {
  id: string;
  label: string;
  /** A list of allowed values, or `{type: "string"}` for free text such as a model id. */
  values: string[] | { type: "string" };
  per_tool: boolean;
  never_written: string[];
}

export interface ExplainData {
  control: ExplainControl;
  writes: ExplainWrite[];
  tools: Record<string, { label: string; cannot_remove: string[] }>;
  claude_model_ids: string[];
}

export interface EditorWrite {
  tool: string;
  write: string;
  key: string;
  key_path: string[];
  value: unknown;
  weakens_safety: boolean;
  takes_effect: string;
}

export interface PriorState {
  present: boolean;
  value?: unknown;
}

export interface EditorRestore {
  tool: string;
  write: string;
  key: string;
  key_path: string[];
  restore: PriorState;
  was: PriorState;
  profile: string | null;
}

export interface ActionResult {
  tool: string;
  write: string;
  file: string;
  key_path: string[] | null;
  status: string;
  detail: string;
  previous?: PriorState;
  new?: PriorState;
}

export interface ActionDoc {
  schema_version: number;
  action: "set" | "reset" | "remove-override" | "record-editor-write";
  control?: string;
  value?: string;
  tool?: string | null;
  dry_run?: boolean;
  confirmation?: { required: boolean; kind: string | null };
  results?: ActionResult[];
  editor_writes?: EditorWrite[];
  editor_restores?: EditorRestore[];
  after?: ShowRecord[];
  ignored?: string[];
  exit_code: number;
}

/** Exit codes of `nexus-hub settings`: 0 done, 1 partial, 2 usage, 3 refused, 4 nothing to write. */
export const EXIT = { OK: 0, PARTIAL: 1, USAGE: 2, REFUSED: 3, NOTHING: 4 } as const;
