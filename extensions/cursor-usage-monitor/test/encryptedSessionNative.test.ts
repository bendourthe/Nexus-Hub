import { execFileSync } from "node:child_process";
import { createCipheriv, randomBytes, randomUUID } from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, join, relative } from "node:path";
import { expect, it } from "vitest";
import { CursorSessionAdapter, DEFAULT_SESSION_KEY } from "../src/providers/session";
import { ENCRYPTED_SESSION_PREFIX } from "../src/providers/encryptedSession";

it.skipIf(process.platform !== "win32")("uses real SQLite and Windows DPAPI only within a synthetic profile", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const tempBase = realpathSync(tmpdir());
  const owned = mkdtempSync(join(tempBase, "nexus-cursor-native-"));
  const key = randomBytes(32);
  try {
    const statePath = join(owned, "User", "globalStorage", "state.vscdb");
    const localState = join(owned, "Local State");
    mkdirSync(dirname(statePath), { recursive: true });
    const protect = "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Security; " +
      "$b=[Convert]::FromBase64String([Console]::In.ReadToEnd()); " +
      "$p=[Security.Cryptography.ProtectedData]::Protect($b,$null," +
      "[Security.Cryptography.DataProtectionScope]::CurrentUser); " +
      "[Console]::Out.Write([Convert]::ToBase64String($p)); [Array]::Clear($b,0,$b.Length)";
    const powershell = join(process.env.SystemRoot ?? "C:\\Windows", "System32", "WindowsPowerShell", "v1.0", "powershell.exe");
    // Fixture setup only: a cold Windows PowerShell start on a busy runner can exceed 10 seconds.
    const wrapped = Buffer.from(execFileSync(powershell,
      ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", protect],
      { input: key.toString("base64"), encoding: "utf8", windowsHide: true, timeout: 30000, maxBuffer: 4096 }).trim(), "base64");
    const writeKey = (value: Buffer) => writeFileSync(localState, JSON.stringify({
      os_crypt: { encrypted_key: Buffer.concat([Buffer.from("DPAPI"), value]).toString("base64") }
    }));
    writeKey(wrapped);
    const synthetic = "synthetic-session-" + randomUUID();
    const nonce = randomBytes(12);
    const cipher = createCipheriv("aes-256-gcm", key, nonce);
    const ciphertext = Buffer.concat([cipher.update(synthetic, "utf8"), cipher.final()]);
    const blob = Buffer.concat([Buffer.from("v10"), nonce, ciphertext, cipher.getAuthTag()]);
    const encrypted = ENCRYPTED_SESSION_PREFIX + blob.toString("base64");
    const database = new DatabaseSync(statePath);
    try {
      database.exec("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)");
      database.prepare("INSERT INTO ItemTable VALUES (?,?)").run(DEFAULT_SESSION_KEY, encrypted);
    } finally { database.close(); }
    const replaceSession = (value: string) => {
      const db = new DatabaseSync(statePath);
      try { db.prepare("UPDATE ItemTable SET value=? WHERE key=?").run(value, DEFAULT_SESSION_KEY); }
      finally { db.close(); }
    };
    const adapter = new CursorSessionAdapter({ statePath });
    let operations = 0;
    const operation = async (value: string) => {
      // A failing assertion prints a boolean, never session or key material.
      expect(value === synthetic).toBe(true);
      operations++;
      return { ok: true as const, value: true };
    };
    const encryptedDatabase = readFileSync(statePath);
    expect((await adapter.withSession(operation)).ok).toBe(true);
    expect(readFileSync(statePath).equals(encryptedDatabase)).toBe(true);
    expect(operations).toBe(1);
    const tampered = Buffer.from(blob);
    tampered[tampered.length - 1] ^= 1;
    replaceSession(ENCRYPTED_SESSION_PREFIX + tampered.toString("base64"));
    const badTag = await adapter.withSession(operation);
    expect(!badTag.ok && badTag.error.code === "session-decryption-unavailable").toBe(true);
    expect(operations).toBe(1);
    replaceSession(encrypted);
    writeKey(randomBytes(48));
    const badKey = await adapter.withSession(operation);
    expect(!badKey.ok && badKey.error.code === "session-decryption-unavailable").toBe(true);
    expect(operations).toBe(1);
    unlinkSync(localState);
    replaceSession(synthetic);
    expect((await adapter.withSession(operation)).ok).toBe(true);
    expect(operations).toBe(2);
  } finally {
    key.fill(0);
    const resolved = realpathSync(owned);
    const child = relative(tempBase, resolved);
    if (!child || child.startsWith("..") || isAbsolute(child) || !basename(resolved).startsWith("nexus-cursor-native-")) {
      throw new Error("Unsafe synthetic-profile cleanup path.");
    }
    rmSync(resolved, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
  }
}, 60000);
