import { afterEach, describe, expect, it, vi } from "vitest";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { EFFORTS, EffortProtocol, claudeLaunchArgs, mappedEffort, type LiveState } from "../src/liveEffortProxy";

function session(provider: "claude" | "codex") {
  const native: string[] = [], client: string[] = [], states: LiveState[] = [];
  const bridge = new EffortProtocol(provider, (line) => native.push(line), (line) => client.push(line), (state) => states.push(state));
  bridge.setModels("test", new Map([["test", [...EFFORTS]]]));
  const send = (packet: unknown) => bridge.fromClient(JSON.stringify(packet));
  const receive = (packet: unknown) => bridge.fromNative(JSON.stringify(packet));
  return { bridge, native, client, states, send, receive };
}

describe("live effort protocol boundary", () => {
  afterEach(() => vi.useRealTimers());
  it("keeps file-based settings and secrets out of the command line", () => {
    const directory = fs.mkdtempSync(path.join(os.tmpdir(), "nexus-settings-args-"));
    try {
      const file = path.join(directory, "original.json"); const settings = { env: { ANTHROPIC_API_KEY: "private-sentinel", CLAUDE_CODE_EFFORT_LEVEL: "high" }, permissions: { defaultMode: "plan" } };
      fs.writeFileSync(file, JSON.stringify(settings)); let merged = "";
      const updated = claudeLaunchArgs(["--settings", file], (content) => { merged = content; return path.join(directory, "private-merged.json"); });
      expect(updated).toEqual(["--settings", path.join(directory, "private-merged.json")]);
      expect(updated.join(" ")).not.toContain("private-sentinel");
      expect(JSON.parse(merged)).toEqual({ ...settings, env: { ...settings.env, CLAUDE_CODE_EFFORT_LEVEL: "" } });
      expect(JSON.parse(fs.readFileSync(file, "utf8"))).toEqual(settings);
    } finally { fs.rmSync(directory, { recursive: true }); }
  });
  it.each(["refusal", "timeout"])("applies the latest Claude choice after a stale %s", (failure) => {
    vi.useFakeTimers(); const s = session("claude"); s.bridge.setEffort("high");
    s.send({ type: "control_request", request_id: "init", request: { subtype: "initialize" } });
    s.receive({ type: "control_response", response: { request_id: "init", subtype: "success" } });
    const old = JSON.parse(s.native.at(-1)!); s.bridge.setEffort("low");
    if (failure === "timeout") { vi.advanceTimersByTime(5000); }
    else { s.receive({ type: "control_response", response: { request_id: old.request_id, subtype: "error" } }); }
    expect(JSON.parse(s.native.at(-1)!).request.settings.effortLevel).toBe("low");
  });
  it("releases initialization when effort management is cleared", () => {
    const s = session("claude"); s.bridge.setEffort("high");
    s.send({ type: "control_request", request_id: "init", request: { subtype: "initialize" } });
    s.receive({ type: "control_response", response: { request_id: "init", subtype: "success" } });
    s.bridge.setEffort(null); expect(s.client).toHaveLength(1);
  });
  it("preserves utility threads, ignores unknown notifications, and cancels closed-session timeouts", () => {
    vi.useFakeTimers(); const s = session("codex"); s.bridge.setEffort("ultra");
    s.send({ id: 1, method: "initialize", params: {} }); s.receive({ id: 1, result: {} });
    const utility = { id: 2, method: "thread/start", params: { ephemeral: true, config: { model_reasoning_effort: "low" } } };
    s.send(utility); expect(s.native.at(-1)).toBe(JSON.stringify(utility));
    s.receive({ method: "thread/settings/updated", params: { threadId: "utility", threadSettings: { effort: "low" } } });
    s.receive({ id: 2, result: { thread: { id: "utility" }, model: "test" } });
    const turn = { id: 3, method: "turn/start", params: { threadId: "utility", effort: "low" } }; s.send(turn); expect(s.native.at(-1)).toBe(JSON.stringify(turn));
    s.send({ id: 4, method: "thread/resume", params: { threadId: "foreground" } }); s.receive({ id: 4, result: { thread: { id: "foreground" }, model: "test" } });
    const update = JSON.parse(s.native.at(-1)!);
    s.receive({ method: "thread/closed", params: { threadId: "foreground" } });
    const count = s.states.length; vi.advanceTimersByTime(6000); expect(s.states).toHaveLength(count);
    s.receive({ id: update.id, result: {} }); expect(s.client.at(-1)).not.toContain(update.id);
    expect(s.states.at(-1)).toMatchObject({ sessions: 0 });
  });
  it("reconciles newly advertised capabilities without inventing unsupported effort", () => {
    const s = session("codex"); s.bridge.setModels("late", new Map([["plain", []]])); s.bridge.setEffort("ultra");
    const unchanged = { id: 7, method: "turn/start", params: { model: "plain", effort: null } }; s.send(unchanged); expect(s.native.at(-1)).toBe(JSON.stringify(unchanged));
    s.send({ id: 1, method: "initialize", params: {} }); s.receive({ id: 1, result: {} });
    s.send({ id: 2, method: "thread/resume", params: { threadId: "late" } }); s.receive({ id: 2, result: { thread: { id: "late" }, model: "late", reasoningEffort: "xhigh" } });
    s.send({ id: 3, method: "model/list", params: {} }); s.receive({ id: 3, result: { data: [{ model: "late", supportedReasoningEfforts: EFFORTS.map((reasoningEffort) => ({ reasoningEffort })) }] } });
    expect(JSON.parse(s.native.at(-1)!)).toMatchObject({ method: "thread/settings/update", params: { effort: "ultra" } });
  });
  it("reconciles model capabilities that arrive during an older mapping update", () => {
    const s = session("codex"); s.bridge.setModels("late", new Map()); s.bridge.setEffort("ultra");
    s.send({ id: 1, method: "initialize", params: {} }); s.receive({ id: 1, result: {} });
    s.send({ id: 2, method: "thread/resume", params: { threadId: "late" } }); s.receive({ id: 2, result: { thread: { id: "late" }, model: "late", reasoningEffort: "low" } });
    const old = JSON.parse(s.native.at(-1)!); expect(old.params.effort).toBe("xhigh");
    s.send({ id: 3, method: "model/list", params: {} }); s.receive({ id: 3, result: { data: [{ model: "late", supportedReasoningEfforts: EFFORTS.map((reasoningEffort) => ({ reasoningEffort })) }] } });
    s.receive({ method: "thread/settings/updated", params: { threadId: "late", threadSettings: { effort: "xhigh" } } }); s.receive({ id: old.id, result: {} });
    expect(JSON.parse(s.native.at(-1)!)).toMatchObject({ method: "thread/settings/update", params: { effort: "ultra" } });
  });
  it("keeps acknowledgment when a new preference maps to the already applied native level", () => {
    const s = session("codex"); s.bridge.setModels("legacy", new Map([["legacy", ["low", "medium", "high", "xhigh"]]])); s.bridge.setEffort("xhigh");
    s.send({ id: 1, method: "initialize", params: {} }); s.receive({ id: 1, result: {} });
    s.send({ id: 2, method: "thread/resume", params: { threadId: "existing" } }); s.receive({ id: 2, result: { thread: { id: "existing" }, model: "legacy", reasoningEffort: "xhigh" } });
    const count = s.native.length; s.bridge.setEffort("max"); expect(s.native).toHaveLength(count);
    expect(s.states.at(-1)).toMatchObject({ requested: "max", mapped: "xhigh", applied: true, sessions: 1 });
  });
  it("neutralizes the Claude effort environment pin without changing permission or hook settings", () => {
    const settings = { permissions: { defaultMode: "plan", deny: ["Bash(rm *)"] }, hooks: { Stop: [] }, env: { KEEP: "yes", CLAUDE_CODE_EFFORT_LEVEL: "high" } };
    const args = ["--print", "--settings", JSON.stringify(settings), "--input-format", "stream-json"];
    const updated = claudeLaunchArgs(args);
    expect(JSON.parse(updated[2]!)).toEqual({ ...settings, env: { KEEP: "yes", CLAUDE_CODE_EFFORT_LEVEL: "" } });
    expect(updated.filter((_, index) => index !== 2)).toEqual(args.filter((_, index) => index !== 2));
    expect(claudeLaunchArgs(["--settings", "malformed"]) ).toEqual(["--settings", "malformed"]);
  });
  it.each(EFFORTS)("maps %s using native capabilities", (value) => {
    expect(mappedEffort("codex", value, EFFORTS)).toBe(value);
    expect(mappedEffort("claude", value)).toBe(value === "ultra" ? "xhigh" : value);
    expect(["low", "medium", "high", "xhigh"]).toContain(mappedEffort("codex", value));
  });
  it("passes malformed input and unrelated requests through byte for byte", () => {
    const s = session("codex"); s.bridge.setEffort("ultra");
    for (const line of ["not json", "null", "[]", '{ "id": 3, "method":"thread/settings/update","params":{"threadId":"t","approvalPolicy":"on-request","sandboxPolicy":{"type":"readOnly"}}}']) {
      s.bridge.fromClient(line); expect(s.native.at(-1)).toBe(line);
    }
  });
  it("leaves traffic untouched when there is no valid shared preference", () => {
    const s = session("codex"); const line = '{"id":2,"method":"turn/start","params":{"threadId":"t","effort":"low"}}';
    s.bridge.fromClient(line); expect(s.native).toEqual([line]);
  });
  it("enforces current effort on ordinary new and existing chat requests without changing permissions or input", () => {
    const s = session("codex"); s.bridge.setEffort("ultra");
    const params = { threadId: "existing", model: "test", effort: "low", approvalPolicy: "on-request", sandboxPolicy: { type: "readOnly" }, input: [{ type: "text", text: "keep this exactly" }], collaborationMode: { mode: "plan", settings: { model: "test", reasoning_effort: "low", developer_instructions: "keep" } } };
    s.send({ id: 2, method: "turn/start", params });
    expect(JSON.parse(s.native.at(-1)!)).toEqual({ id: 2, method: "turn/start", params: { ...params, effort: "ultra", collaborationMode: { ...params.collaborationMode, settings: { ...params.collaborationMode.settings, reasoning_effort: "ultra" } } } });
    s.send({ id: 3, method: "thread/start", params: { model: "test", config: { model_reasoning_effort: "low", approval_policy: "on-request", sandbox_mode: "read-only" } } });
    expect(JSON.parse(s.native.at(-1)!).params.config).toEqual({ model_reasoning_effort: "ultra", approval_policy: "on-request", sandbox_mode: "read-only" });
    const mode = { mode: "plan", settings: { model: "test", reasoning_effort: "low", developer_instructions: "keep" } };
    s.send({ id: 4, method: "thread/settings/update", params: { threadId: "existing", collaborationMode: mode, approvalPolicy: "on-request" } });
    expect(JSON.parse(s.native.at(-1)!).params).toEqual({ threadId: "existing", effort: "ultra", collaborationMode: { ...mode, settings: { ...mode.settings, reasoning_effort: "ultra" } }, approvalPolicy: "on-request" });
  });
  it("updates a loaded Codex thread and forwards its real settings notification", () => {
    const s = session("codex"); s.bridge.setEffort("high");
    s.send({ id: 1, method: "initialize", params: {} }); s.receive({ id: 1, result: {} });
    s.send({ id: 2, method: "thread/resume", params: { threadId: "existing" } }); s.receive({ id: 2, result: { thread: { id: "existing" }, model: "test" } });
    const update = JSON.parse(s.native.at(-1)!);
    expect(update).toMatchObject({ method: "thread/settings/update", params: { threadId: "existing", effort: "high" } });
    s.receive({ id: update.id, result: {} });
    expect(s.client.some((line) => line.includes(update.id))).toBe(false);
    expect(s.states.at(-1)?.applied).toBe(false);
    const notification = { method: "thread/settings/updated", params: { threadId: "existing", threadSettings: { model: "test", effort: "high", approvalPolicy: "on-request", sandboxPolicy: { type: "readOnly" } } } };
    s.receive(notification); expect(s.client.at(-1)).toBe(JSON.stringify(notification)); expect(s.states.at(-1)).toMatchObject({ requested: "high", applied: true, sessions: 1 });
    s.bridge.setEffort("medium"); expect(JSON.parse(s.native.at(-1)!).params.effort).toBe("medium");
  });
  it("applies Claude flags before releasing initialization, then verifies native readback", () => {
    const s = session("claude"); s.bridge.setEffort("ultra");
    s.send({ type: "control_request", request_id: "init", request: { subtype: "initialize" } });
    const initialized = { type: "control_response", response: { request_id: "init", subtype: "success", response: {} } };
    s.receive(initialized); expect(s.client).toEqual([]);
    const apply = JSON.parse(s.native.at(-1)!);
    expect(apply.request).toEqual({ subtype: "apply_flag_settings", settings: { effortLevel: "xhigh", ultracode: true } });
    s.receive({ type: "control_response", response: { request_id: apply.request_id, subtype: "success", response: {} } });
    const read = JSON.parse(s.native.at(-1)!); expect(read.request.subtype).toBe("get_settings");
    s.receive({ type: "control_response", response: { request_id: read.request_id, subtype: "success", response: { applied: { effort: "xhigh", ultracode: true } } } });
    expect(s.client).toEqual([JSON.stringify(initialized)]); expect(s.states.at(-1)).toMatchObject({ applied: true, requested: "ultra" });
    s.bridge.setEffort("low"); expect(JSON.parse(s.native.at(-1)!).request.settings).toEqual({ effortLevel: "low", ultracode: false });
  });
  it("reports a native refusal and releases initialization without pretending the change applied", () => {
    const s = session("claude"); s.bridge.setEffort("high");
    s.send({ type: "control_request", request_id: "init", request: { subtype: "initialize" } });
    s.receive({ type: "control_response", response: { request_id: "init", subtype: "success" } });
    const apply = JSON.parse(s.native.at(-1)!);
    s.receive({ type: "control_response", response: { request_id: apply.request_id, subtype: "error", error: "unsupported" } });
    expect(s.states.at(-1)).toMatchObject({ applied: false, error: expect.stringContaining("refused") }); expect(s.client).toHaveLength(1);
  });
  it("replaces stale explicit Claude effort without changing other live flags", () => {
    const s = session("claude"); s.bridge.setEffort("max");
    s.send({ type: "control_request", request_id: "user", request: { subtype: "apply_flag_settings", settings: { effortLevel: "low", outputStyle: "concise" } } });
    expect(JSON.parse(s.native.at(-1)!).request.settings).toEqual({ effortLevel: "max", ultracode: false, outputStyle: "concise" });
  });
});
