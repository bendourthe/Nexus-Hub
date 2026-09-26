// Nexus-Hub completion gate for OpenClaw (v4.13.2).
//
// On `before_agent_finalize`, asks the installed Nexus-Hub gate core whether
// this session's full /implement run is complete, and returns `revise` with the
// core's reason when it is not. OpenClaw allows at most three revisions per run
// and gives each handler 15 seconds, so the core runs with a 10-second budget.
// Needs plugins.entries.nexus-completion-gate.enabled and
// hooks.allowConversationAccess (see `openclaw plugins enable`).
// Policy: catalog/skills/workflow/implement-phase/references/completion-contract.md
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
// Shared gate call (see the OpenCode and Pi plugins for the same block).
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const CORE = join(homedir(), ".nexus-hub", "scripts", "completion_gate.py");
const PYTHONS = process.platform === "win32" ? ["python", "py"] : ["python3", "python"];

function runGate(sessionId, platform, timeoutMs = 25000, budgetSeconds = "25") {
  const payload = JSON.stringify({ hook_event_name: "Stop", session_id: sessionId, platform });
  const env = { ...process.env, NEXUS_GATE_FORMAT: "plugin", NEXUS_GATE_BUDGET_SECONDS: budgetSeconds };
  return new Promise((resolve) => {
    const attempt = (index) => {
      if (index >= PYTHONS.length) return resolve(null);
      let child;
      try {
        child = spawn(PYTHONS[index], [CORE, "stop"], { shell: false, env, windowsHide: true });
      } catch {
        return attempt(index + 1);
      }
      let out = "";
      let done = false;
      const finish = (value) => {
        if (!done) {
          done = true;
          clearTimeout(timer);
          resolve(value);
        }
      };
      const timer = setTimeout(() => {
        child.kill();
        finish(null);
      }, timeoutMs);
      child.on("error", () => {
        if (!done) {
          done = true;
          clearTimeout(timer);
          attempt(index + 1);
        }
      });
      child.stdout.on("data", (chunk) => (out += chunk));
      child.on("close", () => {
        try {
          finish(out.trim() ? JSON.parse(out) : null);
        } catch {
          finish(null);
        }
      });
      child.stdin.on("error", () => {});
      child.stdin.end(payload);
    };
    attempt(0);
  });
}

export default definePluginEntry({
  id: "nexus-completion-gate",
  name: "Nexus-Hub completion gate",
  description: "Revise the final answer while a full /implement run is incomplete.",
  register(api) {
    api.on("before_agent_finalize", async (_event, ctx) => {
      const id = ctx && ctx.sessionId;
      if (!id) return;
      const verdict = await runGate(id, "openclaw", 12000, "10");
      if (!verdict || verdict.decision !== "continue" || !verdict.reason) return;
      return {
        action: "revise",
        reason: verdict.reason,
        retry: { instruction: verdict.reason, idempotencyKey: "nexus-completion-gate", maxAttempts: 3 },
      };
    });
  },
});
