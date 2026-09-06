import { describe, expect, it } from "vitest";
import {
  automaticSessionProbe,
  CursorCredentialStore,
  resolveAuthPlan,
  resolveCursorStatePath,
  type SecretStorageLike
} from "../src/providers/auth";

class FakeSecrets implements SecretStorageLike {
  public readonly values = new Map<string, string>();
  public failGet = false;
  public failStore = false;
  public failDelete = false;

  public async get(key: string): Promise<string | undefined> {
    if (this.failGet) {
      throw new Error("fixture secret must not escape");
    }
    return this.values.get(key);
  }

  public async store(key: string, value: string): Promise<void> {
    if (this.failStore) {
      throw new Error("fixture secret must not escape");
    }
    this.values.set(key, value);
  }

  public async delete(key: string): Promise<void> {
    if (this.failDelete) {
      throw new Error("fixture secret must not escape");
    }
    this.values.delete(key);
  }
}

const credential = "fixture-credential-value-1234567890";

describe("CursorCredentialStore", () => {
  it("stores, scopes, reports, and clears an explicit credential", async () => {
    const secrets = new FakeSecrets();
    const store = new CursorCredentialStore(secrets);
    expect(await store.hasCredential()).toEqual({ ok: true, value: false });
    expect(await store.setCredential(`  ${credential}  `)).toEqual({
      ok: true
    });
    expect(await store.hasCredential()).toEqual({ ok: true, value: true });

    let observed = "";
    const result = await store.withCredential(async (value) => {
      observed = value;
      return { ok: true, value: "done" };
    });
    expect(result).toEqual({ ok: true, value: "done" });
    expect(observed).toBe(credential);

    expect(await store.clearCredential()).toEqual({ ok: true });
    expect(await store.hasCredential()).toEqual({ ok: true, value: false });
  });

  it.each(["", "short", "contains whitespace value", "line\nbreak"])(
    "rejects invalid explicit credentials",
    async (value) => {
      const store = new CursorCredentialStore(new FakeSecrets());
      const result = await store.setCredential(value);
      expect(!result.ok && result.error.code).toBe("invalid-credential");
    }
  );

  it("returns a typed missing-credential result", async () => {
    const result = await new CursorCredentialStore(
      new FakeSecrets()
    ).withCredential(async () => ({ ok: true, value: "unreachable" }));
    expect(!result.ok && result.error.code).toBe("missing-credential");
  });

  it("redacts credential adapter exceptions", async () => {
    const secrets = new FakeSecrets();
    const store = new CursorCredentialStore(secrets);
    await store.setCredential(credential);
    const result = await store.withCredential(async () => {
      throw new Error(`do not expose ${credential}`);
    });
    expect(!result.ok && result.error.code).toBe(
      "credential-adapter-unavailable"
    );
    expect(!result.ok && result.error.message).not.toContain(credential);
  });

  it("converts SecretStorage failures into fixed safe errors", async () => {
    const secrets = new FakeSecrets();
    const store = new CursorCredentialStore(secrets);
    secrets.failGet = true;
    expect(!(await store.hasCredential()).ok).toBe(true);
    expect(
      !(
        await store.withCredential(async () => ({
          ok: true,
          value: "unreachable"
        }))
      ).ok
    ).toBe(true);

    secrets.failGet = false;
    secrets.failStore = true;
    expect(!(await store.setCredential(credential)).ok).toBe(true);

    secrets.failStore = false;
    secrets.failDelete = true;
    expect(!(await store.clearCredential()).ok).toBe(true);
  });
});

describe("auth planning", () => {
  it("prefers an extension-owned SecretStorage credential", () => {
    expect(resolveAuthPlan({ hasStoredCredential: true })).toEqual({
      kind: "secret-storage",
      secretKey: "cursorUsage.credential"
    });
  });

  it("requires complete explicit authorization for a session probe", () => {
    const authorizedProbe = {
      statePath: "/fixture/state.vscdb",
      allowlistedKey: "fixture.cursor.session",
      authorizationId: "fixture-authorization"
    };
    expect(
      resolveAuthPlan({ hasStoredCredential: false, authorizedProbe })
    ).toEqual({ kind: "authorized-session-probe", ...authorizedProbe });
    expect(
      resolveAuthPlan({
        hasStoredCredential: false,
        authorizedProbe: { ...authorizedProbe, authorizationId: "" }
      })
    ).toEqual({ kind: "none", reason: "not-configured" });
    expect(resolveAuthPlan({ hasStoredCredential: false })).toEqual({
      kind: "none",
      reason: "authorization-required"
    });
  });

  it("keeps automatic session reuse disabled", () => {
    const result = automaticSessionProbe();
    expect(!result.ok && result.error.code).toBe("authorization-required");
  });

  it("resolves platform paths without touching the filesystem", () => {
    expect(
      resolveCursorStatePath("win32", {
        home: "C:\\fixture",
        appData: "C:\\fixture\\AppData\\Roaming"
      })
    ).toContain("Cursor\\User\\globalStorage\\state.vscdb");
    expect(
      resolveCursorStatePath("darwin", { home: "/fixture" })
    ).toBe(
      "/fixture/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
    );
    expect(
      resolveCursorStatePath("linux", {
        home: "/fixture",
        xdgConfigHome: "/fixture-config"
      })
    ).toBe("/fixture-config/Cursor/User/globalStorage/state.vscdb");
    expect(resolveCursorStatePath("aix", { home: "/fixture" })).toBeNull();
    expect(
      resolveCursorStatePath("win32", { home: "C:\\fixture" })
    ).toBeNull();
  });
});
