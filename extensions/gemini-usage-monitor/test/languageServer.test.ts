import * as fs from "fs";
import * as http from "http";
import type { AddressInfo } from "net";
import * as os from "os";
import * as path from "path";
import { afterEach, describe, expect, it } from "vitest";
import {
  LANGUAGE_SERVER_SERVICE,
  QUOTA_SUMMARY_METHOD,
  discoverEndpoint,
  isAntigravityHost,
  isHubProcess,
  orderPorts,
  parseCsrfToken,
  parseHubPort,
  parseLsofPorts,
  parsePsOutput,
  parseWindowsProcessJson,
  postRpc,
  selectServers,
  type ServerProcess,
} from "../src/providers/languageServer";

const APP_ROOT = process.platform === "win32" ? "C:\\Apps\\Antigravity IDE\\resources\\app" : "/opt/antigravity/resources/app";
const EXE = path.join(APP_ROOT, "extensions", "antigravity", "bin", "language_server_x64");
const HOME = process.platform === "win32" ? "C:\\Users\\me" : "/home/me";
const EXT = process.platform === "win32" ? ".exe" : "";
const AGY = path.join(HOME, ".gemini", "bin", "agy" + EXT);

function proc(pid: number, args: string, executable = EXE): ServerProcess {
  return { pid, executable, commandLine: `${executable} ${args}`, ports: [] };
}

describe("parseCsrfToken", () => {
  it("reads --csrf_token and never the extension-server token", () => {
    expect(parseCsrfToken("ls --extension_server_csrf_token other --csrf_token abc-123")).toBe("abc-123");
    expect(parseCsrfToken("ls --csrf_token=xyz")).toBe("xyz");
    expect(parseCsrfToken('ls --csrf_token "quoted"')).toBe("quoted");
    expect(parseCsrfToken("ls --extension_server_csrf_token only")).toBeNull();
  });
});

describe("selectServers", () => {
  it("keeps this install's servers only, main-process server first", () => {
    const other = path.join("/elsewhere", "Antigravity", "resources", "app", "extensions", "antigravity", "bin", "ls");
    const picked = selectServers(
      [
        proc(1, "--enable_lsp --csrf_token a"),
        proc(2, "--csrf_token b"),
        proc(3, "--csrf_token c", other),
        proc(4, "--no_token_here"),
      ],
      APP_ROOT,
    );
    expect(picked.map((p) => p.pid)).toEqual([2, 1]);
  });

  it("adds agy hubs after this install's servers, and only hubs with a token", () => {
    const picked = selectServers(
      [
        proc(5, "--hub --hub-port=59895 --app_data_dir=antigravity --csrf_token h", AGY),
        proc(6, "--hub --hub-port=1", AGY),
        proc(7, "chat --csrf_token x", AGY),
        proc(2, "--csrf_token b"),
      ],
      APP_ROOT,
      HOME,
    );
    expect(picked.map((p) => p.pid)).toEqual([2, 5]);
  });

  it("finds an agy hub on its own when the editor has no built-in server", () => {
    const hub = proc(9, "--hub --hub-port 40000 --csrf_token h", AGY);
    expect(selectServers([hub], APP_ROOT, HOME).map((p) => p.pid)).toEqual([9]);
  });

  it("never trusts an agy hub outside this user's ~/.gemini/bin", () => {
    const spoof = proc(10, "--hub --hub-port 40001 --csrf_token h", path.join(os.tmpdir(), "agy" + EXT));
    const otherUser = proc(11, "--hub --hub-port 40002 --csrf_token h", path.join(path.dirname(HOME), "someone", ".gemini", "bin", "agy" + EXT));
    expect(selectServers([spoof, otherUser], APP_ROOT, HOME)).toEqual([]);
  });
});

describe("agy hub helpers", () => {
  it("recognizes the hub by its full path, executable name and --hub flag", () => {
    const base = { pid: 1, ports: [] };
    expect(isHubProcess({ ...base, executable: AGY, commandLine: `${AGY} --hub --csrf_token t` }, HOME)).toBe(true);
    expect(isHubProcess({ ...base, executable: "", commandLine: `${AGY} --hub --csrf_token t` }, HOME)).toBe(true);
    expect(isHubProcess({ ...base, executable: AGY, commandLine: `${AGY} chat` }, HOME)).toBe(false);
    expect(isHubProcess({ ...base, executable: "/usr/bin/legacy-agy-tool", commandLine: "legacy-agy-tool --hub" }, HOME)).toBe(false);
  });

  it("accepts a bare agy name only where the process list is limited to this user", () => {
    const bare = { pid: 1, ports: [], executable: "", commandLine: "agy --hub --csrf_token t" };
    expect(isHubProcess(bare, HOME)).toBe(process.platform !== "win32");
  });

  it("reads --hub-port and tries it first", () => {
    expect(parseHubPort("agy --hub --hub-port=59895 --csrf_token t")).toBe(59895);
    expect(parseHubPort("agy --hub --hub-port 40000")).toBe(40000);
    expect(parseHubPort("agy --hub")).toBeNull();
    expect(orderPorts([59898, 59895], "agy --hub --hub-port=59895")).toEqual([59895, 59898]);
    expect(orderPorts([59898], "agy --hub --hub-port=59895")).toEqual([59898]);
    expect(orderPorts([1, 2], "language_server --csrf_token t")).toEqual([1, 2]);
  });
});

describe("process and port parsers", () => {
  it("parses the Windows discovery JSON, single object or array, tolerating junk", () => {
    expect(parseWindowsProcessJson('{"pid":7,"exe":"C:\\\\x.exe","cmd":"x --csrf_token t","ports":51891}')).toEqual([
      { pid: 7, executable: "C:\\x.exe", commandLine: "x --csrf_token t", ports: [51891] },
    ]);
    expect(parseWindowsProcessJson('[{"pid":7,"cmd":"x","ports":[1,2]},{"pid":"bad"},null]')).toHaveLength(1);
    expect(parseWindowsProcessJson("")).toEqual([]);
    expect(parseWindowsProcessJson("not json")).toEqual([]);
  });

  it("parses ps output, keeping language servers only", () => {
    const out = parsePsOutput("  12  501 /a/language_server_macos_arm --csrf_token t\n 13 501 /bin/zsh\n");
    expect(out).toEqual([{ pid: 12, executable: "/a/language_server_macos_arm", commandLine: "/a/language_server_macos_arm --csrf_token t", ports: [] }]);
  });

  it("parses ps output, keeping this user's agy hubs and dropping other users' processes", () => {
    const hub = "/Users/me/.gemini/bin/agy";
    const stdout = [
      ` 21 501 ${hub} --hub --hub-port=40000 --csrf_token t`,
      ` 22 501 ${hub} chat`,
      ` 23 502 /a/language_server_macos_arm --csrf_token other-user`,
    ].join("\n");
    const out = parsePsOutput(stdout, 501, "/Users/me");
    expect(out.map((p) => p.pid)).toEqual([21]);
    expect(parsePsOutput(stdout).map((p) => p.pid)).toContain(23);
    expect(parsePsOutput(stdout, 501).map((p) => p.pid)).not.toContain(23);
  });

  it("parses lsof -Fn listen addresses", () => {
    expect(parseLsofPorts("p12\nf9\nn127.0.0.1:51891\nf10\nn*:51892\nn[::1]:51891\n").sort()).toEqual([51891, 51892]);
  });
});

describe("host detection", () => {
  it("recognizes an editor that ships the Antigravity extension", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "ag-host-"));
    expect(isAntigravityHost(root)).toBe(false);
    fs.mkdirSync(path.join(root, "extensions", "antigravity"), { recursive: true });
    fs.writeFileSync(path.join(root, "extensions", "antigravity", "package.json"), "{}");
    expect(isAntigravityHost(root)).toBe(true);
  });

  it("recognizes an Antigravity IDE without the built-in extension by its product.json", () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), "ag-product-"));
    fs.writeFileSync(path.join(root, "product.json"), JSON.stringify({ nameShort: "Code", applicationName: "code" }));
    expect(isAntigravityHost(root)).toBe(false);
    fs.writeFileSync(path.join(root, "product.json"), JSON.stringify({ nameShort: "Antigravity IDE", applicationName: "antigravity-ide" }));
    expect(isAntigravityHost(root)).toBe(true);
    fs.writeFileSync(path.join(root, "product.json"), "not json");
    expect(isAntigravityHost(root)).toBe(false);
  });

  it("discovery stops at not-antigravity without listing processes", async () => {
    expect(await discoverEndpoint(path.join(os.tmpdir(), "no-such-editor"))).toEqual({ ok: false, reason: "not-antigravity" });
  });
});

describe("postRpc", () => {
  let server: http.Server | undefined;
  afterEach(() => server?.close());

  async function listen(handler: http.RequestListener): Promise<number> {
    server = http.createServer(handler);
    await new Promise<void>((resolve) => server!.listen(0, "127.0.0.1", resolve));
    return (server!.address() as AddressInfo).port;
  }

  it("sends a Connect-JSON POST with the CSRF header to the loopback port", async () => {
    let seen: { path?: string; csrf?: string; proto?: string; body?: string } = {};
    const port = await listen((req, res) => {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", () => {
        seen = { path: req.url, csrf: req.headers["x-codeium-csrf-token"] as string, proto: req.headers["connect-protocol-version"] as string, body };
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end('{"response":{"groups":[]}}');
      });
    });

    const res = await postRpc({ port, scheme: "http", csrfToken: "tok" }, QUOTA_SUMMARY_METHOD, { forceRefresh: true });
    expect(res).toEqual({ status: 200, body: { response: { groups: [] } } });
    expect(seen).toEqual({ path: `/${LANGUAGE_SERVER_SERVICE}/${QUOTA_SUMMARY_METHOD}`, csrf: "tok", proto: "1", body: '{"forceRefresh":true}' });
  });

  it("returns the status with a null body for non-JSON, and null when nothing listens", async () => {
    const port = await listen((_req, res) => {
      res.writeHead(403);
      res.end("forbidden");
    });
    expect(await postRpc({ port, scheme: "http", csrfToken: "bad" }, QUOTA_SUMMARY_METHOD, {})).toEqual({ status: 403, body: null });
    server!.close();
    server = undefined;
    expect(await postRpc({ port, scheme: "http", csrfToken: "t" }, QUOTA_SUMMARY_METHOD, {})).toBeNull();
  });
});
