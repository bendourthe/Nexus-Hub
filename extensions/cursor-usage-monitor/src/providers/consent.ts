import type { ProviderError } from "../types";
import { providerError } from "./errors";

export const CONSENT_STATE_KEY = "cursorUsage.liveTransportConsent";

/**
 * Identifies the exact boundary the prompt discloses. Widening what the session
 * adapter reads MUST bump this value, so a stored "granted" can never silently
 * authorize a larger read than the user actually agreed to.
 */
export const CONSENT_SCOPE = "state-db-allowlisted-key+usage-json/v1";

export const CONSENT_PROMPT_TITLE =
  "Allow Cursor Usage to read your Cursor sign-in for live usage numbers?";

/**
 * The disclosure is exported rather than inlined at the call site so the tests
 * can assert the promise the user is shown matches what the adapter does.
 */
export const CONSENT_PROMPT_WILL_READ: readonly string[] = [
  "Open Cursor's own application state database on this machine, read-only.",
  "Read one named key from it to reuse the Cursor session you are already signed in to.",
  "Send one request to Cursor's own usage endpoint using that session."
];

export const CONSENT_PROMPT_WILL_NOT_READ: readonly string[] = [
  "No browser cookies, saved passwords, or Login Data file.",
  "No operating-system keychain, process memory, or shell history.",
  "No HTML billing page, and no search of your filesystem for credentials."
];

export type ConsentDecision = "granted" | "declined";

/** A prompt the user closed without answering. Never persisted. */
export type ConsentAnswer = ConsentDecision | "dismissed";

export type ConsentStatus =
  | { state: "granted"; decidedAt: string }
  | { state: "declined"; decidedAt: string }
  | { state: "undecided" };

export interface ConsentRecord {
  decision: ConsentDecision;
  scope: string;
  decidedAt: string;
}

export interface ConsentPromptRequest {
  title: string;
  willRead: readonly string[];
  willNotRead: readonly string[];
}

export interface ConsentPrompt {
  ask(request: ConsentPromptRequest): Promise<ConsentAnswer>;
}

/**
 * Deliberately narrower than the store's `MementoLike`: the provider layer owns
 * the consent decision and must not gain a dependency on the usage store.
 */
export interface ConsentStateLike {
  get<T>(key: string): T | undefined;
  update(key: string, value: unknown): Thenable<void>;
}

export function consentPromptRequest(): ConsentPromptRequest {
  return {
    title: CONSENT_PROMPT_TITLE,
    willRead: CONSENT_PROMPT_WILL_READ,
    willNotRead: CONSENT_PROMPT_WILL_NOT_READ
  };
}

export function consentRequiredError(): ProviderError {
  return providerError("authorization-required", "credential-api");
}

export class ConsentGate {
  private promptSuppressed = false;
  /**
   * Holds a decision that could not be written to storage. Without it a failed
   * persist would leave `ensure()` reporting "granted" while `isGranted()` still
   * read false, so capability and the credential source would disagree. It is
   * deliberately not durable: the decision is re-asked on the next activation.
   */
  private sessionDecision: ConsentRecord | undefined;

  public constructor(
    private readonly state: ConsentStateLike,
    private readonly prompt: ConsentPrompt,
    private readonly now: () => Date = () => new Date(),
    private readonly scope: string = CONSENT_SCOPE
  ) {}

  public status(): ConsentStatus {
    const record =
      decodeConsentRecord(
        this.state.get<unknown>(CONSENT_STATE_KEY),
        this.scope
      ) ?? this.sessionDecision;
    if (record === undefined) {
      return { state: "undecided" };
    }
    return { state: record.decision, decidedAt: record.decidedAt };
  }

  public isGranted(): boolean {
    return this.status().state === "granted";
  }

  /**
   * Resolves consent, prompting at most once for the lifetime of the decision.
   * A stored decision - granted or declined - is returned without re-prompting,
   * which is what keeps refusal a first-class path rather than a nag loop.
   */
  public async ensure(): Promise<ConsentStatus> {
    const existing = this.status();
    if (existing.state !== "undecided" || this.promptSuppressed) {
      return existing;
    }

    let answer: ConsentAnswer;
    try {
      answer = await this.prompt.ask(consentPromptRequest());
    } catch {
      this.promptSuppressed = true;
      return { state: "undecided" };
    }
    if (answer === "dismissed") {
      // Not an answer, so nothing is persisted; suppressed for this session only
      // so a dismissed dialog never reopens on every refresh tick.
      this.promptSuppressed = true;
      return { state: "undecided" };
    }

    const record: ConsentRecord = {
      decision: answer,
      scope: this.scope,
      decidedAt: this.now().toISOString()
    };
    try {
      await this.state.update(CONSENT_STATE_KEY, record);
    } catch {
      // The decision could not be persisted. Honor it for this session without
      // re-prompting rather than treating a storage fault as consent.
      this.promptSuppressed = true;
      this.sessionDecision = record;
    }
    return answer === "granted"
      ? { state: "granted", decidedAt: record.decidedAt }
      : { state: "declined", decidedAt: record.decidedAt };
  }

  /** Clears the decision so a later `ensure()` may prompt once again. */
  public async revoke(): Promise<void> {
    this.promptSuppressed = false;
    this.sessionDecision = undefined;
    await this.state.update(CONSENT_STATE_KEY, undefined);
  }
}

function decodeConsentRecord(
  value: unknown,
  scope: string
): ConsentRecord | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return undefined;
  }
  const record = value as Record<string, unknown>;
  if (record.scope !== scope) {
    // A scope change means the disclosure the user saw no longer describes what
    // the adapter would do, so the stale decision is discarded, not honored.
    return undefined;
  }
  if (record.decision !== "granted" && record.decision !== "declined") {
    return undefined;
  }
  if (typeof record.decidedAt !== "string" || record.decidedAt.length === 0) {
    return undefined;
  }
  return {
    decision: record.decision,
    scope,
    decidedAt: record.decidedAt
  };
}
