import { createCipheriv } from "node:crypto";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { decryptStoredSession, ENCRYPTED_SESSION_PREFIX } from "../src/providers/encryptedSession";
import { CursorSessionAdapter } from "../src/providers/session";
import { createCredentialSource } from "../src/providers/liveAccess";
import { consentPromptRequest, ConsentGate, CONSENT_SCOPE, CONSENT_STATE_KEY } from "../src/providers/consent";

const TOKEN = "fixture.session.token-0123456789";
const STATE_PATH = resolve("fixture", "Cursor", "User", "globalStorage", "state.vscdb");

function fixture() {
  const key = Buffer.alloc(32, 7);
  const nonce = Buffer.alloc(12, 9);
  const cipher = createCipheriv("aes-256-gcm", key, nonce);
  const blob = Buffer.concat([Buffer.from("v10"), nonce,
    cipher.update(TOKEN, "utf8"), cipher.final(), cipher.getAuthTag()]);
  const encrypted = ENCRYPTED_SESSION_PREFIX + blob.toString("base64");
  const unwrapped = Buffer.from(key);
  const readLocalState = vi.fn(async () => JSON.stringify({
    os_crypt: { encrypted_key: Buffer.from("DPAPIprotected-fixture-key").toString("base64") }
  }));
  const unprotect = vi.fn(async () => unwrapped);
  return { encrypted, blob, key, unwrapped, readLocalState, unprotect,
    dependencies: { platform: "win32" as const, readLocalState, unprotect } };
}

describe("Cursor encrypted session", () => {
  it("discloses the Local State read and Windows data protection", () => {
    const disclosure = consentPromptRequest().willRead.join(" ");
    expect(disclosure).toContain("Local State");
    expect(disclosure).toContain("Windows data protection");
    expect(disclosure).toContain("in memory");
  });

  it("clears an unwrapped key with the wrong length", async () => {
    const f = fixture();
    const wrongKey = Buffer.alloc(16, 5);
    f.unprotect.mockResolvedValue(wrongKey);
    await expect(decryptStoredSession(f.encrypted, STATE_PATH, f.dependencies)).rejects.toThrow();
    expect(wrongKey.equals(Buffer.alloc(16))).toBe(true);
  });
  it("decrypts authenticated v10 data using only the application's named key", async () => {
    const f = fixture();
    expect(await decryptStoredSession(f.encrypted, STATE_PATH, f.dependencies)).toBe(TOKEN);
    expect(f.readLocalState).toHaveBeenCalledWith(resolve("fixture", "Cursor", "Local State"));
    expect(f.unprotect).toHaveBeenCalledWith(Buffer.from("protected-fixture-key"));
    expect(f.unwrapped.equals(Buffer.alloc(32))).toBe(true);
  });

  it.each(["linux", "darwin"] as const)("does not read or decrypt on %s", async (platform) => {
    const f = fixture();
    await expect(decryptStoredSession(f.encrypted, STATE_PATH, { ...f.dependencies, platform }))
      .rejects.toThrow("Cursor session decryption is unavailable.");
    expect(f.readLocalState).not.toHaveBeenCalled();
    expect(f.unprotect).not.toHaveBeenCalled();
  });

  it.each(["cursor-safe-storage:v2:AAAA", ENCRYPTED_SESSION_PREFIX + "***",
    ENCRYPTED_SESSION_PREFIX + Buffer.from("v11unsupported").toString("base64")])(
    "rejects an unsupported envelope before reading the application key", async (value) => {
      const f = fixture();
      await expect(decryptStoredSession(value, STATE_PATH, f.dependencies)).rejects.toThrow();
      expect(f.readLocalState).not.toHaveBeenCalled();
    });

  it("rejects tampering and clears the unwrapped key", async () => {
    const f = fixture();
    f.blob[f.blob.length - 1] ^= 1;
    await expect(decryptStoredSession(ENCRYPTED_SESSION_PREFIX + f.blob.toString("base64"),
      STATE_PATH, f.dependencies)).rejects.toThrow("Cursor session decryption is unavailable.");
    expect(f.unwrapped.equals(Buffer.alloc(32))).toBe(true);
  });

  it("replaces native exceptions with a fixed error", async () => {
    const f = fixture();
    f.unprotect.mockRejectedValue(new Error("private-key-path-and-secret"));
    await expect(decryptStoredSession(f.encrypted, STATE_PATH, f.dependencies))
      .rejects.toThrow(/^Cursor session decryption is unavailable\.$/);
  });

  it.each(["{}", "not-json", JSON.stringify({ os_crypt: { encrypted_key: "AAAA" } })])(
    "refuses a missing or malformed protected application key", async (text) => {
      const f = fixture();
      f.readLocalState.mockResolvedValue(text);
      await expect(decryptStoredSession(f.encrypted, STATE_PATH, f.dependencies)).rejects.toThrow();
      expect(f.unprotect).not.toHaveBeenCalled();
    });
});

function sessionAdapter(value: string, decryptSession: (value: string, path: string) => Promise<string>) {
  return new CursorSessionAdapter({ statePath: STATE_PATH, pathExists: () => true,
    decryptSession, loadSqlite: async () => ({ DatabaseSync: class {
      prepare() { return { get: () => ({ value }) }; }
      close() {}
    } }) });
}

describe("encrypted session integration", () => {
  it("hands only the decrypted token to the operation", async () => {
    const f = fixture();
    const adapter = sessionAdapter(f.encrypted,
      (value, path) => decryptStoredSession(value, path, f.dependencies));
    const operation = vi.fn(async (token: string) => ({ ok: true as const, value: token === TOKEN }));
    expect(await adapter.withSession(operation)).toEqual({ ok: true, value: true });
    expect(operation).toHaveBeenCalledWith(TOKEN);
  });

  it("keeps plaintext sessions compatible without decryption", async () => {
    const decrypt = vi.fn();
    expect(await sessionAdapter(TOKEN, decrypt).withSession(async () => ({ ok: true, value: true })))
      .toEqual({ ok: true, value: true });
    expect(decrypt).not.toHaveBeenCalled();
  });

  it.each(["failure", "invalid", "wrapped"])("does not send credentials after %s", async (mode) => {
    const operation = vi.fn();
    const adapter = sessionAdapter(fixture().encrypted, async () => {
      if (mode === "failure") { throw new Error("private"); }
      return mode === "invalid" ? "short" : fixture().encrypted;
    });
    expect(await adapter.withSession(operation)).toMatchObject({ ok: false,
      error: { code: "session-decryption-unavailable" } });
    expect(operation).not.toHaveBeenCalled();
  });

  it("does not touch encrypted session storage without current consent", async () => {
    const adapter = { capability: vi.fn(), withSession: vi.fn() };
    const source = createCredentialSource({
      secrets: { hasCredential: async () => ({ ok: true, value: false }), withCredential: vi.fn() },
      consent: { isGranted: () => false, ensure: vi.fn() }, adapter
    });
    expect(await source.withCredential(vi.fn())).toMatchObject({ ok: false,
      error: { code: "authorization-required" } });
    expect(adapter.withSession).not.toHaveBeenCalled();
  });

  it("requires a new decision for the previous plaintext-only scope", async () => {
    const old = { decision: "granted", scope: "state-db-allowlisted-key+model-key+usage-json/v2",
      decidedAt: "2026-11-05T00:00:00Z" };
    const update = vi.fn(async () => {});
    const ask = vi.fn(async () => "declined" as const);
    const consent = new ConsentGate({ get: <T,>() => old as T, update }, { ask });
    expect(consent.isGranted()).toBe(false);
    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(ask).toHaveBeenCalledOnce();
    expect(update).toHaveBeenCalledWith(CONSENT_STATE_KEY, expect.objectContaining({ scope: CONSENT_SCOPE }));
  });
});
