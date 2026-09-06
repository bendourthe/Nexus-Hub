import { describe, expect, it } from "vitest";
import {
  CONSENT_PROMPT_WILL_NOT_READ,
  CONSENT_PROMPT_WILL_READ,
  CONSENT_SCOPE,
  CONSENT_STATE_KEY,
  ConsentGate,
  consentPromptRequest,
  consentRequiredError,
  type ConsentAnswer,
  type ConsentPrompt,
  type ConsentPromptRequest,
  type ConsentStateLike
} from "../src/providers/consent";

class FakeState implements ConsentStateLike {
  public readonly values = new Map<string, unknown>();
  public failUpdate = false;

  public get<T>(key: string): T | undefined {
    return this.values.get(key) as T | undefined;
  }

  public async update(key: string, value: unknown): Promise<void> {
    if (this.failUpdate) {
      throw new Error("consent state unavailable");
    }
    if (value === undefined) {
      this.values.delete(key);
    } else {
      this.values.set(key, value);
    }
  }
}

class ScriptedPrompt implements ConsentPrompt {
  public calls = 0;
  public readonly seen: ConsentPromptRequest[] = [];

  public constructor(private readonly answers: ConsentAnswer[]) {}

  public async ask(request: ConsentPromptRequest): Promise<ConsentAnswer> {
    this.calls += 1;
    this.seen.push(request);
    return this.answers.shift() ?? "dismissed";
  }
}

class ThrowingPrompt implements ConsentPrompt {
  public calls = 0;

  public async ask(): Promise<ConsentAnswer> {
    this.calls += 1;
    throw new Error("prompt host unavailable");
  }
}

const fixedNow = (): Date => new Date("2026-08-05T12:00:00Z");

function gate(
  prompt: ConsentPrompt,
  state = new FakeState(),
  scope = CONSENT_SCOPE
): { gate: ConsentGate; state: FakeState } {
  return {
    gate: new ConsentGate(state, prompt, fixedNow, scope),
    state
  };
}

describe("consent disclosure", () => {
  it("states the read boundary and names every excluded source", () => {
    const request = consentPromptRequest();
    const willRead = request.willRead.join(" ").toLowerCase();
    const willNotRead = request.willNotRead.join(" ").toLowerCase();

    expect(willRead).toContain("read-only");
    expect(willRead).toContain("one named key");
    expect(willRead).toContain("one request");

    // Every exclusion the auth probe names must appear, because the prompt is the
    // only place the user learns what the extension will not touch.
    for (const excluded of [
      "cookies",
      "login data",
      "keychain",
      "process memory",
      "shell history",
      "html"
    ]) {
      expect(willNotRead).toContain(excluded);
    }
  });

  it("never promises to read a browser or credential store", () => {
    const willRead = CONSENT_PROMPT_WILL_READ.join(" ").toLowerCase();
    expect(willRead).not.toContain("cookie");
    expect(willRead).not.toContain("keychain");
    expect(willRead).not.toContain("password");
    expect(CONSENT_PROMPT_WILL_NOT_READ.length).toBeGreaterThan(0);
  });

  it("raises an authorization-required error rather than a bespoke code", () => {
    const error = consentRequiredError();
    expect(error.code).toBe("authorization-required");
    expect(error.sourceAttempt).toBe("credential-api");
  });
});

describe("ConsentGate", () => {
  it("prompts once, persists the grant, and never asks again", async () => {
    const prompt = new ScriptedPrompt(["granted"]);
    const { gate: consent, state } = gate(prompt);

    expect(consent.status()).toEqual({ state: "undecided" });
    expect(await consent.ensure()).toMatchObject({ state: "granted" });
    expect(consent.isGranted()).toBe(true);

    expect(await consent.ensure()).toMatchObject({ state: "granted" });
    expect(prompt.calls).toBe(1);
    expect(state.values.get(CONSENT_STATE_KEY)).toMatchObject({
      decision: "granted",
      scope: CONSENT_SCOPE
    });
  });

  it("treats refusal as a first-class answer and stops asking", async () => {
    const prompt = new ScriptedPrompt(["declined"]);
    const { gate: consent } = gate(prompt);

    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(prompt.calls).toBe(1);
    expect(consent.isGranted()).toBe(false);
  });

  it("persists nothing when the prompt is dismissed and does not re-nag", async () => {
    const prompt = new ScriptedPrompt(["dismissed", "granted"]);
    const { gate: consent, state } = gate(prompt);

    expect(await consent.ensure()).toEqual({ state: "undecided" });
    expect(state.values.has(CONSENT_STATE_KEY)).toBe(false);

    // Dismissal is not an answer, so nothing is stored - but the dialog must not
    // reopen on every refresh tick either.
    expect(await consent.ensure()).toEqual({ state: "undecided" });
    expect(prompt.calls).toBe(1);
  });

  it("discards a decision recorded against a different disclosure scope", async () => {
    const state = new FakeState();
    state.values.set(CONSENT_STATE_KEY, {
      decision: "granted",
      scope: "state-db-allowlisted-key+usage-json/v0",
      decidedAt: "2026-08-01T00:00:00Z"
    });
    const prompt = new ScriptedPrompt(["declined"]);
    const { gate: consent } = gate(prompt, state);

    // A widened boundary invalidates the old grant instead of inheriting it.
    expect(consent.isGranted()).toBe(false);
    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(prompt.calls).toBe(1);
  });

  it.each([
    ["a non-object record", "granted"],
    ["an unknown decision", { decision: "maybe", scope: CONSENT_SCOPE, decidedAt: "x" }],
    ["a missing timestamp", { decision: "granted", scope: CONSENT_SCOPE }]
  ])("ignores %s", async (_label, stored) => {
    const state = new FakeState();
    state.values.set(CONSENT_STATE_KEY, stored);
    const { gate: consent } = gate(new ScriptedPrompt([]), state);
    expect(consent.status()).toEqual({ state: "undecided" });
  });

  it("clears the decision on revoke and allows exactly one more prompt", async () => {
    const prompt = new ScriptedPrompt(["granted", "declined"]);
    const { gate: consent, state } = gate(prompt);

    await consent.ensure();
    await consent.revoke();
    expect(state.values.has(CONSENT_STATE_KEY)).toBe(false);
    expect(consent.isGranted()).toBe(false);

    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(prompt.calls).toBe(2);
  });

  it("honors an unpersistable answer coherently for the session only", async () => {
    const state = new FakeState();
    state.failUpdate = true;
    const prompt = new ScriptedPrompt(["granted"]);
    const { gate: consent } = gate(prompt, state);

    expect(await consent.ensure()).toMatchObject({ state: "granted" });
    expect(state.values.has(CONSENT_STATE_KEY)).toBe(false);

    // The decision must be coherent across the whole gate: a storage fault that
    // left `ensure()` reporting granted while `isGranted()` read false would make
    // capability and the credential source disagree.
    expect(consent.isGranted()).toBe(true);
    expect(await consent.ensure()).toMatchObject({ state: "granted" });
    expect(prompt.calls).toBe(1);
  });

  it("does not read a storage fault as consent when the answer was a refusal", async () => {
    const state = new FakeState();
    state.failUpdate = true;
    const { gate: consent } = gate(new ScriptedPrompt(["declined"]), state);

    expect(await consent.ensure()).toMatchObject({ state: "declined" });
    expect(consent.isGranted()).toBe(false);
  });

  it("treats a failing prompt host as undecided without consenting", async () => {
    const prompt = new ThrowingPrompt();
    const { gate: consent } = gate(prompt);

    expect(await consent.ensure()).toEqual({ state: "undecided" });
    expect(await consent.ensure()).toEqual({ state: "undecided" });
    expect(prompt.calls).toBe(1);
    expect(consent.isGranted()).toBe(false);
  });
});
