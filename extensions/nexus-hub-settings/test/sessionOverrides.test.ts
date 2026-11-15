import { expect, it, vi } from "vitest";
import { CODEX_UI_HOOK } from "../src/vendorUiPatch";
import { historyEntries } from "../src/codexHistory";
import { validateMessage } from "../src/messages";
import { emptyModel } from "../src/viewModel";

it("leaves manual Codex effort alone until a new application event", async () => {
  let listener: (event: unknown) => void = () => {};
  const select = vi.fn().mockResolvedValue(true);
  const settings = { model: "same", reasoningEffort: "high", isLoading: false };
  const react = { useRef: () => ({ current: null }), useEffect: (effect: () => void) => effect() };
  const hook = new Function("window", "Rt", "it", CODEX_UI_HOOK + ";return nexusUseEffortBridge;")({ addEventListener: (_: string, callback: typeof listener) => { listener = callback; } }, react, () => ({ data: { models: [{ model: "same", supportedReasoningEfforts: ["low", "medium", "high"].map(reasoningEffort => ({ reasoningEffort })) }] } }));
  hook(settings, select, "local", null);
  const event = (revision: string) => ({ data: { type: "nexus-effort-v1", effort: "low", revision }, stopImmediatePropagation: vi.fn() });
  listener(event("default")); await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
  expect(select).toHaveBeenCalledWith("same", "low", { persistAsDefault: false });
  settings.reasoningEffort = "medium"; listener(event("default")); await Promise.resolve();
  expect(select).toHaveBeenCalledTimes(1);
  listener(event("apply-all")); await Promise.resolve(); await Promise.resolve();
  expect(select).toHaveBeenCalledTimes(2);
});
it("reads local history metadata, replaces duplicate titles and rejects invalid IDs", () => {
  const id = "01234567-1234-1234-1234-012345678901";
  const index = [{ id, thread_name: "Old", updated_at: "2026-11-04" }, { id, thread_name: "Current", updated_at: "2026-11-05" }, { id: "../../other", thread_name: "Bad", updated_at: "2026-11-05" }].map(x => JSON.stringify(x)).join("\n");
  expect(historyEntries(index + "\nbroken")).toEqual([{ id, label: "Current", description: "2026-11-05" }]);
});
it("blocks apply-all and upgrade messages in read-only panels and rejects injected fields", () => {
  const model = emptyModel("Default", "windows");
  for (const type of ["applyAll", "upgrade"]) {
    expect(validateMessage({ type }, { ...model, readOnly: true }).ok).toBe(false);
    expect(validateMessage({ type, command: "injected" }, { ...model, readOnly: false }).ok).toBe(false);
    expect(validateMessage({ type }, { ...model, readOnly: false }).ok).toBe(true);
  }
});
