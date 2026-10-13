import * as fs from "fs";
import * as os from "os";
import * as path from "path";

/**
 * Writes this provider's pay-per-use credit reminder settings to
 * `$NEXUS_HOME/config/credit-reminders-codex.json` (else `~/.nexus-hub/...`), the file
 * the Nexus-Hub usage-guard hook reads (`reminder_settings`). Only this
 * provider's entry is replaced; separate provider files prevent editor hosts
 * from overwriting another provider's settings.
 */
export interface CreditReminderSettings {
  /** Spend between reminders, in the provider's credit unit; 0 turns them off. */
  step: number;
  /** Also remind every `step` when the credit allowance has a fixed limit. */
  when_capped: boolean;
}

export function creditRemindersPath(env: NodeJS.ProcessEnv = process.env, homeDir: string = os.homedir()): string {
  const override = env.NEXUS_HOME?.trim();
  const base = override ? override : path.join(homeDir, ".nexus-hub");
  return path.join(base, "config", "credit-reminders-codex.json");
}

export function normalizeCreditReminders(step: unknown, whenCapped: unknown, fallbackStep: number): CreditReminderSettings {
  const valid = typeof step === "number" && Number.isFinite(step) && step >= 0 && step <= 1_000_000_000;
  return { step: valid ? step : fallbackStep, when_capped: whenCapped === true };
}

/** Merge `settings` into the file under `provider`. Returns false when it could not be written. */
export function writeCreditReminders(
  provider: string,
  settings: CreditReminderSettings,
  filePath: string = creditRemindersPath()
): boolean {
  let data: { providers?: Record<string, unknown> } = {};
  try {
    const parsed: unknown = JSON.parse(fs.readFileSync(filePath, "utf8"));
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      data = parsed as typeof data;
    }
  } catch {
    // A missing or unreadable file is replaced.
  }
  const providers =
    data.providers && typeof data.providers === "object" && !Array.isArray(data.providers) ? data.providers : {};
  const next = { ...data, providers: { ...providers, [provider]: settings } };
  const temp = `${filePath}.${process.pid}.tmp`;
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(temp, JSON.stringify(next, null, 2) + "\n", "utf8");
    fs.renameSync(temp, filePath);
    return true;
  } catch {
    try {
      fs.rmSync(temp, { force: true });
    } catch {
      // Nothing else to clean up.
    }
    return false;
  }
}
