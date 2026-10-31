import { describe, expect, it } from "vitest";
import { validText, validateMessage } from "../src/messages";
import { buildModel } from "../src/viewModel";
import { explains, layers, showReport } from "./fixtures";

function model(trusted = true) {
  return buildModel({ report: showReport(), explains: explains(), inspect: (k) => layers(k), trusted, profile: "Default" });
}

const ok = (raw: unknown, m = model()) => {
  const checked = validateMessage(raw, m);
  expect(checked.ok).toBe(true);
  return checked.ok ? checked.message : undefined;
};
const bad = (raw: unknown, reason: string, m = model()) => {
  const checked = validateMessage(raw, m);
  expect(checked).toEqual({ ok: false, reason: expect.stringContaining(reason) });
};

describe("message validation against the catalog allowlist", () => {
  it("accepts ready and refresh", () => {
    expect(ok({ type: "ready" })).toEqual({ type: "ready" });
    expect(ok({ type: "refresh" })).toEqual({ type: "refresh" });
  });

  it("accepts a catalog choice for every tool, and a per-tool override only where the control allows it", () => {
    expect(ok({ type: "set", control: "posture", value: "full-auto" })).toEqual({ type: "set", control: "posture", value: "full-auto", tool: null });
    expect(ok({ type: "set", control: "effort", value: "high", tool: "codex" })).toMatchObject({ tool: "codex" });
    expect(ok({ type: "set", control: "git_guardrails", value: "off", tool: null })).toMatchObject({ value: "off" });
  });

  it.each(["constructor", "toString", "hasOwnProperty", "__proto__", "valueOf"])("answers a message typed %s with a refusal instead of throwing", (name) => {
    bad({ type: name }, "unknown message");
    bad(JSON.parse(`{"type":"${name}","control":"effort"}`), "unknown message");
  });

  it("requires a tool for a per-tool control and accepts a plain model id", () => {
    bad({ type: "set", control: "model", value: "opus" }, "chosen per tool");
    expect(ok({ type: "set", control: "model", value: "claude-opus-5-5", tool: "claude" })).toMatchObject({ value: "claude-opus-5-5", tool: "claude" });
  });

  it.each([
    [{ type: "bogus" }, "unknown message"],
    ["set", "unknown message"],
    [null, "unknown message"],
    [[], "unknown message"],
    [{ type: "set", control: "effort", value: "high", extra: 1 }, "unexpected fields"],
    [{ type: "set", control: "nope", value: "high" }, "unknown control"],
    [{ type: "set", control: "effort", value: "max" }, "invalid value"],
    [{ type: "set", control: "effort", value: 3 }, "invalid value"],
    [{ type: "set", control: "effort", value: "high", tool: 7 }, "invalid tool"],
    [{ type: "set", control: "posture", value: "ask", tool: "claude" }, "not set per tool"],
    [{ type: "set", control: "effort", value: "high", tool: "copilot-cli" }, "cannot be set"],
    [{ type: "set", control: "model", value: "-x", tool: "claude" }, "invalid value"],
    [{ type: "set", control: "model", value: "a b ", tool: "claude" }, "invalid value"],
    [{ type: "set", control: "model", value: "cafe" + String.fromCharCode(0x301) + "", tool: "claude" }, "invalid value"],
    [{ type: "set", control: "model", value: "x".repeat(201), tool: "claude" }, "invalid value"],
    [{ type: "reset", control: "effort", tool: "elsewhere" }, "unknown tool"],
    [{ type: "removeOverride", control: "effort", tool: "codex" }, "nothing removable"],
    [{ type: "removeOverride", control: "effort" }, "nothing removable"],
    [{ type: "openSource", control: "effort", write: "not-a-write" }, "unknown source"],
    [{ type: "openSource", control: "git_guardrails", write: "internal.git_guardrails" }, "unknown source"],
  ])("rejects %j", (raw, reason) => {
    bad(raw, reason);
  });

  it("accepts reset and removeOverride where the model offers them", () => {
    expect(ok({ type: "reset", control: "effort" })).toEqual({ type: "reset", control: "effort", tool: null });
    expect(ok({ type: "reset", control: "effort", tool: "claude" })).toMatchObject({ tool: "claude" });
    expect(ok({ type: "removeOverride", control: "effort", tool: "claude" })).toEqual({ type: "removeOverride", control: "effort", tool: "claude" });
  });

  it("accepts opening only a source the model marked openable, by write id", () => {
    expect(ok({ type: "openSource", control: "posture", write: "claude.posture" })).toEqual({ type: "openSource", control: "posture", write: "claude.posture" });
  });

  it("refuses every write while the panel is read-only, but still allows reading", () => {
    const readOnly = model(false);
    bad({ type: "set", control: "effort", value: "high" }, "read-only", readOnly);
    bad({ type: "reset", control: "effort" }, "read-only", readOnly);
    bad({ type: "removeOverride", control: "effort", tool: "claude" }, "read-only", readOnly);
    expect(ok({ type: "refresh" }, readOnly)).toEqual({ type: "refresh" });
    expect(ok({ type: "openSource", control: "posture", write: "claude.posture" }, readOnly)).toBeDefined();
  });

  it("validates free text the way the engine does", () => {
    expect(validText("claude-opus-5-5")).toBe(true);
    expect(validText("model:v1[1m]")).toBe(true);
    expect(validText("")).toBe(false);
    expect(validText(" lead")).toBe(false);
    expect(validText("--flag")).toBe(false);
    expect(validText(5)).toBe(false);
  });
});
