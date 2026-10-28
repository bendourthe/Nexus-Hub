import * as fs from "fs";
import * as path from "path";

/**
 * The opt-in "Save Raw Usage Response" command writes one redacted copy of the
 * usage response so a maintainer can see which fields the vendor serves (for
 * example whether resets are reported) without sharing anything identifying.
 *
 * Kept: every key, every number and boolean, ISO dates, short lowercase
 * enum-like words, short window ids ("5h"), and the plain-text `displayName` and
 * `description` of each `groups` / `buckets` entry, which name a model group or a
 * limit and are needed to tell the quota windows apart. Replaced with a
 * placeholder: every other string, any value
 * under an identity- or secret-shaped key (ids, emails, names, accounts,
 * organizations, owners, phones, tokens, passwords, cookies, sessions), and any
 * key that itself looks like an id or an email. A key is split into words first,
 * so `userId`, `display-name`, and `user_id` match alike, and a secret word
 * inside a run-together key (`sessiontoken`) matches too.
 *
 * Nothing from the decoded response is written as-is. Every kept key, number,
 * date, and enum word is rebuilt character by character from the constant
 * alphabets below, and booleans become fresh literals, so the saved document is
 * a new structure whose every character originates in this module. A key or
 * value containing a character outside its alphabet becomes a placeholder.
 */

const DATE = /^\d{4}-\d{2}-\d{2}([T ][0-9:.]+(Z|[+-]\d{2}:?\d{2})?)?$/;
const ENUM_WORD = /^[a-z][a-z_-]{0,31}$/;
// Quota window ids such as "5h" or "7d": a short count and a short unit, never a token.
const WINDOW_ID = /^\d{1,3}[a-z]{1,8}$/;
// The quota summary's own labels ("Gemini Models", "Five Hour Limit Remaining") name a
// model group or a limit, not a person, so they are kept; the same keys elsewhere are not.
const QUOTA_ARRAYS = new Set(["groups", "buckets"]);
const QUOTA_LABEL_KEYS = new Set(["displayName", "description"]);
const QUOTA_LABEL = /^[A-Za-z0-9 .,'()&/+:-]{1,160}$/;
const IDENTITY_KEY = /(^|_)(id|ids|uuid|guid|email|emails|name|names|username|login|user|users|account|accounts|org|orgs|organization|workspace|owner|handle|phone|token|tokens|key|keys|secret|password|passwd|cookie|cookies|session|auth|authorization|credential|credentials|url|uri)(_|$)/;
const SECRET_WORD = /token|secret|passw|cookie|credential|apikey|bearer/i;
const ID_SHAPED_KEY = /(^[0-9a-f-]{16,}$)|(\d{5,})|@/i;

const KEY_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-.$ ";
const NUMBER_CHARS = "0123456789.-+e";
const DATE_CHARS = "0123456789-T:.Z+ ";
const ENUM_CHARS = "abcdefghijklmnopqrstuvwxyz_-";
const WINDOW_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz";
const LABEL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,'()&/+:-";

/**
 * Copy `text` using only characters taken from `alphabet`, or return null when
 * any character falls outside it. Each output character is read from the
 * constant, selected by an equality test, never copied from `text` itself.
 */
function rebuild(text: string, alphabet: string): string | null {
  let out = "";
  for (const ch of text) {
    let matched = false;
    for (let i = 0; i < alphabet.length; i += 1) {
      if (ch === alphabet[i]) {
        out += alphabet[i];
        matched = true;
        break;
      }
    }
    if (!matched) {
      return null;
    }
  }
  return out;
}

export const RAW_RESPONSE_FILE = "raw-usage-response.json";

/** `userId`, `user-id`, and `user_id` all become `user_id`. */
function keyWords(key: string): string {
  return key
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .replace(/[^A-Za-z0-9]+/g, "_")
    .toLowerCase();
}

function isIdentityKey(key: string): boolean {
  return IDENTITY_KEY.test(keyWords(key)) || SECRET_WORD.test(key);
}

function placeholder(value: string): string {
  return `<redacted string, ${value.length} chars>`;
}

function redactNumber(value: number, identityKey: boolean): number | string {
  const digits = identityKey ? null : rebuild(String(value), NUMBER_CHARS);
  return digits === null ? "<redacted number>" : Number(digits);
}

function redactString(value: string, identityKey: boolean): string {
  if (!identityKey) {
    const kept = DATE.test(value)
      ? rebuild(value, DATE_CHARS)
      : ENUM_WORD.test(value)
        ? rebuild(value, ENUM_CHARS)
        : WINDOW_ID.test(value)
          ? rebuild(value, WINDOW_CHARS)
          : null;
    if (kept !== null) {
      return kept;
    }
  }
  return placeholder(value);
}

function redactScalar(value: unknown, identityKey: boolean): unknown {
  if (value === null) {
    return null;
  }
  if (typeof value === "boolean") {
    return value === true;
  }
  if (typeof value === "number") {
    return redactNumber(value, identityKey);
  }
  if (typeof value === "string") {
    return redactString(value, identityKey);
  }
  return `<${typeof value}>`;
}

/** A quota group or bucket label kept as text, or null when it must be redacted. */
function quotaLabel(value: unknown): string | null {
  return typeof value === "string" && QUOTA_LABEL.test(value) && !value.includes("@") ? rebuild(value, LABEL_CHARS) : null;
}

/**
 * A redacted deep copy of a decoded JSON response. `quotaItem` marks an object that
 * is an element of a `groups` or `buckets` array, whose own labels are kept.
 */
export function redactUsagePayload(value: unknown, identityKey = false, quotaItem = false): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactUsagePayload(item, identityKey));
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    let index = 0;
    for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
      const safeKey = (ID_SHAPED_KEY.test(key) ? null : rebuild(key, KEY_CHARS)) ?? `<key ${index}>`;
      const label = quotaItem && !identityKey && QUOTA_LABEL_KEYS.has(key) ? quotaLabel(child) : null;
      if (label !== null) {
        out[safeKey] = label;
      } else if (Array.isArray(child) && QUOTA_ARRAYS.has(key) && !identityKey) {
        out[safeKey] = child.map((item) => redactUsagePayload(item, false, true));
      } else {
        out[safeKey] = redactUsagePayload(child, identityKey || isIdentityKey(key));
      }
      index += 1;
    }
    return out;
  }
  return redactScalar(value, identityKey);
}

/**
 * Write the redacted response to `<storageDir>/raw-usage-response.json`,
 * replacing any earlier copy, and return the file path. Nothing is sent anywhere.
 */
export function saveRawUsageResponse(storageDir: string, endpoint: string, raw: unknown, now = new Date()): string {
  fs.mkdirSync(storageDir, { recursive: true });
  const file = path.join(storageDir, RAW_RESPONSE_FILE);
  const document = {
    note: "Redacted copy of one usage response, saved by the Save Raw Usage Response command. Strings other than dates and short enum words are replaced.",
    endpoint,
    savedAt: now.toISOString(),
    response: redactUsagePayload(raw),
  };
  fs.writeFileSync(file, `${JSON.stringify(document, null, 2)}\n`, { encoding: "utf8", mode: 0o600 });
  return file;
}
