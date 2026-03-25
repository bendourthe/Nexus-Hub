import * as vscode from "vscode";
import { UsageStore } from "./usageStore";
import {
  UsageData,
  AutoSwitchAction,
  AutoSwitchState,
  DEFAULT_AUTO_SWITCH_STATE,
  formatModelName,
} from "./types";

const isOpus = (m: string): boolean => /opus|default/i.test(m);
const isHaiku = (m: string): boolean => /haiku/i.test(m);
const isSonnet = (m: string): boolean => /sonnet/i.test(m);

/** Advisory messages keyed by threshold. */
const EFFORT_ADVICE: Record<number, { withModelSwitch: (to: string) => string; withoutModelSwitch: string }> = {
  50: {
    withModelSwitch: () =>
      "Usage has passed 50% of your current limit. Consider lowering the Effort setting (only if currently set to High or Max) to maximize capacity.",
    withoutModelSwitch:
      "Usage has passed 50% of your current limit. Consider lowering the Effort setting (only if currently set to High or Max) to maximize capacity.",
  },
  75: {
    withModelSwitch: (to: string) =>
      `Usage has passed 75%. Model automatically switched to ${to}. Also consider reducing/maintaining the Effort setting to Medium or Low.`,
    withoutModelSwitch:
      "Usage has passed 75%. Consider reducing/maintaining the Effort setting to Medium or Low.",
  },
  95: {
    withModelSwitch: (to: string) =>
      `Usage has passed 95%. Model automatically switched to ${to}. Consider reducing the Effort setting to Low.`,
    withoutModelSwitch:
      "Usage has passed 95%. Consider reducing/maintaining the Effort setting to Low.",
  },
};

export class AutoSwitcher {
  private _switchInProgress = false;

  constructor(private readonly store: UsageStore) {}

  /** True while the switcher is writing a VS Code setting (to distinguish from user changes). */
  isSwitching(): boolean {
    return this._switchInProgress;
  }

  /**
   * Evaluate current usage against thresholds and apply auto-switch actions.
   * Returns an array of actions taken (for notification purposes).
   */
  async evaluate(data: UsageData): Promise<AutoSwitchAction[]> {
    const config = this.store.getAutoSwitchConfig();
    if (!config.enabled) {
      return [];
    }

    const triggerPercent = Math.max(data.session.percent, data.weeklyAllModels.percent);
    const state = this.store.getAutoSwitchState();
    const actions: AutoSwitchAction[] = [];

    // --- Auto-restore model when usage drops below the Sonnet threshold ---
    if (state.modelAutoSwitched && state.preAutoModel && triggerPercent < config.modelSonnetThreshold) {
      const from = data.currentModel;
      await this.writeModelSetting(state.preAutoModel);
      state.modelAutoSwitched = false;
      const restored = state.preAutoModel;
      state.preAutoModel = null;
      actions.push({
        kind: "model-restored",
        from: formatModelName(from),
        to: formatModelName(restored),
        triggerPercent,
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
    }

    // --- Threshold advisory notifications (one-time per threshold) ---
    const thresholds = [95, 75, 50];
    for (const threshold of thresholds) {
      if (triggerPercent >= threshold && !state.notifiedThresholds.includes(threshold)) {
        state.notifiedThresholds.push(threshold);
        const advice = EFFORT_ADVICE[threshold];
        const message = modelSwitchedTo
          ? advice.withModelSwitch(modelSwitchedTo)
          : advice.withoutModelSwitch;
        actions.push({
          kind: "usage-advisory",
          from: "",
          to: "",
          triggerPercent,
          message,
        });
        // Only emit the highest unnotified threshold
        break;
      }
    }

    await this.store.saveAutoSwitchState(state);
    return actions;
  }

  /**
   * Called when claudeCode.selectedModel changes and _switchInProgress is false,
   * meaning the user changed it manually. Clears auto-switch model state so we
   * respect their choice.
   */
  handleUserModelChange(_newModel: string): void {
    if (this._switchInProgress) {
      return;
    }
    const state = this.store.getAutoSwitchState();
    if (state.modelAutoSwitched) {
      state.modelAutoSwitched = false;
      state.preAutoModel = null;
      this.store.saveAutoSwitchState(state);
    }
  }

  /** Restore model to pre-auto-switch value. */
  async undoModelSwitch(): Promise<void> {
    const state = this.store.getAutoSwitchState();
    if (state.preAutoModel) {
      await this.writeModelSetting(state.preAutoModel);
      state.modelAutoSwitched = false;
      state.preAutoModel = null;
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

    if (triggerPercent >= haikuThreshold && !isHaiku(currentModel)) {
      if (!state.modelAutoSwitched) {
        state.preAutoModel = currentModel;
      }
      await this.writeModelSetting("haiku");
      state.modelAutoSwitched = true;
      state.lastSwitchAt = Date.now();
      actions.push({
        kind: "model-switched",
        from: formatModelName(currentModel),
        to: formatModelName("haiku"),
        triggerPercent,
      });
    } else if (triggerPercent >= sonnetThreshold && isOpus(currentModel)) {
      if (!state.modelAutoSwitched) {
        state.preAutoModel = currentModel;
      }
      await this.writeModelSetting("sonnet");
      state.modelAutoSwitched = true;
      state.lastSwitchAt = Date.now();
      actions.push({
        kind: "model-switched",
        from: formatModelName(currentModel),
        to: formatModelName("sonnet"),
        triggerPercent,
      });
    }

    return actions;
  }

  private async writeModelSetting(model: string): Promise<void> {
    this._switchInProgress = true;
    try {
      await vscode.workspace
        .getConfiguration("claudeCode")
        .update("selectedModel", model, vscode.ConfigurationTarget.Global);
    } finally {
      this._switchInProgress = false;
    }
  }
}
