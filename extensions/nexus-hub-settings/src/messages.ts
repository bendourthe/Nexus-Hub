import type { ViewModel } from "./viewModel";

/**
 * Every message the webview posts is validated here against the catalog allowlist
 * (the controls, values, tools, and sources the engine itself reported) before it
 * becomes command-line arguments or an action. The webview is treated as untrusted:
 * it never supplies a URL, a path, a file name, or a command.
 */

export type Incoming =
  | { type: "ready" }
  | { type: "refresh" }
  | { type: "newCodex" }
  | { type: "set"; control: string; value: string; tool: string | null }
  | { type: "reset"; control: string; tool: string | null }
  | { type: "removeOverride"; control: string; tool: string }
  | { type: "openSource"; control: string; write: string };

export type Validated = { ok: true; message: Incoming } | { ok: false; reason: string };

const ALLOWED_KEYS: Record<string, readonly string[]> = {
  ready: ["type"],
  refresh: ["type"],
  newCodex: ["type"],
  set: ["type", "control", "value", "tool"],
  reset: ["type", "control", "tool"],
  removeOverride: ["type", "control", "tool"],
  openSource: ["type", "control", "write"],
};

const TEXT_LIMIT = 200;
const WRITES = new Set(["set", "reset", "removeOverride"]);

function fail(reason: string): Validated {
  return { ok: false, reason };
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Free text (a model id): 1 to 200 printable ASCII characters, no edges of whitespace, no leading hyphen. */
export function validText(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= TEXT_LIMIT &&
    value === value.trim() &&
    !value.startsWith("-") &&
    [...value].every((char) => char >= " " && char <= "~")
  );
}

function optionalTool(raw: unknown): string | null | undefined {
  if (raw === undefined || raw === null) {
    return null;
  }
  return typeof raw === "string" ? raw : undefined;
}

export function validateMessage(raw: unknown, model: ViewModel): Validated {
  if (!isPlainObject(raw) || typeof raw.type !== "string" || !Object.hasOwn(ALLOWED_KEYS, raw.type)) {
    return fail("unknown message");
  }
  const allowed = ALLOWED_KEYS[raw.type] as readonly string[];
  if (Object.keys(raw).some((key) => !allowed.includes(key))) {
    return fail("unexpected fields");
  }
  if (raw.type === "ready" || raw.type === "refresh") {
    return { ok: true, message: { type: raw.type } };
  }
  if (WRITES.has(raw.type) && model.readOnly) {
    return fail("the panel is read-only");
  }
  if (raw.type === "newCodex") {
    return !model.readOnly && model.codexAvailable ? { ok: true, message: { type: "newCodex" } } : fail("Codex is unavailable or the panel is read-only");
  }
  const control = model.controls.find((c) => c.id === raw.control);
  if (!control) {
    return fail("unknown control");
  }
  if (raw.type === "openSource") {
    const source = control.sources.find((s) => s.write === raw.write);
    return source && source.canOpen ? { ok: true, message: { type: "openSource", control: control.id, write: source.write } } : fail("unknown source");
  }
  const tool = optionalTool(raw.tool);
  if (tool === undefined) {
    return fail("invalid tool");
  }
  const settable = new Set(control.rows.filter((row) => row.canSet).map((row) => row.tool));
  if (raw.type === "removeOverride") {
    const removable = control.rows.some((row) => row.tool === tool && row.removable !== null);
    return tool !== null && removable ? { ok: true, message: { type: "removeOverride", control: control.id, tool } } : fail("nothing removable for that tool");
  }
  if (raw.type === "reset") {
    const known = tool === null || control.rows.some((row) => row.tool === tool);
    return known ? { ok: true, message: { type: "reset", control: control.id, tool } } : fail("unknown tool");
  }
  if (control.kind === "choice" ? typeof raw.value !== "string" || !control.choices.includes(raw.value) : !validText(raw.value)) {
    return fail("invalid value");
  }
  if (control.perTool && tool === null) {
    return fail("this control is chosen per tool");
  }
  if (tool !== null && !(control.perTool || control.perToolOverride)) {
    return fail("this control is not set per tool");
  }
  if (tool !== null && !settable.has(tool)) {
    return fail("that tool cannot be set");
  }
  return { ok: true, message: { type: "set", control: control.id, value: raw.value as string, tool } };
}
