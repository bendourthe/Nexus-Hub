import * as fs from "fs";
import * as path from "path";
import type * as vscode from "vscode";
import type { FetchLike } from "../src/providers/githubApi";

const FIXTURES = path.join(__dirname, "fixtures");

/** Parse one of the Phase 1 fixtures (captured or labelled synthetic). */
export function fixture<T = unknown>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(FIXTURES, name), "utf-8")) as T;
}

/**
 * A fake credential value, shaped like a GitHub token so a leak would be
 * recognizable, assembled at runtime so no credential-shaped literal sits in
 * the source. The leak test fails if any of these appears in an output.
 */
function fakeCredential(prefix: string, label: string): string {
  return [prefix, `FAKE${label}`.padEnd(36, "0")].join("_");
}
export const WORK_TOKEN = fakeCredential("gho", "WORKSESSION");
export const PERSONAL_TOKEN = fakeCredential("gho", "PERSONALSESSION");
export const ORG_TOKEN = fakeCredential("github_pat", "ORGANIZATION");
/**
 * Every substring a leak detector looks for in a fake token: the whole value,
 * its distinctive core (`FAKE...` without padding), and every 12-character
 * window, so a truncated, split, or partially masked token is still caught.
 * Windows made only of the zero padding are skipped: they are not distinctive.
 */
export function tokenSlices(token: string, width = 12): string[] {
  const slices = new Set<string>([token]);
  const core = token.match(/FAKE[A-Z]+/);
  if (core) slices.add(core[0]);
  for (let i = 0; i + width <= token.length; i++) {
    const window = token.slice(i, i + width);
    if (!/^[0_]+$/.test(window)) slices.add(window);
  }
  return [...slices];
}

/** The needles from `needles` found in `text`. */
export function findLeaks(text: string, needles: readonly string[]): string[] {
  return needles.filter((needle) => text.includes(needle));
}

/** Identity placeholders from the fixtures README; never allowed in an output. */
export const PLACEHOLDER_IDENTITIES = ["example-user", "example-org", "example-id"];

/** A JSON Response as fetch would return it. */
export function jsonResponse(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    statusText: status === 200 ? "OK" : "Error",
    headers: { "content-type": "application/json", ...headers },
  });
}

export interface RecordedRequest {
  url: string;
  init: RequestInit;
  authorization: string | undefined;
}

/** A fetch stub that routes by Authorization header and URL, and records every call. */
export function routedFetch(
  route: (url: URL, authorization: string | undefined) => Response | Promise<Response> | "throw",
): { fetch: FetchLike; calls: RecordedRequest[] } {
  const calls: RecordedRequest[] = [];
  const fetchImpl: FetchLike = async (input, init) => {
    const headers = (init.headers ?? {}) as Record<string, string>;
    calls.push({ url: input, init, authorization: headers.Authorization });
    const result = await route(new URL(input), headers.Authorization);
    if (result === "throw") {
      throw new TypeError("fetch failed");
    }
    return result;
  };
  return { fetch: fetchImpl, calls };
}

export interface FakeAccount {
  id: string;
  label: string;
  token: string;
}

/**
 * Models VS Code's GitHub authentication as decision (1b) records it: a call
 * without `account` returns the session of the extension's stored account
 * preference; with no preference and several sessions, a silent call returns
 * undefined; an interactive call (`createIfNone`) with no preference, or with
 * `clearSessionPreference`, "picks" `pickOnPrompt` and stores it.
 */
export class FakeGitHubAuth {
  readonly calls: Array<{ providerId: string; scopes: readonly string[]; options: Record<string, unknown> }> = [];
  preference: string | undefined;
  pickOnPrompt: string | undefined;

  constructor(public accounts: FakeAccount[]) {}

  private session(account: FakeAccount): vscode.AuthenticationSession {
    return {
      id: `session-${account.id}`,
      accessToken: account.token,
      account: { id: account.id, label: account.label },
      scopes: ["user:email"],
    };
  }

  async getSession(
    providerId: string,
    scopes: readonly string[],
    options: Record<string, unknown> = {},
  ): Promise<vscode.AuthenticationSession | undefined> {
    this.calls.push({ providerId, scopes: [...scopes], options: { ...options } });
    if (providerId !== "github") {
      return undefined;
    }
    if (options.clearSessionPreference) {
      this.preference = undefined;
    } else {
      const preferred = this.accounts.find((a) => a.id === this.preference);
      if (preferred) {
        return this.session(preferred);
      }
      if (this.accounts.length === 1) {
        return this.session(this.accounts[0]);
      }
    }
    if (options.createIfNone) {
      const picked = this.accounts.find((a) => a.id === this.pickOnPrompt);
      if (picked) {
        this.preference = picked.id;
        return this.session(picked);
      }
    }
    return undefined;
  }

  async getAccounts(_providerId: string): Promise<readonly vscode.AuthenticationSessionAccountInformation[]> {
    return this.accounts.map((a) => ({ id: a.id, label: a.label }));
  }
}

/** An in-memory SecretStorage that records what it is asked to store and delete. */
export class FakeSecretStorage {
  readonly values = new Map<string, string>();
  readonly stored: Array<{ key: string; value: string }> = [];
  readonly deleted: string[] = [];

  async get(key: string): Promise<string | undefined> {
    return this.values.get(key);
  }
  async store(key: string, value: string): Promise<void> {
    this.stored.push({ key, value });
    this.values.set(key, value);
  }
  async delete(key: string): Promise<void> {
    this.deleted.push(key);
    this.values.delete(key);
  }
  keys(): Promise<string[]> {
    return Promise.resolve([...this.values.keys()]);
  }
  onDidChange = (): { dispose(): void } => ({ dispose() {} });

  asSecretStorage(): vscode.SecretStorage {
    return this as unknown as vscode.SecretStorage;
  }
}

/** A Memento backed by a Map, for UsageStore. */
export function createMemento(): vscode.Memento {
  const values = new Map<string, unknown>();
  return {
    get<T>(key: string, defaultValue?: T): T | undefined {
      return values.has(key) ? (values.get(key) as T) : defaultValue;
    },
    async update(key: string, value: unknown): Promise<void> {
      if (value === undefined) {
        values.delete(key);
      } else {
        values.set(key, value);
      }
    },
    keys(): readonly string[] {
      return [...values.keys()];
    },
  } as vscode.Memento;
}

/** A routed fetch serving the Phase 1 fixtures by session value and endpoint. */
export function fixtureFetch(options: {
  personalByToken?: Record<string, string>;
  billing?: string;
  usage?: string;
}): ReturnType<typeof routedFetch> {
  return routedFetch((url, authorization) => {
    if (url.pathname === "/copilot_internal/user") {
      const value = authorization?.replace(/^token /, "") ?? "";
      const name = options.personalByToken?.[value];
      return name ? jsonResponse(fixture(name)) : jsonResponse({ message: "Bad credentials" }, 401);
    }
    if (url.pathname.endsWith("/copilot/billing")) {
      return options.billing ? jsonResponse(fixture(options.billing)) : jsonResponse({}, 404);
    }
    if (url.pathname.endsWith("/settings/billing/ai_credit/usage")) {
      return options.usage ? jsonResponse(fixture(options.usage)) : jsonResponse({}, 404);
    }
    return jsonResponse({ message: "Not Found" }, 404);
  });
}
