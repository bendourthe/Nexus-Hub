import { afterEach, beforeEach, describe, expect, it } from "vitest";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import {
  parseCodexCredential,
  resolveCodexAuthPath,
  readCodexCredential,
  isSyntheticAccountId,
} from "../src/providers/codex";

describe("parseCodexCredential", () => {
  it("parses the nested tokens shape", () => {
    const raw = JSON.stringify({
      tokens: { access_token: "sk-abc123", account_id: "acct_42" },
      last_refresh: "2026-07-16T00:00:00Z",
    });
    expect(parseCodexCredential(raw)).toEqual({ accessToken: "sk-abc123", accountId: "acct_42" });
  });

  it("parses the flat shape", () => {
    const raw = JSON.stringify({ access_token: "sk-flat", account_id: "acct_7" });
    expect(parseCodexCredential(raw)).toEqual({ accessToken: "sk-flat", accountId: "acct_7" });
  });

  it("accepts camelCase field names", () => {
    const raw = JSON.stringify({ tokens: { accessToken: "sk-camel", accountId: "acct_c" } });
    expect(parseCodexCredential(raw)).toEqual({ accessToken: "sk-camel", accountId: "acct_c" });
  });

  it("returns a null accountId when the account id is absent", () => {
    const raw = JSON.stringify({ tokens: { access_token: "sk-noacct" } });
    expect(parseCodexCredential(raw)).toEqual({ accessToken: "sk-noacct", accountId: null });
  });

  it("returns null when the access token is missing", () => {
    const raw = JSON.stringify({ tokens: { account_id: "acct_only" } });
    expect(parseCodexCredential(raw)).toBeNull();
  });

  it("returns null for malformed JSON", () => {
    expect(parseCodexCredential("{ not valid json")).toBeNull();
  });

  it("returns null for a non-object payload", () => {
    expect(parseCodexCredential("\"a string\"")).toBeNull();
    expect(parseCodexCredential("null")).toBeNull();
  });
});

describe("resolveCodexAuthPath", () => {
  const homeDir = path.join(path.sep, "home", "user");

  it("defaults to ~/.codex/auth.json when nothing is configured", () => {
    expect(resolveCodexAuthPath({ homeDir })).toBe(path.join(homeDir, ".codex", "auth.json"));
  });

  it("uses CODEX_HOME/auth.json when CODEX_HOME is set", () => {
    const codexHome = path.join(path.sep, "opt", "codex");
    expect(resolveCodexAuthPath({ codexHome, homeDir })).toBe(path.join(codexHome, "auth.json"));
  });

  it("prefers an explicit configured path over CODEX_HOME", () => {
    const configuredPath = path.join(path.sep, "custom", "creds.json");
    const codexHome = path.join(path.sep, "opt", "codex");
    expect(resolveCodexAuthPath({ configuredPath, codexHome, homeDir })).toBe(configuredPath);
  });

  it("expands a leading ~ in the configured path", () => {
    expect(resolveCodexAuthPath({ configuredPath: "~/creds/codex.json", homeDir })).toBe(
      path.join(homeDir, "creds", "codex.json"),
    );
  });

  it("ignores a blank configured path", () => {
    expect(resolveCodexAuthPath({ configuredPath: "   ", homeDir })).toBe(
      path.join(homeDir, ".codex", "auth.json"),
    );
  });
});

describe("isSyntheticAccountId", () => {
  it("flags email_ and local_ prefixes as synthetic", () => {
    expect(isSyntheticAccountId("email_abc")).toBe(true);
    expect(isSyntheticAccountId("local_xyz")).toBe(true);
  });

  it("treats a real account id and null as not synthetic", () => {
    expect(isSyntheticAccountId("acct_42")).toBe(false);
    expect(isSyntheticAccountId(null)).toBe(false);
  });
});

describe("readCodexCredential", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "codex-cred-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("reads and parses a valid credential file", () => {
    const authPath = path.join(tmpDir, "auth.json");
    fs.writeFileSync(authPath, JSON.stringify({ tokens: { access_token: "sk-ok", account_id: "acct_1" } }));
    const result = readCodexCredential(authPath);
    expect(result).toEqual({ ok: true, credential: { accessToken: "sk-ok", accountId: "acct_1" } });
  });

  it("returns a missing result when the file does not exist", () => {
    const result = readCodexCredential(path.join(tmpDir, "does-not-exist.json"));
    expect(result).toEqual({ ok: false, reason: "missing" });
  });

  it("returns an invalid result when the file is malformed", () => {
    const authPath = path.join(tmpDir, "auth.json");
    fs.writeFileSync(authPath, "{ broken json");
    const result = readCodexCredential(authPath);
    expect(result).toEqual({ ok: false, reason: "invalid" });
  });

  it("never surfaces the token in a failure result", () => {
    const authPath = path.join(tmpDir, "auth.json");
    fs.writeFileSync(authPath, JSON.stringify({ tokens: { account_id: "acct_only" } }));
    const result = readCodexCredential(authPath);
    expect(result).toEqual({ ok: false, reason: "invalid" });
  });
});
