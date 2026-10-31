import { execFile } from "node:child_process";
import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import { ActionDoc, EXIT, ExplainData, ShowReport } from "./types";

/**
 * The only door from the panel to the engine.
 *
 * It runs `nexus_hub_cli.py settings ...` with an absolute interpreter, an
 * absolute script path inside the Nexus-Hub install root, `shell: false`, and the
 * install root as the working directory. Nothing is looked up on PATH and nothing
 * is taken from the workspace: a repository that plants `nexus-hub.cmd`,
 * `nexus-hub.exe`, or `python.exe` in its folder is never executed. The workspace
 * folder reaches the command only as the `--project` argument, which the engine
 * reads as data and never runs.
 */

export interface Interpreter {
  command: string;
  args: string[];
}

export type BridgeErrorKind = "no-install" | "no-python" | "timeout" | "spawn" | "exit" | "json" | "argument";

export class BridgeError extends Error {
  constructor(
    readonly kind: BridgeErrorKind,
    message: string,
    /** The command that was run or would be run, shown on the error card. */
    readonly command: string,
    /** What the user should do next. */
    readonly fix: string,
  ) {
    super(message);
    this.name = "BridgeError";
  }
}

export interface BridgeOptions {
  platform?: NodeJS.Platform;
  env?: NodeJS.ProcessEnv;
  home?: string;
  timeoutMs?: number;
  /** The user-scope `nexusHubSettings.pythonPath` value (never a workspace value). */
  pythonPath?: () => string | undefined;
  /** Test seam: use this interpreter and skip discovery. */
  interpreter?: Interpreter;
  listDir?: (dir: string) => string[];
  now?: () => number;
}

export const TIMEOUT_MS = 15_000;
const MAX_BUFFER = 16 * 1024 * 1024;
const PYTHON_FLAGS = ["-B", "-X", "utf8"];
const TOKEN_FILE = "settings-panel-token.json";
const CONTROL = /^[a-z][a-z_]{0,40}$/;
const TOOL = /^[a-z][a-z0-9-]{0,40}$/;
const VALUE_LIMIT = 200;

export const INSTALL_COMMAND: Record<"win32" | "posix", string> = {
  win32: "irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex",
  posix: "curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash",
};

function nodePath(platform: NodeJS.Platform): path.PlatformPath {
  return platform === "win32" ? path.win32 : path.posix;
}

/** The Nexus-Hub install root: `NEXUS_HUB_HOME` when set (as the launcher does), else `~/.nexus-hub`. */
export function installRoot(env: NodeJS.ProcessEnv, home: string, platform: NodeJS.Platform = process.platform): string {
  const p = nodePath(platform);
  const override = env.NEXUS_HUB_HOME?.trim();
  return override && p.isAbsolute(override) ? override : p.join(home, ".nexus-hub");
}

/** Highest Python 3 minor version first: `Python313` is 13, `PythonSoftwareFoundation.Python.3.12_x` is 12. */
function newestFirst(names: string[]): string[] {
  const minor = (name: string): number => Number(/^Python3(\d+)/.exec(name)?.[1] ?? /Python\.3\.(\d+)/.exec(name)?.[1] ?? 0);
  return [...names].sort((a, b) => minor(b) - minor(a));
}

/**
 * Absolute interpreter candidates in the standard install locations, best first.
 * A pure function of the platform and environment, so tests can exercise either
 * family on any host. No entry comes from PATH, the current directory, or a workspace.
 */
export function candidateInterpreters(
  platform: NodeJS.Platform,
  env: NodeJS.ProcessEnv,
  listDir: (dir: string) => string[],
): Interpreter[] {
  const p = nodePath(platform);
  if (platform !== "win32") {
    return ["/usr/bin/python3", "/usr/local/bin/python3", "/opt/homebrew/bin/python3", "/usr/bin/python"].map((command) => ({
      command,
      args: [...PYTHON_FLAGS],
    }));
  }
  const found: Interpreter[] = [];
  const roots = [
    env.LOCALAPPDATA ? p.join(env.LOCALAPPDATA, "Programs", "Python") : "",
    env.ProgramFiles ?? "",
    env["ProgramFiles(x86)"] ?? "",
  ].filter((dir) => dir.length > 0);
  for (const root of roots) {
    for (const entry of newestFirst(listDir(root).filter((name) => /^Python3\d+(-\d+)?$/.test(name)))) {
      found.push({ command: p.join(root, entry, "python.exe"), args: [...PYTHON_FLAGS] });
    }
  }
  const store = env.LOCALAPPDATA ? p.join(env.LOCALAPPDATA, "Microsoft", "WindowsApps") : "";
  if (store) {
    for (const entry of newestFirst(listDir(store).filter((name) => /^PythonSoftwareFoundation\.Python\.3\.\d+_/.test(name)))) {
      found.push({ command: p.join(store, entry, "python.exe"), args: [...PYTHON_FLAGS] });
    }
  }
  const launchers = [
    env.LOCALAPPDATA ? p.join(env.LOCALAPPDATA, "Programs", "Python", "Launcher", "py.exe") : "",
    p.join(env.SystemRoot ?? "C:\\Windows", "py.exe"),
  ].filter((command) => command.length > 0);
  for (const command of launchers) {
    found.push({ command, args: ["-3", ...PYTHON_FLAGS] });
  }
  return found;
}

/**
 * A regular file, or a link that cannot be followed with `stat`. The Microsoft Store Python is
 * an app-execution alias: `stat` fails with EACCES, `lstat` reports a link, and `CreateProcess`
 * runs it, so such a link counts as a file here. A dead link then fails at launch with a clear error.
 */
function isFile(target: string): boolean {
  try {
    return fs.statSync(target).isFile();
  } catch {
    try {
      return fs.lstatSync(target).isSymbolicLink();
    } catch {
      return false;
    }
  }
}

function quote(part: string): string {
  return /[\s"]/.test(part) ? `"${part.replace(/"/g, '\\"')}"` : part;
}

export interface CliResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  command: string;
}

export interface ActionOutcome {
  exitCode: number;
  /** Parsed for exit codes 0, 1, and 4. Null for a usage error (2) or a refusal (3). */
  doc: ActionDoc | null;
  /** The command's own message for exit codes 2 and 3. */
  message: string;
}

export interface TokenSpec {
  action: "set" | "remove-override";
  control: string;
  value: string | null;
  tool: string | null;
}

export interface ActionSpec {
  action: "set" | "reset" | "remove-override";
  control: string;
  value?: string;
  tool?: string | null;
  dryRun?: boolean;
  project?: string;
  /** Present only after a person confirmed a safety-weakening change. */
  token?: TokenSpec;
}

function checkControl(control: string): void {
  if (!CONTROL.test(control)) {
    throw new BridgeError("argument", `invalid control id ${JSON.stringify(control)}`, "", "Pick a control from the panel.");
  }
}

function checkTool(tool: string | null | undefined): void {
  if (tool != null && !TOOL.test(tool)) {
    throw new BridgeError("argument", `invalid tool id ${JSON.stringify(tool)}`, "", "Pick a tool from the panel.");
  }
}

function checkValue(value: string): void {
  const printable = [...value].every((char) => char >= " " && char <= "~");
  if (value.length === 0 || value.length > VALUE_LIMIT || !printable || value.startsWith("-")) {
    throw new BridgeError("argument", "the value must be 1 to 200 printable ASCII characters and not start with a hyphen", "", "Enter a different value.");
  }
}

function projectArg(project: string | undefined): string[] {
  return project ? [`--project=${project}`] : [];
}

/** The arguments after the script path for one action. Exported for tests. */
export function buildArgs(spec: ActionSpec): string[] {
  checkControl(spec.control);
  checkTool(spec.tool);
  const tail = [...(spec.dryRun ? ["--dry-run"] : []), "--json", ...projectArg(spec.project)];
  if (spec.action === "set") {
    checkValue(spec.value ?? "");
    return ["settings", "set", spec.control, spec.value as string, ...(spec.tool ? ["--tool", spec.tool] : []), ...tail];
  }
  if (spec.action === "reset") {
    return ["settings", "reset", spec.control, ...(spec.tool ? ["--tool", spec.tool] : []), ...tail];
  }
  if (!spec.tool) {
    throw new BridgeError("argument", "remove-override needs a tool", "", "Pick a tool from the panel.");
  }
  return ["settings", "remove-override", spec.control, "--tool", spec.tool, ...tail];
}

export class CliBridge {
  private readonly platform: NodeJS.Platform;
  private readonly env: NodeJS.ProcessEnv;
  private readonly home: string;
  private readonly timeoutMs: number;

  constructor(private readonly options: BridgeOptions = {}) {
    this.platform = options.platform ?? process.platform;
    this.env = options.env ?? process.env;
    this.home = options.home ?? os.homedir();
    this.timeoutMs = options.timeoutMs ?? TIMEOUT_MS;
  }

  root(): string {
    return installRoot(this.env, this.home, this.platform);
  }

  cliPath(): string {
    return nodePath(this.platform).join(this.root(), "scripts", "nexus_hub_cli.py");
  }

  /** The command a person can run in a terminal to see the same thing, for error cards. */
  describe(args: string[] = ["settings", "show", "--json"]): string {
    let interpreter: Interpreter | undefined;
    try {
      interpreter = this.interpreter();
    } catch {
      interpreter = undefined;
    }
    const lead = interpreter ? [interpreter.command, ...interpreter.args] : ["python"];
    return [...lead, this.cliPath(), ...args].map(quote).join(" ");
  }

  private installHint(): string {
    return `Install or repair Nexus-Hub, then reload the window. In a terminal: ${INSTALL_COMMAND[this.platform === "win32" ? "win32" : "posix"]}`;
  }

  interpreter(): Interpreter {
    if (this.options.interpreter) {
      return this.options.interpreter;
    }
    const p = nodePath(this.platform);
    const configured = this.options.pythonPath?.()?.trim();
    if (configured) {
      if (!p.isAbsolute(configured) || !isFile(configured)) {
        throw new BridgeError(
          "no-python",
          `nexusHubSettings.pythonPath is not an absolute path to an existing file: ${configured}`,
          "",
          "Open Settings, search for nexusHubSettings.pythonPath, and enter the full path to python.exe (or python3). Workspace values are ignored.",
        );
      }
      return { command: configured, args: [...PYTHON_FLAGS] };
    }
    const list = this.options.listDir ?? ((dir: string): string[] => {
      try {
        return fs.readdirSync(dir);
      } catch {
        return [];
      }
    });
    const found = candidateInterpreters(this.platform, this.env, list).find((candidate) => isFile(candidate.command));
    if (!found) {
      throw new BridgeError(
        "no-python",
        "no Python 3 interpreter was found in the standard install locations",
        "",
        "Install Python 3, or set nexusHubSettings.pythonPath to the full path of python.exe (or python3) in your user settings.",
      );
    }
    return found;
  }

  private childEnv(): NodeJS.ProcessEnv {
    return { ...this.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1", PYTHONDONTWRITEBYTECODE: "1" };
  }

  /** Run the CLI with these arguments. Rejects with a `BridgeError` for anything but an exit code. */
  run(args: string[]): Promise<CliResult> {
    const cli = this.cliPath();
    if (!isFile(cli)) {
      return Promise.reject(
        new BridgeError("no-install", `the Nexus-Hub command line was not found at ${cli}`, this.describe(args), this.installHint()),
      );
    }
    let interpreter: Interpreter;
    try {
      interpreter = this.interpreter();
    } catch (error) {
      return Promise.reject(error);
    }
    const argv = [...interpreter.args, cli, ...args];
    const command = [interpreter.command, ...argv].map(quote).join(" ");
    return new Promise<CliResult>((resolve, reject) => {
      execFile(
        interpreter.command,
        argv,
        { cwd: this.root(), env: this.childEnv(), shell: false, windowsHide: true, timeout: this.timeoutMs, maxBuffer: MAX_BUFFER, encoding: "utf8" },
        (error, stdout, stderr) => {
          const out = String(stdout ?? "");
          const err = String(stderr ?? "");
          if (!error) {
            resolve({ exitCode: 0, stdout: out, stderr: err, command });
            return;
          }
          const failure = error as NodeJS.ErrnoException & { killed?: boolean; code?: number | string };
          if (typeof failure.code === "number") {
            resolve({ exitCode: failure.code, stdout: out, stderr: err, command });
            return;
          }
          if (failure.killed) {
            reject(new BridgeError("timeout", `timed out after ${Math.round(this.timeoutMs / 1000)} seconds`, command, "Run the command above in a terminal to see why it is slow, then refresh."));
            return;
          }
          reject(new BridgeError("spawn", `could not start the interpreter (${failure.code ?? failure.message})`, command, "Set nexusHubSettings.pythonPath to a working Python 3 interpreter."));
        },
      );
    });
  }

  private parse<T>(result: CliResult, valid: (data: unknown) => boolean): T {
    let data: unknown;
    try {
      data = JSON.parse(result.stdout);
    } catch {
      const tail = result.stderr.trim().split(/\r?\n/).slice(-3).join(" | ");
      throw new BridgeError(
        result.stdout.trim() === "" ? "exit" : "json",
        `the command returned no usable JSON (exit ${result.exitCode})${tail ? `: ${tail}` : ""}`,
        result.command,
        "Run the command above in a terminal, fix what it reports, then refresh.",
      );
    }
    if (!valid(data)) {
      throw new BridgeError("json", "the command returned JSON in an unexpected shape", result.command, "Update Nexus-Hub so the panel and the command line match, then reload the window.");
    }
    return data as T;
  }

  private async readOnly<T>(args: string[], valid: (data: unknown) => boolean): Promise<T> {
    const result = await this.run(args);
    if (result.exitCode !== EXIT.OK) {
      const tail = result.stderr.trim().split(/\r?\n/).slice(-3).join(" | ");
      throw new BridgeError("exit", `the command exited with ${result.exitCode}${tail ? `: ${tail}` : ""}`, result.command, "Run the command above in a terminal to see the full message.");
    }
    return this.parse<T>(result, valid);
  }

  show(project?: string): Promise<ShowReport> {
    const isReport = (d: unknown): boolean => isRecord(d) && d.schema_version === 1 && Array.isArray(d.records) && isRecord(d.tools);
    return this.readOnly<ShowReport>(["settings", "show", "--json", ...projectArg(project)], isReport);
  }

  async explain(control: string, project?: string): Promise<ExplainData> {
    checkControl(control);
    const isExplain = (d: unknown): boolean => isRecord(d) && isRecord(d.control) && Array.isArray(d.writes);
    return this.readOnly<ExplainData>(["settings", "explain", control, "--json", ...projectArg(project)], isExplain);
  }

  async action(spec: ActionSpec): Promise<ActionOutcome> {
    const args = buildArgs(spec);
    const cleanup = spec.token && !spec.dryRun ? this.writeToken(spec.token) : undefined;
    try {
      const result = await this.run(args);
      return this.outcome(result);
    } finally {
      cleanup?.();
    }
  }

  private outcome(result: CliResult): ActionOutcome {
    const code = result.exitCode;
    if (code === EXIT.USAGE || code === EXIT.REFUSED) {
      const message = result.stderr.trim() || `the command exited with ${code}`;
      return { exitCode: code, doc: null, message };
    }
    if (code === EXIT.OK || code === EXIT.PARTIAL || code === EXIT.NOTHING) {
      const doc = this.parse<ActionDoc>(result, (d) => isRecord(d) && typeof d.action === "string" && typeof d.exit_code === "number");
      return { exitCode: code, doc, message: "" };
    }
    throw new BridgeError("exit", `the command exited with ${code}: ${result.stderr.trim().split(/\r?\n/).slice(-3).join(" | ")}`, result.command, "Run the command above in a terminal to see the full message.");
  }

  /** Record one VS Code setting the panel just wrote, so `reset` can restore it. */
  async recordEditorWrite(payload: { write: string; previous: { present: boolean; value?: unknown }; new: unknown; profile?: string }): Promise<void> {
    const result = await this.run(["settings", "record-editor-write", JSON.stringify(payload), "--json"]);
    if (result.exitCode !== EXIT.OK) {
      throw new BridgeError("exit", `recording the editor write failed: ${result.stderr.trim() || `exit ${result.exitCode}`}`, result.command, "Nothing was kept: the panel restores the previous VS Code value.");
    }
  }

  /**
   * Write the one-time confirmation token (owner-only, valid 30 seconds for this exact
   * change) that tells the engine a person confirmed. Returns the function that deletes it.
   */
  private writeToken(spec: TokenSpec): () => void {
    const dir = path.join(this.home, ".nexus-hub");
    const file = path.join(dir, TOKEN_FILE);
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    fs.rmSync(file, { force: true });
    const body = {
      token: crypto.randomBytes(32).toString("hex"),
      issued_at: (this.options.now ?? Date.now)() / 1000,
      action: spec.action,
      control: spec.control,
      value: spec.value,
      tool: spec.tool,
    };
    fs.writeFileSync(file, JSON.stringify(body), { mode: 0o600, flag: "wx" });
    return () => fs.rmSync(file, { force: true });
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
