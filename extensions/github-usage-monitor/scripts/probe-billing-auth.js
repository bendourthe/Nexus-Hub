#!/usr/bin/env node
/**
 * HO-6 probe runner for the PAT legs: does this credential class authenticate the
 * enhanced billing endpoint for this billing target?
 *
 * Run from extensions/github-usage-monitor after `npm run compile`. The token comes
 * from the environment so it never reaches your shell history as an argument:
 *
 *   # PowerShell
 *   $env:GITHUB_BILLING_PROBE_TOKEN = "ghp_..."
 *   node scripts/probe-billing-auth.js --level organization --name acme --credential classic-pat
 *
 *   # bash
 *   GITHUB_BILLING_PROBE_TOKEN=ghp_... node scripts/probe-billing-auth.js --level user --name octocat --credential classic-pat
 *
 * RUN THE CLASSIC PAT FIRST. It is the control: without a 200 from it on the same
 * target, a failing result from any other credential class is uninterpretable,
 * because insufficient role, organization OAuth-app restrictions, and SSO
 * authorization all produce the same 403/404 shapes.
 *
 * The VS Code OAuth leg is NOT runnable here: a session can only be obtained inside
 * the editor. Run the PAT legs first, then ask for the in-editor diagnostic.
 *
 * Prints only the sanitized record from `toSanitizedRecord`, whose field set is
 * asserted by test. Never prints the token.
 */

"use strict";

const {
  isProbeAllowed,
  probeWithToken,
  toMarkdownRow,
  toSanitizedRecord
} = require("../out/providers/authProbe.js");

const LEVELS = new Set(["user", "organization", "enterprise"]);
const CREDENTIALS = new Set(["classic-pat", "fine-grained-pat"]);
const TOKEN_VAR = "GITHUB_BILLING_PROBE_TOKEN";

function parseArgs(argv) {
  const args = { level: null, name: null, credential: "classic-pat" };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--level" && value) {
      args.level = value;
      index += 1;
    } else if (flag === "--name" && value) {
      args.name = value;
      index += 1;
    } else if (flag === "--credential" && value) {
      args.credential = value;
      index += 1;
    } else if (flag === "--help" || flag === "-h") {
      args.help = true;
    }
  }
  return args;
}

function usage() {
  console.log(
    [
      "Usage: node scripts/probe-billing-auth.js --level <user|organization|enterprise> --name <owner> [--credential <classic-pat|fine-grained-pat>]",
      "",
      `  Token is read from $${TOKEN_VAR}, never from an argument.`,
      "  Default credential is classic-pat, which is the control. Run it first.",
      "",
      "  enterprise + fine-grained-pat is refused: GitHub's endpoint reference",
      "  explicitly rejects fine-grained PATs and GitHub App tokens at that scope.",
      "",
      "Requires `npm run compile` first."
    ].join("\n")
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return 0;
  }
  if (!LEVELS.has(args.level)) {
    console.error(`--level must be one of: ${[...LEVELS].join(", ")}`);
    return 2;
  }
  if (!args.name) {
    console.error("--name is required (the username, org slug, or enterprise slug)");
    return 2;
  }
  if (!CREDENTIALS.has(args.credential)) {
    console.error(`--credential must be one of: ${[...CREDENTIALS].join(", ")}`);
    return 2;
  }
  if (!isProbeAllowed(args.level, args.credential)) {
    console.error(
      "Refused: enterprise billing usage documentarily rejects fine-grained PATs."
    );
    console.error("Use --credential classic-pat for enterprise scope.");
    return 2;
  }

  const token = process.env[TOKEN_VAR];
  if (!token) {
    console.error(`Set $${TOKEN_VAR} to the token you want to test.`);
    return 2;
  }

  const record = await probeWithToken({
    owner: { scope: args.level, name: args.name },
    token,
    credentialKind: args.credential
  });

  console.log("Sanitized probe record:");
  console.log(JSON.stringify(toSanitizedRecord(record), null, 2));
  console.log("");
  console.log("Paste this row into the results table in");
  console.log("docs/v3/v3.15/development/github-billing-auth-probe.md:");
  console.log("");
  console.log(toMarkdownRow(record));
  console.log("");

  if (record.status === 200) {
    console.log(
      args.credential === "classic-pat"
        ? "CONTROL ESTABLISHED. This target and endpoint work with a classic PAT, so a"
        : "SUPPORTED for this target and endpoint."
    );
    if (args.credential === "classic-pat") {
      console.log(
        "  failing result from another credential class on this same target is now"
      );
      console.log("  interpretable. Run the other classes next.");
    }
  } else if (record.status === 401) {
    console.log(
      "401: the token is invalid, revoked, or expired. This says NOTHING about"
    );
    console.log("  whether this credential CLASS is supported. Fix the token and retry.");
  } else if (record.acceptedOAuthScopes.length > 0) {
    console.log(
      `GitHub reports this operation accepts OAuth scopes: ${record.acceptedOAuthScopes.join(", ")}`
    );
    console.log(
      `  and the presented credential carries: ${record.grantedOAuthScopes.join(", ") || "none"}`
    );
  } else {
    console.log(
      `${record.status}: check the interpretation table in the probe doc before`
    );
    console.log(
      "  recording a verdict. Confirm the role, the owner name, and that enhanced"
    );
    console.log("  billing is enabled for this account first.");
  }
  return record.status === 200 ? 0 : 1;
}

main()
  .then((code) => process.exit(code))
  .catch((error) => {
    // Never print the error object: a thrown fetch error can carry the request,
    // and the request carries the Authorization header.
    console.error(
      `Probe failed: ${error instanceof Error ? error.name : "unknown error"}`
    );
    process.exit(1);
  });
