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
  parseCsrfToken,
  parseLsofPorts,
  parsePsOutput,
  parseWindowsProcessJson,
  postRpc,
  selectServers,
  type ServerProcess,
} from "../src/providers/languageServer";

const APP_ROOT = process.platform === "win32" ? "C:\\Apps\\Antigravity IDE\\resources\\app" : "/opt/antigravity/resources/app";
const EXE = path.join(APP_ROOT, "extensions", "antigravity", "bin", "language_server_x64");

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
    const out = parsePsOutput("  12 /a/language_server_macos_arm --csrf_token t\n 13 /bin/zsh\n");
    expect(out).toEqual([{ pid: 12, executable: "/a/language_server_macos_arm", commandLine: "/a/language_server_macos_arm --csrf_token t", ports: [] }]);
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
