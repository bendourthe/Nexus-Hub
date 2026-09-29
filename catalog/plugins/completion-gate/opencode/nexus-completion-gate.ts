// Nexus-Hub completion gate for OpenCode (v4.13.2).
//
// On `session.idle`, asks the installed Nexus-Hub gate core whether this
// session's full /implement run is complete. When the core answers "continue",
// starts another turn with `client.session.prompt`. Sessions without a full-run
// record are never touched. Installed user-global only; remove with the
// Nexus-Hub uninstaller or opt out with NEXUS_HUB_COMPLETION_PLUGINS=0.
// Policy: catalog/skills/workflow/implement-phase/references/completion-contract.md
// Shared gate call, copied verbatim into each TypeScript plugin because a
// user-global plugin must not import files outside its own directory.
// Runs the installed core with an argument array and no shell, sends the
// payload on stdin, and returns its JSON verdict, or null on any failure:
// a gate that cannot evaluate must never trap the session.
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { delimiter, isAbsolute, join } from "node:path";

const CORE = join(homedir(), ".nexus-hub", "scripts", "completion_gate.py");
const PYTHON_NAMES = process.platform === "win32" ? ["python.exe", "py.exe"] : ["python3", "python"];

function pythonPaths(env) {
  const pathKey = Object.keys(env).sort().find((key) => key.toLowerCase() === "path");
  const entries = pathKey ? (env[pathKey] || "").split(delimiter) : [];
  const directories = entries
    .map((entry) => entry.replace(/^"(.*)"$/, "$1"))
    .filter((entry) => isAbsolute(entry));
  return PYTHON_NAMES.flatMap((name) => directories.map((entry) => join(entry, name)));
}

function runGate(sessionId, platform, timeoutMs = 25000, budgetSeconds = "25") {
  const payload = JSON.stringify({ hook_event_name: "Stop", session_id: sessionId, platform });
  const env = { ...process.env, NEXUS_GATE_FORMAT: "plugin", NEXUS_GATE_BUDGET_SECONDS: budgetSeconds };
  const pythons = pythonPaths(env);
  return new Promise((resolve) => {
    const attempt = (index) => {
      if (index >= pythons.length) return resolve(null);
      let child;
      try {
        child = spawn(pythons[index], [CORE, "stop"], { shell: false, env, windowsHide: true });
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

export const NexusCompletionGate = async ({ client }) => ({
  event: async ({ event }) => {
    if (!event || event.type !== "session.idle") return;
    const id = event.properties && event.properties.sessionID;
    if (!id) return;
    const verdict = await runGate(id, "opencode");
    if (!verdict || verdict.decision !== "continue" || !verdict.reason) return;
    await client.session.prompt({ path: { id }, body: { parts: [{ type: "text", text: verdict.reason }] } });
  },
});
