import { spawnSync } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mapCopilotUser } from "../src/providers/copilot";
import { mapOrganizationUsage } from "../src/providers/copilotOrganization";
import { __resetLog } from "../src/log";
import type { UsageData } from "../src/types";
import { UsageController } from "../src/usageController";
import { UsageService } from "../src/usageService";
import { buildUsageState, removeUsageState, usageStatePath, writeUsageState } from "../src/usageStateFile";
import { UsageStore } from "../src/usageStore";
import { createMemento, fixture } from "./helpers";
import { __resetStubState, __setStubConfig, outputLines } from "./vscode-stub";

const FETCHED = Date.UTC(2026, 9, 2, 0, 5, 30);
const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");
const PROBE = path.join(REPO_ROOT, "catalog", "hooks", "_usage_probe.py");

const personal = (): UsageData => ({
  personal: mapCopilotUser(fixture("copilot-internal-user.personal.json"))!,
  lastUpdated: FETCHED,
  dataSource: "api",
});
const member = (): UsageData => ({
  personal: mapCopilotUser(fixture("copilot-internal-user.business-member.json"))!,
  lastUpdated: FETCHED,
  dataSource: "api",
});
const pool = (usage: string, billing = "copilot-billing.json"): UsageData => ({
  ...member(),
  organization: mapOrganizationUsage(fixture(billing), fixture(usage), FETCHED)!,
});

/** Every fixture state with the state file it must produce (null = no file). */
const STATES: Array<[string, () => UsageData, { percent: number; source: string; approximate: boolean } | null]> = [
  ["personal Copilot Free", personal, { percent: 0, source: "personal", approximate: false }],
  ["Business member without billing access", member, null],
  ["organization pool, captured 0.907 of 13,300", () => pool("ai-credit-usage.json"), { percent: 0.01, source: "organization", approximate: false }],
  ["organization pool near the limit", () => pool("ai-credit-usage.near-limit.synthetic.json"), { percent: 99.25, source: "organization", approximate: false }],
  ["organization pool exhausted", () => pool("ai-credit-usage.over-pool.synthetic.json"), { percent: 100, source: "organization", approximate: false }],
  ["organization pool, seat added this cycle", () => pool("ai-credit-usage.json", "copilot-billing.seat-added.synthetic.json"), { percent: 0.01, source: "organization", approximate: true }],
];

let dir: string;

beforeEach(() => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), "copilot-state-"));
});

afterEach(() => {
  fs.rmSync(dir, { recursive: true, force: true });
  __resetLog();
  __resetStubState();
});

describe("buildUsageState (decision item 6 schema)", () => {
  it.each(STATES)("%s", (_name, make, expected) => {
    const state = buildUsageState(make());
    if (expected === null) {
      expect(state).toBeNull();
      return;
    }
    expect(state).toEqual({
      schema_version: 1,
      provider: "copilot",
      fetched_at: "2026-10-02T00:05:30Z",
      approximate: expected.approximate,
      windows: [
        { name: "monthly", percent: expected.percent, resets_at: "2026-11-01T00:00:00Z", source: expected.source },
      ],
    });
  });

  it("carries a null reset when GitHub gave none, and nothing for missing data", () => {
    const data = personal();
    data.personal!.resetsAt = null;
    expect(buildUsageState(data)!.windows[0].resets_at).toBeNull();
    expect(buildUsageState(undefined)).toBeNull();
  });

  it("holds only the schema keys", () => {
    for (const [, make] of STATES) {
      const state = buildUsageState(make());
      if (!state) continue;
      expect(Object.keys(state).sort()).toEqual(["approximate", "fetched_at", "provider", "schema_version", "windows"]);
      expect(Object.keys(state.windows[0]).sort()).toEqual(["name", "percent", "resets_at", "source"]);
    }
  });
});

describe("usageStatePath", () => {
  it("follows NEXUS_HOME like the probe, else ~/.nexus-hub", () => {
    expect(usageStatePath({ NEXUS_HOME: "/custom/home" }, "/u")).toBe(path.join("/custom/home", "state", "usage-probe", "copilot.json"));
    expect(usageStatePath({ NEXUS_HOME: "  " }, "/u")).toBe(path.join("/u", ".nexus-hub", "state", "usage-probe", "copilot.json"));
    expect(usageStatePath({}, "/u")).toBe(path.join("/u", ".nexus-hub", "state", "usage-probe", "copilot.json"));
  });
});

describe("writeUsageState", () => {
  it("creates the directory and writes the file atomically, leaving no temporary sibling", () => {
    const file = path.join(dir, "state", "usage-probe", "copilot.json");
    expect(writeUsageState(pool("ai-credit-usage.near-limit.synthetic.json"), file)).toBe("written");
    expect(JSON.parse(fs.readFileSync(file, "utf-8")).windows[0].percent).toBe(99.25);
    expect(fs.readdirSync(path.dirname(file))).toEqual(["copilot.json"]);
  });

  it("never exposes a partial file to a reader while writes repeat", () => {
    const file = path.join(dir, "copilot.json");
    writeUsageState(personal(), file);
    const states = [personal(), pool("ai-credit-usage.json"), pool("ai-credit-usage.near-limit.synthetic.json")];
    for (let i = 0; i < 60; i++) {
      writeUsageState(states[i % states.length], file);
      const parsed = JSON.parse(fs.readFileSync(file, "utf-8"));
      expect(parsed.provider).toBe("copilot");
    }
    expect(fs.readdirSync(dir)).toEqual(["copilot.json"]);
  });

  it("removes an earlier file instead of writing one for the member state", () => {
    const file = path.join(dir, "copilot.json");
    writeUsageState(personal(), file);
    expect(fs.existsSync(file)).toBe(true);
    expect(writeUsageState(member(), file)).toBe("removed");
    expect(fs.existsSync(file)).toBe(false);
    expect(writeUsageState(member(), file)).toBe("removed");
  });

  it("logs once and does not throw when the location is not writable", () => {
    const blocker = path.join(dir, "not-a-directory");
    fs.writeFileSync(blocker, "x");
    const file = path.join(blocker, "copilot.json");
    expect(writeUsageState(personal(), file)).toBe("failed");
    expect(writeUsageState(personal(), file)).toBe("failed");
    expect(outputLines).toHaveLength(1);
    expect(outputLines[0]).toContain("Could not write the Copilot usage state file");
    expect(fs.readdirSync(dir)).toEqual(["not-a-directory"]);
  });

  it("removeUsageState tolerates a missing file and logs once on failure", () => {
    removeUsageState(path.join(dir, "absent.json"));
    const nonEmptyDir = path.join(dir, "busy");
    fs.mkdirSync(path.join(nonEmptyDir, "child"), { recursive: true });
    removeUsageState(nonEmptyDir);
    removeUsageState(nonEmptyDir);
    expect(outputLines).toHaveLength(1);
  });
});

describe("UsageController and the state file", () => {
  function controllerFor(results: UsageData[], file: string) {
    const store = new UsageStore(createMemento());
    let call = 0;
    const service = { fetchAll: async () => ({ success: true as const, data: results[Math.min(call++, results.length - 1)], rateLimited: false }) };
    const surface = { refresh: () => {}, setLastError: () => {}, applyBackoff: () => {}, resetBackoff: () => {} };
    return { store, controller: new UsageController(store, service as unknown as UsageService, surface, file) };
  }

  it("writes after each successful fetch with the status bar's precedence", async () => {
    const file = path.join(dir, "copilot.json");
    const { controller } = controllerFor([pool("ai-credit-usage.near-limit.synthetic.json")], file);
    await controller.refresh(FETCHED);
    expect(JSON.parse(fs.readFileSync(file, "utf-8")).windows[0]).toMatchObject({ source: "organization", percent: 99.25 });
  });

  it("writes nothing when copilotUsage.writeUsageState is false, and removes the file when it is turned off", async () => {
    const file = path.join(dir, "copilot.json");
    __setStubConfig("copilotUsage", "writeUsageState", false);
    const { controller } = controllerFor([personal()], file);
    await controller.refresh(FETCHED);
    expect(fs.existsSync(file)).toBe(false);
    fs.writeFileSync(file, "{}");
    controller.stateWritingDisabled();
    expect(fs.existsSync(file)).toBe(false);
  });

  it("rewrites from the personal figure after a disconnect, and deletes the file when none remains", async () => {
    const file = path.join(dir, "copilot.json");
    const withPersonal = { ...pool("ai-credit-usage.near-limit.synthetic.json"), personal: personal().personal };
    const { controller, store } = controllerFor([withPersonal], file);
    await controller.refresh(FETCHED);
    expect(JSON.parse(fs.readFileSync(file, "utf-8")).windows[0].source).toBe("organization");

    await controller.organizationRemoved();
    expect(store.get()!.organization).toBeUndefined();
    expect(JSON.parse(fs.readFileSync(file, "utf-8")).windows[0]).toMatchObject({ source: "personal", percent: 0 });

    await controller.clear();
    expect(fs.existsSync(file)).toBe(false);
    expect(store.get()).toBeUndefined();
    await controller.organizationRemoved();
    expect(fs.existsSync(file)).toBe(false);
  });

  it("removes the file after a disconnect when only a member figure remains", async () => {
    const file = path.join(dir, "copilot.json");
    const { controller } = controllerFor([pool("ai-credit-usage.json")], file);
    await controller.refresh(FETCHED);
    expect(fs.existsSync(file)).toBe(true);
    await controller.organizationRemoved();
    expect(fs.existsSync(file)).toBe(false);
  });
});

/**
 * Cross-check against the reader the usage guard actually uses: for each
 * fixture state, the file this code path writes must parse through
 * `catalog/hooks/_usage_probe.py` `read_copilot`, and the member state must
 * read as "missing". Python is required on every host that runs this suite
 * (the repository's own gate already needs it).
 */
describe("read_copilot cross-check", () => {
  const python = ["python3", "python"].find((cmd) => spawnSync(cmd, ["--version"]).status === 0);

  it("finds a Python interpreter and the probe", () => {
    expect(python, "python3 or python must be on PATH for the probe cross-check").toBeDefined();
    expect(fs.existsSync(PROBE)).toBe(true);
  });

  it.each(STATES)("%s parses through read_copilot", (_name, make, expected) => {
    const home = path.join(dir, "nexus-home");
    const data = { ...make(), lastUpdated: Date.now() };
    writeUsageState(data, usageStatePath({ NEXUS_HOME: home }));
    const run = spawnSync(python!, [PROBE, "--platform", "copilot", "--json"], {
      env: { ...process.env, NEXUS_HOME: home, NEXUS_USAGE_PROBE_DISABLED: "", NEXUS_USAGE_PROBE_PROVIDERS: "copilot" },
      encoding: "utf-8",
    });
    expect(run.status, run.stderr).toBe(0);
    const result = JSON.parse(run.stdout);
    const copilot = Array.isArray(result) ? result.find((r: { platform: string }) => r.platform === "copilot") : result;
    if (expected === null) {
      expect(copilot.status).toBe("unavailable");
      expect(copilot.reason).toContain("state file missing");
      return;
    }
    expect(copilot.status).toBe("ok");
    expect(copilot.windows).toHaveLength(1);
    expect(copilot.windows[0]).toMatchObject({ name: "monthly", percent: expected.percent, source: expected.source });
    expect(copilot.windows[0].resets_at).toBe("2026-11-01T00:00:00Z");
  });
});
