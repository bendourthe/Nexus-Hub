import { execFile } from "child_process";
import * as fs from "fs";
import * as http from "http";
import * as https from "https";
import * as path from "path";

/**
 * Local transport to the Antigravity language server, the process that backs
 * Antigravity's own "Settings > Models > Models & Usage" panel.
 *
 * Nothing here talks to the internet. The language server listens on random
 * loopback ports and requires the CSRF token it was launched with; both are read
 * from the user's own process list, held in memory only, and never logged or
 * persisted. Requests go to 127.0.0.1 alone, using the Connect protocol's JSON
 * form (POST, `Connect-Protocol-Version: 1`), which the server accepts beside its
 * binary protobuf form.
 *
 * Kept free of the `vscode` module so it can be unit-tested and probed under
 * plain Node.
 */

export const LANGUAGE_SERVER_SERVICE = "exa.language_server_pb.LanguageServerService";
export const QUOTA_SUMMARY_METHOD = "RetrieveUserQuotaSummary";
export const USER_STATUS_METHOD = "GetUserStatus";

const COMMAND_TIMEOUT_MS = 15_000;
const REQUEST_TIMEOUT_MS = 10_000;

/** A running language server as listed by the operating system. */
export interface ServerProcess {
  pid: number;
  /** Executable path, or the command line's first token when the OS hides it. */
  executable: string;
  commandLine: string;
  /** Loopback ports the process listens on (filled only for selected candidates). */
  ports: number[];
}

/** A reachable language server endpoint. The token never leaves this module's callers. */
export interface ServerEndpoint {
  pid: number;
  port: number;
  scheme: "http" | "https";
  csrfToken: string;
}

/** Why no endpoint could be produced. */
export type DiscoveryFailure = "not-antigravity" | "server-not-found" | "server-unreachable";

export type DiscoveryResult =
  | { ok: true; endpoint: ServerEndpoint }
  | { ok: false; reason: DiscoveryFailure };

/** The built-in Antigravity extension folder that ships the language server. */
export function antigravityExtensionDir(appRoot: string): string {
  return path.join(appRoot, "extensions", "antigravity");
}

/** True when the host editor ships the Antigravity language server (so this is Antigravity). */
export function isAntigravityHost(appRoot: string): boolean {
  return fs.existsSync(path.join(antigravityExtensionDir(appRoot), "package.json"));
}

/**
 * Read `--csrf_token` from a language-server command line. The lookbehind keeps
 * `--extension_server_csrf_token` (a different secret) from matching.
 */
export function parseCsrfToken(commandLine: string): string | null {
  const match = /(?:^|\s)--csrf_token(?:=|\s+)"?([^\s"]+)"?/.exec(commandLine);
  return match ? match[1] : null;
}

function normalizeForCompare(p: string): string {
  const unified = p.replace(/\\/g, "/");
  return process.platform === "win32" ? unified.toLowerCase() : unified;
}

/**
 * Pick the language servers that belong to THIS editor install, best first.
 *
 * Antigravity runs two servers: one owned by the main process (serves the
 * Models & Usage panel) and one owned by the extension host, launched with
 * `--enable_lsp`. The main-process server is preferred because it is the one the
 * panel reads; the other is kept as a fallback. A server from a different
 * install (an older Antigravity beside Antigravity IDE) is excluded by path.
 */
export function selectServers(processes: ServerProcess[], appRoot: string): ServerProcess[] {
  const extDir = normalizeForCompare(antigravityExtensionDir(appRoot));
  const ours = processes.filter((p) => {
    const where = normalizeForCompare(p.executable || p.commandLine);
    return where.includes(extDir) && parseCsrfToken(p.commandLine) != null;
  });
  const isLsp = (p: ServerProcess): number => (/(?:^|\s)--enable_lsp\b/.test(p.commandLine) ? 1 : 0);
  return ours.sort((a, b) => isLsp(a) - isLsp(b));
}

function run(file: string, args: string[]): Promise<string> {
  return new Promise((resolve) => {
    execFile(file, args, { timeout: COMMAND_TIMEOUT_MS, windowsHide: true, maxBuffer: 4 * 1024 * 1024 }, (error, stdout) => {
      // A non-zero exit (e.g. lsof with no matches) still yields usable stdout.
      resolve(error && !stdout ? "" : String(stdout));
    });
  });
}

// One PowerShell call lists every language server with its listening ports, so a
// discovery costs a single process spawn on Windows.
const WINDOWS_DISCOVERY_SCRIPT = [
  "$ErrorActionPreference='SilentlyContinue'",
  "$p=@(Get-CimInstance Win32_Process -Filter \"Name LIKE 'language_server%'\")",
  "$o=foreach($x in $p){[pscustomobject]@{pid=[int]$x.ProcessId;exe=[string]$x.ExecutablePath;cmd=[string]$x.CommandLine;" +
    "ports=@(Get-NetTCPConnection -State Listen -OwningProcess $x.ProcessId | Select-Object -ExpandProperty LocalPort -Unique)}}",
  "ConvertTo-Json -InputObject @($o) -Compress -Depth 3",
].join(";");

/** Parse the Windows discovery script's JSON output. Never throws. */
export function parseWindowsProcessJson(stdout: string): ServerProcess[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(stdout.trim() || "[]");
  } catch {
    return [];
  }
  const list = Array.isArray(parsed) ? parsed : [parsed];
  const out: ServerProcess[] = [];
  for (const item of list) {
    if (item == null || typeof item !== "object") {
      continue;
    }
    const rec = item as Record<string, unknown>;
    const pid = Number(rec.pid);
    if (!Number.isInteger(pid) || typeof rec.cmd !== "string") {
      continue;
    }
    const rawPorts = Array.isArray(rec.ports) ? rec.ports : rec.ports != null ? [rec.ports] : [];
    out.push({
      pid,
      executable: typeof rec.exe === "string" ? rec.exe : "",
      commandLine: rec.cmd,
      ports: rawPorts.map(Number).filter((n) => Number.isInteger(n) && n > 0),
    });
  }
  return out;
}

/** Parse `ps -axww -o pid=,command=` output, keeping language servers only. */
export function parsePsOutput(stdout: string): ServerProcess[] {
  const out: ServerProcess[] = [];
  for (const line of stdout.split(/\r?\n/)) {
    const match = /^\s*(\d+)\s+(.*)$/.exec(line);
    if (!match || !/language_server_/.test(match[2])) {
      continue;
    }
    const commandLine = match[2];
    out.push({ pid: Number(match[1]), executable: commandLine.split(/\s+--/)[0], commandLine, ports: [] });
  }
  return out;
}

/** Parse `lsof -Fn` field output (`n127.0.0.1:51891`, `n*:51891`, `n[::1]:51891`) into ports. */
export function parseLsofPorts(stdout: string): number[] {
  const ports = new Set<number>();
  for (const line of stdout.split(/\r?\n/)) {
    const match = /^n.*:(\d+)$/.exec(line.trim());
    if (match) {
      ports.add(Number(match[1]));
    }
  }
  return [...ports];
}

/** List the running language servers (with ports on Windows; ports filled lazily elsewhere). */
export async function listServerProcesses(): Promise<ServerProcess[]> {
  if (process.platform === "win32") {
    const stdout = await run("powershell.exe", ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", WINDOWS_DISCOVERY_SCRIPT]);
    return parseWindowsProcessJson(stdout);
  }
  return parsePsOutput(await run("ps", ["-axww", "-o", "pid=,command="]));
}

async function listeningPorts(proc: ServerProcess): Promise<number[]> {
  if (proc.ports.length > 0 || process.platform === "win32") {
    return proc.ports;
  }
  return parseLsofPorts(await run("lsof", ["-nP", "-a", "-iTCP", "-sTCP:LISTEN", "-p", String(proc.pid), "-Fn"]));
}

/** The certificate authority Antigravity's own client trusts for the HTTPS port. */
export function readServerCa(appRoot: string): Buffer | undefined {
  try {
    return fs.readFileSync(path.join(antigravityExtensionDir(appRoot), "dist", "languageServer", "cert.pem"));
  } catch {
    return undefined;
  }
}

/** HTTP status plus the parsed JSON body, or null when the call could not complete. */
export interface RpcResponse {
  status: number;
  body: unknown;
}

/** POST one Connect-JSON RPC to a loopback endpoint. Resolves null on any transport failure. */
export function postRpc(
  endpoint: Omit<ServerEndpoint, "pid">,
  method: string,
  payload: unknown,
  ca?: Buffer,
): Promise<RpcResponse | null> {
  const body = JSON.stringify(payload ?? {});
  const options: https.RequestOptions = {
    host: "127.0.0.1",
    port: endpoint.port,
    method: "POST",
    path: `/${LANGUAGE_SERVER_SERVICE}/${method}`,
    headers: {
      "Content-Type": "application/json",
      "Connect-Protocol-Version": "1",
      "x-codeium-csrf-token": endpoint.csrfToken,
      "Content-Length": Buffer.byteLength(body),
    },
    timeout: REQUEST_TIMEOUT_MS,
  };
  if (endpoint.scheme === "https") {
    // Verified against the CA Antigravity ships; the certificate names 127.0.0.1.
    options.ca = ca;
    options.servername = "localhost";
    options.rejectUnauthorized = true;
  }
  const transport = endpoint.scheme === "https" ? https : http;
  return new Promise((resolve) => {
    const req = transport.request(options, (res) => {
      const chunks: Buffer[] = [];
      res.on("data", (c: Buffer) => chunks.push(c));
      res.on("end", () => {
        let parsed: unknown = null;
        try {
          parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
        } catch {
          parsed = null;
        }
        resolve({ status: res.statusCode ?? 0, body: parsed });
      });
      res.on("error", () => resolve(null));
    });
    req.on("timeout", () => req.destroy());
    req.on("error", () => resolve(null));
    req.end(body);
  });
}

/**
 * Find a reachable endpoint for this install. Each candidate port is tried over
 * plain loopback HTTP first, then over HTTPS with Antigravity's CA, and the first
 * one that answers the cheap user-status RPC with 200 wins.
 */
export async function discoverEndpoint(appRoot: string): Promise<DiscoveryResult> {
  if (!isAntigravityHost(appRoot)) {
    return { ok: false, reason: "not-antigravity" };
  }
  const candidates = selectServers(await listServerProcesses(), appRoot);
  if (candidates.length === 0) {
    return { ok: false, reason: "server-not-found" };
  }
  const ca = readServerCa(appRoot);
  for (const proc of candidates) {
    const csrfToken = parseCsrfToken(proc.commandLine) as string;
    for (const port of await listeningPorts(proc)) {
      for (const scheme of ["http", "https"] as const) {
        const res = await postRpc({ port, scheme, csrfToken }, USER_STATUS_METHOD, {}, ca);
        if (res?.status === 200 && res.body != null) {
          return { ok: true, endpoint: { pid: proc.pid, port, scheme, csrfToken } };
        }
      }
    }
  }
  return { ok: false, reason: "server-unreachable" };
}
