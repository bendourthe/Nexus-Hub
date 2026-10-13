import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { afterEach, describe, expect, it } from "vitest";
import { creditRemindersPath, normalizeCreditReminders, writeCreditReminders } from "../src/creditReminders";

const dirs: string[] = [];

function tempFile(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "credit-reminders-"));
  dirs.push(dir);
  return path.join(dir, "config", "credit-reminders.json");
}

afterEach(() => {
  for (const dir of dirs.splice(0)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});

describe("creditReminders", () => {
  it("should resolve the file under NEXUS_HOME when it is set", () => {
    expect(creditRemindersPath({ NEXUS_HOME: "/x/home" }, "/u")).toBe(path.join("/x/home", "config", "credit-reminders.json"));
    expect(creditRemindersPath({}, "/u")).toBe(path.join("/u", ".nexus-hub", "config", "credit-reminders.json"));
  });

  it("should fall back to the default step when the value is invalid", () => {
    expect(normalizeCreditReminders(100, true, 50)).toEqual({ step: 100, when_capped: true });
    expect(normalizeCreditReminders(0, false, 50)).toEqual({ step: 0, when_capped: false });
    for (const bad of [-1, Number.NaN, "100", undefined, 2e9]) {
      expect(normalizeCreditReminders(bad, "yes", 50)).toEqual({ step: 50, when_capped: false });
    }
  });

  it("should replace only this provider's entry and keep the others", () => {
    const file = tempFile();
    expect(writeCreditReminders("claude", { step: 25, when_capped: false }, file)).toBe(true);
    expect(writeCreditReminders("codex", { step: 500, when_capped: true }, file)).toBe(true);
    expect(writeCreditReminders("claude", { step: 75, when_capped: true }, file)).toBe(true);
    expect(JSON.parse(fs.readFileSync(file, "utf8"))).toEqual({
      providers: { claude: { step: 75, when_capped: true }, codex: { step: 500, when_capped: true } },
    });
  });

  it("should replace a corrupt file instead of failing", () => {
    const file = tempFile();
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, "{not json", "utf8");
    expect(writeCreditReminders("cursor", { step: 50, when_capped: false }, file)).toBe(true);
    expect(JSON.parse(fs.readFileSync(file, "utf8")).providers.cursor.step).toBe(50);
  });
});
