/**
 * Summarizes an unknown JSON payload as a type skeleton: field names and types,
 * never values.
 *
 * This exists because HO-5 needs the undocumented route's real field names and
 * units in order to correct `CURSOR_WIRE_CONTRACT`, while the auth probe forbids
 * recording account names, identifiers, or usage figures. A skeleton is exactly
 * the intersection: enough to fix the contract, nothing that identifies an account
 * or leaks a number.
 *
 * Two value classes are reported as *units* rather than suppressed, because they
 * are the units the contract has to agree with and neither identifies anyone: an
 * ISO-8601 timestamp shape and a 3-letter currency code.
 */

const MAX_DEPTH = 6;
const MAX_KEYS_PER_OBJECT = 60;

const ISO_TIMESTAMP =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/u;
const CURRENCY_CODE = /^[A-Z]{3}$/u;
const UNIT_WORD = /^(?:tokens?|requests?|percent|cents?|usd|minutes?|seconds?)$/iu;

export function summarizeShape(value: unknown, depth = 0): string {
  if (value === null) {
    return "null";
  }
  if (depth >= MAX_DEPTH) {
    return "...";
  }
  if (Array.isArray(value)) {
    return value.length === 0
      ? "array<empty>"
      : `array<${summarizeShape(value[0], depth + 1)}>[${value.length}]`;
  }
  switch (typeof value) {
    case "string":
      return describeString(value);
    case "number":
      return Number.isInteger(value) ? "integer" : "decimal";
    case "boolean":
      return "boolean";
    case "object":
      return summarizeObject(value as Record<string, unknown>, depth);
    default:
      return typeof value;
  }
}

function summarizeObject(
  record: Record<string, unknown>,
  depth: number
): string {
  const keys = Object.keys(record).sort().slice(0, MAX_KEYS_PER_OBJECT);
  if (keys.length === 0) {
    return "object<empty>";
  }
  const fields = keys.map(
    (key) => `${key}: ${summarizeShape(record[key], depth + 1)}`
  );
  return `{ ${fields.join(", ")} }`;
}

/**
 * Strings are the leak risk: an account name, email, or team id is a string. Only
 * three outcomes are possible, and none of them echoes free-form text.
 */
function describeString(value: string): string {
  if (ISO_TIMESTAMP.test(value)) {
    return "iso-timestamp";
  }
  if (CURRENCY_CODE.test(value)) {
    return "currency-code";
  }
  if (UNIT_WORD.test(value.trim())) {
    // A declared unit is exactly what the wire contract must agree with, and the
    // allowlist is closed, so no arbitrary text can reach the output this way.
    return `unit-word(${value.trim().toLowerCase()})`;
  }
  return "string";
}

/** The field-name paths present in a payload, for diffing against the contract. */
export function shapePaths(value: unknown, prefix = "", depth = 0): string[] {
  if (
    depth >= MAX_DEPTH ||
    typeof value !== "object" ||
    value === null ||
    Array.isArray(value)
  ) {
    return prefix === "" ? [] : [prefix];
  }
  const record = value as Record<string, unknown>;
  const keys = Object.keys(record).sort();
  if (keys.length === 0) {
    return prefix === "" ? [] : [prefix];
  }
  return keys.flatMap((key) =>
    shapePaths(record[key], prefix === "" ? key : `${prefix}.${key}`, depth + 1)
  );
}
