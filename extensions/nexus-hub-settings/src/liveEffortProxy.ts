import { startNativeStream } from "./nativeStreamProcess";
import { randomUUID } from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";
import * as readline from "node:readline";

export const EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"] as const;
export type Effort = typeof EFFORTS[number];
type Packet = Record<string, unknown>;
export type Provider = "claude" | "codex";
const object = (value: unknown): value is Packet => !!value && typeof value === "object" && !Array.isArray(value);
export const effort = (value: unknown): value is Effort => typeof value === "string" && (EFFORTS as readonly string[]).includes(value);

/** A new value or explicit Apply action is an event; ordinary polling is not. */
export function readEffortPreference(file: string): { value: Effort; revision: string } | null {
  try {
    const data: unknown = JSON.parse(fs.readFileSync(file, "utf8"));
    if (!object(data) || !effort(data.default_effort)) { return null; }
    let token = "";
    try { const event = JSON.parse(fs.readFileSync(path.join(path.dirname(file), "effort-apply.json"), "utf8")); if (event.effort === data.default_effort && typeof event.token === "string") { token = event.token; } } catch { /* No explicit reapply yet. */ }
    return { value: data.default_effort, revision: data.default_effort + ":" + token };
  } catch { return null; }
}
export function requestEffortApply(file: string): void {
  const preference = readEffortPreference(file);
  if (!preference) { throw new Error("Choose a default effort first."); }
  const target = path.join(path.dirname(file), "effort-apply.json"), temporary = target + "." + randomUUID();
  try { fs.writeFileSync(temporary, JSON.stringify({ effort: preference.value, token: randomUUID() }), { flag: "wx" }); fs.renameSync(temporary, target); }
  finally { try { fs.unlinkSync(temporary); } catch { /* The atomic move consumed it. */ } }
}

export function mappedEffort(provider: Provider, wanted: Effort, available: readonly string[] = EFFORTS.slice(0, 4)): string | null {
  if (provider === "claude") { return wanted === "ultra" ? "xhigh" : wanted; }
  return EFFORTS.slice(0, EFFORTS.indexOf(wanted) + 1).filter((level) => available.includes(level)).at(-1) ?? available.find(effort) ?? null;
}

/** Remove only the startup effort pin; preserve every other supplied setting. */
export function claudeLaunchArgs(args: string[], saveSettings?: (content: string) => string): string[] {
  const result = [...args];
  let index = -1, inline = false;
  result.forEach((argument, at) => { if (argument === "--settings" || argument.startsWith("--settings=")) { index = at; inline = argument !== "--settings"; } });
  let settings: Packet = {};
  let fileBased = false;
  if (index >= 0) {
    const value = inline ? result[index]!.slice("--settings=".length) : result[index + 1];
    if (!value) { return result; }
    try {
      if (!value.trim().startsWith("{") && fs.statSync(value).size > 16000) { return result; }
      fileBased = !value.trim().startsWith("{");
      if (fileBased && !saveSettings) { return result; }
      const parsed: unknown = JSON.parse(fileBased ? fs.readFileSync(value, "utf8") : value);
      if (!object(parsed) || (parsed.env !== undefined && !object(parsed.env))) { return result; }
      settings = parsed;
    } catch { return result; }
  }
  const merged = JSON.stringify({ ...settings, env: { ...(object(settings.env) ? settings.env : {}), CLAUDE_CODE_EFFORT_LEVEL: "" } });
  if (merged.length > 16000) { return result; }
  const replacement = fileBased ? saveSettings!(merged) : merged;
  if (index < 0) { result.push("--settings", replacement); }
  else if (inline) { result[index] = "--settings=" + replacement; }
  else { result[index + 1] = replacement; }
  return result;
}

export interface LiveState {
  provider: Provider;
  requested: Effort | null;
  applied: boolean;
  mapped: string | null;
  sessions?: number;
  error?: string;
}
interface Pending { revision?: string; type: "claude-apply" | "claude-read" | "codex-apply"; wanted: Effort; mapped: string; thread?: string }

/** Owns only effort fields and its own request IDs. Vendor requests and permissions remain intact. */
export class EffortProtocol {
  private wanted: Effort | null = null;
  private ready = false;
  private revision = "";
  private readonly manual = new Set<string>();
  private serial = 0;
  private readonly prefix = `nexus-effort-${randomUUID()}-`;
  private readonly pending = new Map<string, Pending>();
  private readonly timers = new Map<string, ReturnType<typeof setTimeout>>();
  private readonly requests = new Map<string | number, { method: string; model?: string; ephemeral?: boolean }>();
  private readonly threads = new Map<string, { model?: string; applied?: string }>();
  private readonly excludedThreads = new Set<string>();
  private readonly models = new Map<string, string[]>();
  private claudeBusy = false;
  private fallbackModel: string | undefined;
  private heldInitialize: string | undefined;

  constructor(private readonly provider: Provider, private readonly native: (line: string) => void, private readonly client: (line: string) => void, private readonly report: (state: LiveState) => void) {}

  setModels(model: string | undefined, models: Map<string, string[]>): void { this.fallbackModel = model; for (const [name, levels] of models) { this.models.set(name, levels); } }
  private mapped(wanted: Effort, model?: string): string | null { return mappedEffort(this.provider, wanted, this.models.get(model ?? this.fallbackModel ?? "")); }
  private codexState(): void {
    const states = [...this.threads.entries()].filter(([id]) => !this.manual.has(id)).map(([, state]) => state).filter((state) => !this.wanted || this.mapped(this.wanted, state.model) !== null);
    const applied = !!this.wanted && states.length > 0 && states.every((state) => state.applied === this.mapped(this.wanted!, state.model));
    const mappings = new Set(states.map((state) => this.wanted ? this.mapped(this.wanted, state.model) : null));
    this.report({ provider: this.provider, requested: this.wanted, mapped: mappings.size === 1 ? [...mappings][0]! : this.wanted ? this.mapped(this.wanted) : null, sessions: states.length, applied, ...!applied && states.length && !this.pending.size ? { error: "A native session has not acknowledged the selected effort." } : {} });
  }
  private releaseInitialize(): void { if (this.heldInitialize) { this.client(this.heldInitialize); this.heldInitialize = undefined; } }
  private superseded(request: Pending): boolean { return request.revision !== this.revision || request.wanted !== this.wanted || (this.provider === "codex" && !!this.wanted && request.mapped !== this.mapped(this.wanted, request.thread ? this.threads.get(request.thread)?.model : undefined)); }
  setEffort(value: Effort | null, revision = value ?? ""): void {
    if (this.wanted === value && this.revision === revision) { return; }
    const reapply = this.wanted === value;
    this.revision = revision;
    for (const [id, state] of this.threads) { if (reapply || this.manual.has(id)) { state.applied = undefined; } }
    this.manual.clear();
    this.wanted = value;
    if (!value) { this.releaseInitialize(); }
    this.report({ provider: this.provider, requested: value, applied: false, mapped: value ? this.mapped(value) : null, sessions: this.provider === "claude" ? Number(this.ready) : this.threads.size });
    this.apply();
    if (this.provider === "codex") { this.codexState(); }
  }
  private send(request: Pending): void {
    const id = this.prefix + ++this.serial;
    request = { ...request, revision: request.revision ?? this.revision };
    this.pending.set(id, request);
    const timer = setTimeout(() => {
      if (!this.pending.delete(id)) { return; }
      this.timers.delete(id); this.claudeBusy = false; this.releaseInitialize();
      this.report({ provider: this.provider, requested: this.wanted, applied: false, mapped: request.mapped, sessions: this.provider === "claude" ? 1 : this.threads.size, error: "The native client did not acknowledge the live effort update." });
      if (this.superseded(request)) { this.apply(); }
    }, 5000);
    timer.unref?.(); this.timers.set(id, timer);
    const packet = this.provider === "claude"
      ? { type: "control_request", request_id: id, request: request.type === "claude-read" ? { subtype: "get_settings" } : { subtype: "apply_flag_settings", settings: { effortLevel: request.mapped, ultracode: request.wanted === "ultra" } } }
      : { jsonrpc: "2.0", id, method: "thread/settings/update", params: { threadId: request.thread, effort: request.mapped } };
    this.native(JSON.stringify(packet));
  }
  private apply(): void {
    if (!this.ready || !this.wanted) { return; }
    if (this.provider === "claude") {
      const mapped = this.mapped(this.wanted);
      if (!this.claudeBusy && mapped) { this.claudeBusy = true; this.send({ type: "claude-apply", wanted: this.wanted, mapped }); }
    } else {
      for (const [thread, state] of this.threads) {
        if (this.manual.has(thread)) { continue; }
        const mapped = this.mapped(this.wanted, state.model);
        if (mapped && state.applied !== mapped && ![...this.pending.values()].some((p) => p.thread === thread)) { this.send({ type: "codex-apply", wanted: this.wanted, mapped, thread }); }
      }
    }
  }
  fromClient(line: string): void {
    let packet: unknown;
    try { packet = JSON.parse(line); } catch { this.native(line); return; }
    if (!object(packet)) { this.native(line); return; }
    const request = this.provider === "claude" ? packet.request : packet.params;
    const method = this.provider === "claude" ? object(request) ? request.subtype : undefined : packet.method;
    const id = this.provider === "claude" ? packet.request_id : packet.id;
    if ((typeof id === "string" || typeof id === "number") && typeof method === "string") {
      if (["initialize", "thread/start", "thread/resume", "thread/fork", "config/read", "model/list"].includes(method)) { this.requests.set(id, { method, model: object(request) && typeof request.model === "string" ? request.model : undefined, ephemeral: object(request) && request.ephemeral === true }); }
    }
    if (!this.wanted || !object(request)) { this.native(line); return; }
    if (request.ephemeral === true || (typeof request.threadId === "string" && this.excludedThreads.has(request.threadId))) { this.native(line); return; }
    const mode = object(request.collaborationMode) && object(request.collaborationMode.settings) ? request.collaborationMode.settings : undefined;
    const selected = typeof request.model === "string" ? request.model : mode && typeof mode.model === "string" ? mode.model : typeof request.threadId === "string" ? this.threads.get(request.threadId)?.model : undefined;
    const mapped = this.mapped(this.wanted, selected);
    if (!mapped) { this.native(line); return; }
    let changed = false;
    // Native picker changes are session choices. Never rewrite their settings or turns.
    if (this.provider === "codex") {
      if (method === "thread/start" || method === "thread/resume" || method === "thread/fork") {
        request.config = { ...(object(request.config) ? request.config : {}), model_reasoning_effort: mapped }; changed = true;
      } else if ((method === "thread/settings/update" || method === "turn/start") && typeof request.threadId === "string") {
        const chosen = typeof request.effort === "string" ? request.effort : mode?.reasoning_effort;
        if (typeof chosen === "string" && chosen !== mapped) { this.manual.add(request.threadId); }
      }
    }
    this.native(changed ? JSON.stringify(packet) : line);
  }
  fromNative(line: string): void {
    let packet: unknown;
    try { packet = JSON.parse(line); } catch { this.client(line); return; }
    if (!object(packet)) { this.client(line); return; }
    const response = this.provider === "claude" && object(packet.response) ? packet.response : packet;
    const id = this.provider === "claude" ? response.request_id : packet.id;
    const own = typeof id === "string" ? this.pending.get(id) : undefined;
    if (own && typeof id === "string") {
      this.pending.delete(id);
      clearTimeout(this.timers.get(id)); this.timers.delete(id);
      if (response.error || response.subtype === "error") {
        this.claudeBusy = false;
        this.report({ provider: this.provider, requested: this.wanted, applied: false, mapped: own.mapped, error: "The native client refused a live effort update." });
        this.releaseInitialize();
        if (this.superseded(own)) { this.apply(); }
        return;
      }
      if (own.type === "claude-apply") { this.send({ ...own, type: "claude-read" }); return; }
      if (own.type === "claude-read") {
        this.claudeBusy = false;
        const settings = object(response.response) && object(response.response.applied) ? response.response.applied : {};
        const applied = settings.effort === own.mapped && settings.ultracode === (own.wanted === "ultra");
        if (!this.superseded(own)) { this.report({ provider: this.provider, requested: this.wanted, mapped: own.mapped, applied, sessions: 1, ...applied ? {} : { error: "The native effort did not match the saved preference." } }); this.releaseInitialize(); }
        else { this.apply(); }
      } else {
        this.codexState();
        if (this.superseded(own)) { this.apply(); }
      }
      return;
    }
    if (typeof id === "string" && id.startsWith(this.prefix)) { return; }
    const original = typeof id === "string" || typeof id === "number" ? this.requests.get(id) : undefined;
    if (this.provider === "codex" && packet.method === "thread/settings/updated" && object(packet.params) && typeof packet.params.threadId === "string" && object(packet.params.threadSettings)) {
      const settings = packet.params.threadSettings;
      if (this.threads.has(packet.params.threadId) && !this.excludedThreads.has(packet.params.threadId)) {
        this.threads.set(packet.params.threadId, { model: typeof settings.model === "string" ? settings.model : this.threads.get(packet.params.threadId)?.model, applied: typeof settings.effort === "string" ? settings.effort : undefined });
        this.codexState();
      }
    }
    if (this.provider === "codex" && ["thread/closed", "thread/archived", "thread/deleted"].includes(String(packet.method)) && object(packet.params) && typeof packet.params.threadId === "string") {
      this.threads.delete(packet.params.threadId); this.excludedThreads.delete(packet.params.threadId);
      for (const [pendingId, pending] of this.pending) { if (pending.thread === packet.params.threadId) { this.pending.delete(pendingId); clearTimeout(this.timers.get(pendingId)); this.timers.delete(pendingId); } }
      this.codexState();
    }
    if (original && (typeof id === "string" || typeof id === "number")) {
      this.requests.delete(id);
      if (original.method === "initialize" && !response.error && response.subtype !== "error") { this.ready = true; }
      if (this.provider === "codex" && object(packet.result)) {
        const result = packet.result;
        if (original.method === "config/read" && object(result.config)) {
          const config = result.config;
          const profile = typeof config.profile === "string" && object(config.profiles) && object(config.profiles[config.profile]) ? config.profiles[config.profile] : undefined;
          const model = object(profile) && typeof profile.model === "string" ? profile.model : typeof config.model === "string" ? config.model : undefined;
          this.fallbackModel = model;
          const mapped = this.wanted ? this.mapped(this.wanted, model) : null;
          if (mapped) { config.model_reasoning_effort = mapped; if (object(profile)) { profile.model_reasoning_effort = mapped; } line = JSON.stringify(packet); }
        }
        if (["thread/start", "thread/resume", "thread/fork"].includes(original.method) && object(result.thread) && typeof result.thread.id === "string") {
          if (original.ephemeral) { this.threads.delete(result.thread.id); this.excludedThreads.add(result.thread.id); }
          else { this.threads.set(result.thread.id, { model: typeof result.model === "string" ? result.model : original.model, applied: typeof result.reasoningEffort === "string" ? result.reasoningEffort : undefined }); this.codexState(); }
        }
        if (original.method === "model/list" && Array.isArray(result.data)) {
          for (const model of result.data) {
            if (object(model) && typeof model.model === "string" && Array.isArray(model.supportedReasoningEfforts)) {
              this.models.set(model.model, model.supportedReasoningEfforts.filter(object).map((entry) => entry.reasoningEffort).filter((level): level is string => typeof level === "string"));
            }
          }
          this.apply(); this.codexState();
        }
      }
    }
    if (this.provider === "claude" && original?.method === "initialize" && this.wanted && this.ready) { this.heldInitialize = line; this.apply(); return; }
    this.client(line);
    if (original?.method === "initialize" || original?.method === "thread/start" || original?.method === "thread/resume" || original?.method === "thread/fork") { this.apply(); }
  }
}

export interface ProxyConfig { provider: Provider; target: string; preferences: string; statusDirectory: string; modelsCache?: string }
export function runProxy(config: ProxyConfig, originalArgs: string[]): void {
  let args = [...originalArgs];
  const target = config.provider === "claude" && args[0] && path.isAbsolute(args[0]) ? args.shift()! : config.target;
  const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
  const clientPid = Number(env.NEXUS_EFFORT_CLIENT_PID); delete env.NEXUS_EFFORT_CLIENT_PID;
  let privateSettings: string | undefined;
  if (config.provider === "claude" && args.includes("stream-json")) {
    try {
      const preference: unknown = JSON.parse(fs.readFileSync(config.preferences, "utf8"));
      if (object(preference) && effort(preference.default_effort)) {
        env.CLAUDE_CODE_EFFORT_LEVEL = "";
        args = claudeLaunchArgs(args, (content) => {
          privateSettings = fs.mkdtempSync(path.join(path.dirname(config.preferences), "live-effort-settings-"));
          const file = path.join(privateSettings, "settings.json"); fs.writeFileSync(file, content, { flag: "wx", mode: 0o600 }); return file;
        });
      }
    } catch { /* With no shared preference the original native environment is preserved. */ }
  }
  const child = startNativeStream(target, args, env);
  const cleanup = (): void => { if (privateSettings) { try { fs.unlinkSync(path.join(privateSettings, "settings.json")); fs.rmdirSync(privateSettings); } catch { /* Preserve any unexpected added contents. */ } } };
  child.once("exit", cleanup); child.once("error", cleanup);
  child.stderr.pipe(process.stderr);
  const streamed = config.provider === "codex" ? args.includes("app-server") : args.includes("stream-json");
  if (!streamed) { process.stdin.pipe(child.stdin); child.stdout.pipe(process.stdout); }
  else {
    try { fs.mkdirSync(config.statusDirectory, { recursive: true }); } catch { /* Telemetry must not prevent native stream forwarding. */ }
    const statusFile = path.join(config.statusDirectory, `${process.pid}-${randomUUID()}.json`);
    let status = "", retries = 0, statusTimer: ReturnType<typeof setTimeout> | undefined;
    const publishStatus = (): void => {
      statusTimer = undefined;
      try { fs.writeFileSync(statusFile + ".tmp", status); fs.renameSync(statusFile + ".tmp", statusFile); }
      catch {
        // Windows readers can briefly lock the destination during an atomic replace.
        if (retries-- > 0) { statusTimer = setTimeout(publishStatus, 25); statusTimer.unref(); }
      }
    };
    const protocol = new EffortProtocol(config.provider, (line) => child.stdin.write(line + "\n"), (line) => process.stdout.write(line + "\n"), (state) => {
      status = JSON.stringify({ ...state, pid: process.pid, childPid: child.pid, clientPid: Number.isInteger(clientPid) && clientPid > 0 ? clientPid : undefined, updatedAt: Date.now() }); retries = 40;
      clearTimeout(statusTimer); publishStatus();
    });
    try {
      if (config.modelsCache && fs.statSync(config.modelsCache).size <= 4_000_000) {
        const data: unknown = JSON.parse(fs.readFileSync(config.modelsCache, "utf8")); const models = new Map<string, string[]>();
        if (object(data) && Array.isArray(data.models)) {
          for (const model of data.models) { if (object(model) && typeof model.slug === "string" && Array.isArray(model.supported_reasoning_levels)) { models.set(model.slug, model.supported_reasoning_levels.filter(object).map((entry) => entry.effort).filter((level): level is string => typeof level === "string")); } }
        }
        protocol.setModels(undefined, models);
      }
    } catch { /* Missing model metadata uses the compatible effort scale. */ }
    const reread = (): void => {
      const preference = readEffortPreference(config.preferences);
      protocol.setEffort(preference?.value ?? null, preference?.revision);
    };
    const eventFile = path.join(path.dirname(config.preferences), "effort-apply.json");
    reread();
    for (const file of [config.preferences, eventFile]) { fs.watchFile(file, { interval: 250, persistent: false }, reread); }
    const input = readline.createInterface({ input: process.stdin }); const output = readline.createInterface({ input: child.stdout });
    input.on("line", (line) => protocol.fromClient(line)); output.on("line", (line) => protocol.fromNative(line));
    input.on("close", () => { fs.unwatchFile(config.preferences, reread); fs.unwatchFile(eventFile, reread); child.stdin.end(); });
    child.once("exit", () => {
      fs.unwatchFile(config.preferences, reread); fs.unwatchFile(eventFile, reread); clearTimeout(statusTimer);
      for (const file of [statusFile, statusFile + ".tmp"]) { try { fs.unlinkSync(file); } catch { /* Only this process's unique status files are removed. */ } }
    });
  }
  child.stdin.on("error", () => undefined);
  child.once("error", () => { process.stderr.write("Nexus live effort: the configured native client could not start.\n"); process.exitCode = 1; process.stdin.destroy(); });
  child.once("exit", (code) => { process.exitCode = code ?? 1; process.stdin.destroy(); });
}

if (require.main === module) {
  try {
    const config: ProxyConfig = JSON.parse(fs.readFileSync(process.argv[2]!, "utf8"));
    if (!["claude", "codex"].includes(config.provider) || ![config.target, config.preferences, config.statusDirectory].every((value) => typeof value === "string" && path.isAbsolute(value))) { throw new Error("Invalid bridge configuration"); }
    runProxy(config, process.argv.slice(3));
  } catch { process.stderr.write("Nexus live effort: invalid local bridge configuration.\n"); process.exitCode = 1; }
}
