import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { UsageStore } from "./usageStore";
import {
  UsageData,
  AutoSwitchAction,
  AutoSwitchState,
  formatModelName,
} from "./types";

const CLAUDE_SETTINGS_PATH = path.join(os.homedir(), ".claude", "settings.json");

const isOpus = (m: string): boolean => /opus|default/i.test(m);
const isHaiku = (m: string): boolean => /haiku/i.test(m);

/** Advisory messages keyed by threshold (shown only when no model switch occurs). */
const EFFORT_ADVICE: Record<number, string> = {
  50: "Usage has passed 50% of your current limit. Consider lowering the Effort setting (only if currently set to High or Max) to maximize capacity.",
  75: "Usage has passed 75%. Consider reducing/maintaining the Effort setting to Medium or Low.",
  95: "Usage has passed 95%. Consider reducing/maintaining the Effort setting to Low.",
};

export class AutoSwitcher {
  private _switchInProgress = false;
  private _lastSwitchTimestamp = 0;

  constructor(
    private readonly store: UsageStore,
    private readonly log?: vscode.OutputChannel,
  ) {}

  /**
   * True while the switcher is sending a model command, or within a 2-second
   * grace period after the command completes.
   */
  isSwitching(): boolean {
    return this._switchInProgress || (Date.now() - this._lastSwitchTimestamp < 2000);
  }

  /**
   * Evaluate current usage against thresholds and apply auto-switch actions.
   * Returns an array of actions taken (for notification purposes).
   */
  async evaluate(data: UsageData): Promise<AutoSwitchAction[]> {
    const config = this.store.getAutoSwitchConfig();
    if (!config.enabled) {
      this.log?.appendLine("[AutoSwitch] Skipped: auto-switch disabled");
      return [];
    }

    // Cross-window dedup: if another window evaluated very recently, skip
    const state = this.store.getAutoSwitchState();
    const now = Date.now();
    if (state.lastEvaluatedAt && (now - state.lastEvaluatedAt) < 5000) {
      this.log?.appendLine(
        `[AutoSwitch] Skipped: another window evaluated ${now - state.lastEvaluatedAt}ms ago`,
      );
      return [];
    }
    // Immediately stamp to claim this evaluation window
    state.lastEvaluatedAt = now;
    await this.store.saveAutoSwitchState(state);

    const triggerPercent = Math.max(data.session.percent, data.weeklyAllModels.percent);
    const actions: AutoSwitchAction[] = [];

    this.log?.appendLine(
      `[AutoSwitch] evaluate: triggerPercent=${triggerPercent} (session=${data.session.percent}, weekly=${data.weeklyAllModels.percent}), ` +
      `currentModel="${data.currentModel}", modelAutoSwitched=${state.modelAutoSwitched}, ` +
      `config.model=${config.model}, sonnetThreshold=${config.modelSonnetThreshold}, haikuThreshold=${config.modelHaikuThreshold}`,
    );

    // --- Auto-restore model when usage drops below the Sonnet threshold ---
    if (state.modelAutoSwitched && state.preAutoModel && triggerPercent < config.modelSonnetThreshold) {
      const from = data.currentModel;
      this.log?.appendLine(`[AutoSwitch] Restoring model to "${state.preAutoModel}" (usage ${triggerPercent}% < ${config.modelSonnetThreshold}%)`);
      const count = await this.switchModel(state.preAutoModel);
      state.modelAutoSwitched = false;
      const restored = state.preAutoModel;
      state.preAutoModel = null;
      state.terminalsSwitched = count;
      state.switchedToModel = null;
      actions.push({
        kind: "model-restored",
        from: formatModelName(from),
        to: formatModelName(restored),
        triggerPercent,
        terminalCount: count,
      });
    }

    // --- Clear notification tracking when usage drops below 50% ---
    if (triggerPercent < 50) {
      state.notifiedThresholds = [];
    }

    // --- Model downgrade ---
    let modelSwitchedTo: string | null = null;
    if (config.model) {
      const modelActions = await this.evaluateModel(
        triggerPercent,
        data.currentModel,
        config.modelSonnetThreshold,
        config.modelHaikuThreshold,
        state,
      );
      if (modelActions.length > 0) {
        modelSwitchedTo = modelActions[0].to;
      }
      actions.push(...modelActions);
    } else {
      this.log?.appendLine("[AutoSwitch] Model switching sub-feature disabled (config.model=false)");
    }

    // --- Threshold advisory notifications (one-time per threshold) ---
    // When a model switch already occurred this evaluation, skip the separate
    // advisory notification (the model-switched notification is sufficient).
    // Still record thresholds as notified so they don't fire later.
    const thresholds = [95, 75, 50];
    if (modelSwitchedTo) {
      for (const threshold of thresholds) {
        if (triggerPercent >= threshold && !state.notifiedThresholds.includes(threshold)) {
          state.notifiedThresholds.push(threshold);
        }
      }
    } else {
      for (const threshold of thresholds) {
        if (triggerPercent >= threshold && !state.notifiedThresholds.includes(threshold)) {
          state.notifiedThresholds.push(threshold);
          actions.push({
            kind: "usage-advisory",
            from: "",
            to: "",
            triggerPercent,
            message: EFFORT_ADVICE[threshold],
          });
          // Only emit the highest unnotified threshold
          break;
        }
      }
    }

    await this.store.saveAutoSwitchState(state);
    this.log?.appendLine(`[AutoSwitch] Evaluation complete: ${actions.length} action(s)`);
    return actions;
  }

  /**
   * Called when another VS Code window triggered an auto-switch via the
   * lastSwitchedModel global setting. Sends /model to local terminals.
   */
  applyRemoteSwitch(targetModel: string): void {
    this.log?.appendLine(`[AutoSwitch] Remote switch signal received: target="${targetModel}"`);
    const count = this.sendModelCommandToTerminals(targetModel);
    this.log?.appendLine(`[AutoSwitch] Remote switch applied to ${count} terminal(s)`);
  }

  /**
   * Apply the pending model switch to a single terminal (called when a new
   * Claude Code terminal opens after the switch was triggered).
   */
  applyPendingSwitchToTerminal(terminal: vscode.Terminal): void {
    const state = this.store.getAutoSwitchState();
    if (!state.modelAutoSwitched || !state.switchedToModel) {
      return;
    }
    if (!/claude/i.test(terminal.name)) {
      return;
    }
    this.log?.appendLine(
      `[AutoSwitch] New Claude terminal "${terminal.name}" detected, sending /model ${state.switchedToModel}`,
    );
    terminal.sendText(`/model ${state.switchedToModel}`);
    state.terminalsSwitched = (state.terminalsSwitched ?? 0) + 1;
    this.store.saveAutoSwitchState(state);
  }

  /** Restore model to pre-auto-switch value. */
  async undoModelSwitch(): Promise<void> {
    const state = this.store.getAutoSwitchState();
    if (state.preAutoModel) {
      this.log?.appendLine(`[AutoSwitch] Undo: restoring to "${state.preAutoModel}"`);
      await this.switchModel(state.preAutoModel);
      state.modelAutoSwitched = false;
      state.preAutoModel = null;
      state.switchedToModel = null;
      state.terminalsSwitched = undefined;
      await this.store.saveAutoSwitchState(state);
    }
  }

  /* ---------------------------------------------------------------- */
  /*  Private helpers                                                 */
  /* ---------------------------------------------------------------- */

  private async evaluateModel(
    triggerPercent: number,
    currentModel: string,
    sonnetThreshold: number,
    haikuThreshold: number,
    state: AutoSwitchState,
  ): Promise<AutoSwitchAction[]> {
    const actions: AutoSwitchAction[] = [];

    // Dedup: if we already switched to the target model, don't re-switch.
    // This prevents repeated notifications when the model couldn't be applied
    // (e.g. no Claude Code terminal found) and currentModel still reports the old value.
    if (triggerPercent >= haikuThreshold && !isHaiku(currentModel)) {
      if (state.modelAutoSwitched && state.switchedToModel === "haiku") {
        this.log?.appendLine("[AutoSwitch] Haiku switch already pending, skipping re-switch");
        return actions;
      }
      this.log?.appendLine(`[AutoSwitch] Haiku threshold hit (${triggerPercent}% >= ${haikuThreshold}%), switching to haiku`);
      if (!state.modelAutoSwitched) {
        state.preAutoModel = currentModel;
      }
      const count = await this.switchModel("haiku");
      state.modelAutoSwitched = true;
      state.lastSwitchAt = Date.now();
      state.terminalsSwitched = count;
      state.switchedToModel = "haiku";
      actions.push({
        kind: "model-switched",
        from: formatModelName(currentModel),
        to: formatModelName("haiku"),
        triggerPercent,
        terminalCount: count,
      });
    } else if (triggerPercent >= sonnetThreshold && isOpus(currentModel)) {
      if (state.modelAutoSwitched && state.switchedToModel === "sonnet") {
        this.log?.appendLine("[AutoSwitch] Sonnet switch already pending, skipping re-switch");
        return actions;
      }
      this.log?.appendLine(`[AutoSwitch] Sonnet threshold hit (${triggerPercent}% >= ${sonnetThreshold}%), switching to sonnet`);
      if (!state.modelAutoSwitched) {
        state.preAutoModel = currentModel;
      }
      const count = await this.switchModel("sonnet");
      state.modelAutoSwitched = true;
      state.lastSwitchAt = Date.now();
      state.terminalsSwitched = count;
      state.switchedToModel = "sonnet";
      actions.push({
        kind: "model-switched",
        from: formatModelName(currentModel),
        to: formatModelName("sonnet"),
        triggerPercent,
        terminalCount: count,
      });
    } else {
      this.log?.appendLine(
        `[AutoSwitch] No model switch needed: triggerPercent=${triggerPercent}, ` +
        `haikuThreshold=${haikuThreshold}, sonnetThreshold=${sonnetThreshold}, ` +
        `isOpus(${currentModel})=${isOpus(currentModel)}, isHaiku(${currentModel})=${isHaiku(currentModel)}`,
      );
    }

    return actions;
  }

  /**
   * Switch Claude Code's model via three mechanisms:
   * 1. Write to ~/.claude/settings.json (Claude Code's own config file)
   * 2. Signal other VS Code windows via the lastSwitchedModel global setting
   * 3. Send /model to any open Claude Code terminals
   * Returns the number of terminals that received the command.
   */
  private async switchModel(model: string): Promise<number> {
    this._switchInProgress = true;
    try {
      // Primary: write to Claude Code's settings.json (same mechanism as its UI)
      this.writeClaudeSettingsModel(model);

      // Signal other VS Code windows via global setting
      await vscode.workspace
        .getConfiguration("claudeUsage.autoSwitch")
        .update("lastSwitchedModel", model, vscode.ConfigurationTarget.Global);

      // Best-effort: send /model to any open Claude Code terminals
      const count = this.sendModelCommandToTerminals(model);
      this.log?.appendLine(
        `[AutoSwitch] Switch complete: settings.json updated, ${count} terminal(s) notified`,
      );

      return count;
    } catch (err) {
      this.log?.appendLine(`[AutoSwitch] switchModel failed: ${err}`);
      throw err;
    } finally {
      this._lastSwitchTimestamp = Date.now();
      this._switchInProgress = false;
    }
  }

  /**
   * Write the model key to ~/.claude/settings.json.
   * Claude Code reads this file on conversation start. "default" deletes the key.
   */
  private writeClaudeSettingsModel(model: string): void {
    try {
      let settings: Record<string, unknown> = {};
      try {
        const raw = fs.readFileSync(CLAUDE_SETTINGS_PATH, "utf-8");
        settings = JSON.parse(raw);
      } catch {
        // File doesn't exist or is invalid; start fresh
      }

      if (model === "default") {
        delete settings.model;
      } else {
        settings.model = model;
      }

      fs.mkdirSync(path.dirname(CLAUDE_SETTINGS_PATH), { recursive: true });
      fs.writeFileSync(CLAUDE_SETTINGS_PATH, JSON.stringify(settings, null, 2) + "\n", "utf-8");
      this.log?.appendLine(`[AutoSwitch] Wrote model="${model}" to ${CLAUDE_SETTINGS_PATH}`);
    } catch (err) {
      this.log?.appendLine(`[AutoSwitch] Failed to write settings.json: ${err}`);
    }
  }

  /**
   * Find all Claude Code terminals in this window and send /model <name>.
   * Returns the number of terminals that received the command.
   */
  private sendModelCommandToTerminals(model: string): number {
    const claudeTerminals = vscode.window.terminals.filter((t) =>
      /claude/i.test(t.name),
    );
    for (const terminal of claudeTerminals) {
      terminal.sendText(`/model ${model}`);
    }
    return claudeTerminals.length;
  }
}
