#!/usr/bin/env node
/**
 * HO-5 probe runner: discover the undocumented Cursor usage route's real field
 * names and units, so `CURSOR_WIRE_CONTRACT` can be corrected from evidence.
 *
 * Run from extensions/cursor-usage-monitor after `npm run compile`:
 *
 *   node scripts/probe-wire-shape.js
 *   node scripts/probe-wire-shape.js --route /api/dashboard/get-current-period-usage
 *   node scripts/probe-wire-shape.js --state-path "D:\\Cursor\\state.vscdb"
 *
 * What it does, and nothing more (the boundary in
 * docs/releases/v3/v3.15/development/cursor-usage-auth-probe.md):
 *   - resolves the platform's documented state-database candidate path
 *   - opens it READ-ONLY and reads ONE allowlisted key
 *   - issues ONE GET to ONE JSON route, never an HTML page
 *   - prints a TYPE SKELETON: field names and types, never values
 *
 * It never prints the session value, never writes a file, and stops on the first
 * failure instead of trying neighbouring routes.
 */

"use strict";

const {
  CursorSessionAdapter,
  DEFAULT_SESSION_KEY
} = require("../out/providers/session.js");
const { resolveCursorStatePath } = require("../out/providers/auth.js");
const {
  CURSOR_USAGE_ORIGIN,
  CURSOR_WIRE_CONTRACT,
  mapWirePayload
} = require("../out/providers/liveTransport.js");
const { summarizeShape, shapePaths } = require("../out/providers/wireShape.js");
const os = require("node:os");

function parseArgs(argv) {
  const args = {
    route: CURSOR_WIRE_CONTRACT.route,
    origin: CURSOR_USAGE_ORIGIN,
    statePath: null,
    method: "GET"
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--origin" && value) {
      // Only an https origin, and only a cursor host: a probe that can be pointed
      // at an arbitrary server is a credential-exfiltration tool.
      const parsed = new URL(value);
      if (parsed.protocol !== "https:" || !/(^|\.)cursor\.(com|sh)$/u.test(parsed.host)) {
        throw new Error(`--origin must be an https cursor.com or cursor.sh host, got ${value}`);
      }
      args.origin = `https://${parsed.host}`;
      index += 1;
    } else if (flag === "--route" && value) {
      args.route = value.startsWith("/") ? value : `/${value}`;
      index += 1;
    } else if (flag === "--state-path" && value) {
      args.statePath = value;
      index += 1;
    } else if (flag === "--method" && value) {
      args.method = value.toUpperCase();
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
      "Usage: node scripts/probe-wire-shape.js [--route <path>] [--state-path <file>]",
      "",
      `  --route       JSON route to try (default ${CURSOR_WIRE_CONTRACT.route})`,
      `  --origin      https cursor host (default ${CURSOR_USAGE_ORIGIN})`,
      "  --state-path  Override the state database location",
      "",
      "Requires `npm run compile` first. Prints field names and types only."
    ].join("\n")
  );
}

function resolveStatePath(override) {
  if (override) {
    return override;
  }
  const options = { home: os.homedir() };
  if (process.env.APPDATA) {
    options.appData = process.env.APPDATA;
  }
  if (process.env.XDG_CONFIG_HOME) {
    options.xdgConfigHome = process.env.XDG_CONFIG_HOME;
  }
  return resolveCursorStatePath(process.platform, options) ?? "";
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return 0;
  }

  const statePath = resolveStatePath(args.statePath);
  console.log("Cursor wire-shape probe");
  console.log(`  node          ${process.version}`);
  console.log(`  platform      ${process.platform}`);
  console.log(`  state path    ${statePath || "(unresolved)"}`);
  console.log(`  allowed key   ${DEFAULT_SESSION_KEY}`);
  console.log(`  route         ${args.origin}${args.route}`);
  console.log("");

  const adapter = new CursorSessionAdapter({ statePath });
  const capability = await adapter.capability();
  if (!capability.available) {
    console.log(`RESULT: capability unavailable (${capability.reason})`);
    if (capability.reason === "sqlite-unavailable") {
      console.log(
        "  This host's Node has no built-in node:sqlite (needs 22.13+). That is WN-5:"
      );
      console.log(
        "  record the Cursor version, because the extension degrades to manual there."
      );
    }
    if (capability.reason === "state-path-missing") {
      console.log("  Pass --state-path if Cursor is installed in a custom location.");
    }
    return 1;
  }
  console.log("capability: available (state database present, node:sqlite loaded)");

  if (args.method !== "GET" && args.method !== "POST") {
    console.log(`RESULT: --method must be GET or POST, got ${args.method}`);
    return 2;
  }
  if (args.method === "POST") {
    // A POST is write-shaped, so it is opt-in rather than the default. The body is
    // an empty object: the probe sends no parameters it has not been told to send,
    // so it cannot express a mutation even by accident.
    console.log("method: POST with an empty JSON body (authorized separately)");
  }

  let status = 0;
  let payload;
  const diagnostics = [];
  const read = await adapter.withSession(async (session) => {
    // The session value is used for exactly one request and is never printed.
    const response = await fetch(`${args.origin}${args.route}`, {
      method: args.method,
      headers: {
        Authorization: `Bearer ${session}`,
        Accept: "application/json",
        ...(args.method === "POST"
          ? { "Content-Type": "application/json" }
          : {})
      },
      ...(args.method === "POST" ? { body: "{}" } : {})
    });
    status = response.status;
    // Diagnostic headers, captured because prose cannot answer what a status means.
    // A conforming 405 MUST carry `Allow` (RFC 9110), which is the only thing that
    // turns "POST is probably the verb" into a fact; `WWW-Authenticate` is what
    // distinguishes a token-audience refusal from a policy refusal on a 401/403.
    for (const name of [
      "allow",
      "www-authenticate",
      "x-request-id",
      "content-type"
    ]) {
      const value = response.headers.get(name);
      if (value !== null) {
        diagnostics.push(`${name}: ${value}`);
      }
    }
    if (!response.ok) {
      return { ok: true, value: null };
    }
    return { ok: true, value: await response.json() };
  });

  if (!read.ok) {
    console.log(`RESULT: session read failed (${read.error.code})`);
    console.log("  No request was made, or the state database had no usable key.");
    return 1;
  }

  console.log(`http status: ${status}`);
  if (diagnostics.length > 0) {
    console.log("response headers:");
    for (const line of diagnostics) {
      console.log(`  ${line}`);
    }
  }
  payload = read.value;
  if (payload === null) {
    console.log("RESULT: the route did not return JSON usage data.");
    console.log(
      status === 401
        ? "  401 means the Cursor session is expired or cleared, OR that this route does not accept a Bearer header."
        : status === 404
          ? "  404 means this route is wrong. Retry with --route /api/dashboard/get-current-period-usage."
          : status === 405
            ? "  405 means the route EXISTS but rejected the verb. Retry once with --method POST (authorize first)."
            : "  Record this status in the probe doc; do not retry in a loop."
    );
    return 1;
  }

  console.log("");
  console.log("SHAPE (names and types only, no values):");
  console.log(`  ${summarizeShape(payload)}`);
  console.log("");
  console.log("PATHS:");
  for (const path of shapePaths(payload)) {
    console.log(`  ${path}`);
  }

  console.log("");
  const mapped = mapWirePayload(payload);
  if (mapped.ok) {
    console.log("CONTRACT: the committed CURSOR_WIRE_CONTRACT already MATCHES.");
    console.log(
      "  Set `verified: true` in the constant and the fixture, and HO-5 closes."
    );
  } else {
    console.log(`CONTRACT: rejected (${mapped.error.code}). This is expected.`);
    console.log(
      "  Map the PATHS above onto CURSOR_WIRE_CONTRACT.fields in"
    );
    console.log(
      "  src/providers/liveTransport.ts, mirror them into"
    );
    console.log(
      "  tests/fixtures/cursor-usage/wire-contract.json, then set verified: true."
    );
    console.log("  A test asserts the constant and the fixture agree.");
  }
  return 0;
}

// `process.exitCode` rather than `process.exit()`: forcing exit while node:sqlite
// and the fetch connection are still tearing down aborts the process with a libuv
// assertion (`!(handle->flags & UV_HANDLE_CLOSING)`), which replaces a usable exit
// code with 0xC0000409 and looks like a crash rather than a 401.
main()
  .then((code) => {
    process.exitCode = code;
  })
  .catch((error) => {
    // Never print the error object: a thrown fetch error can carry a request that
    // carries the Authorization header.
    console.error(
      `Probe failed: ${error instanceof Error ? error.name : "unknown error"}`
    );
    process.exitCode = 1;
  });
