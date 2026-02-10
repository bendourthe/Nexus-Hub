import * as vscode from "vscode";
import { UsageData, ClaudeModel, MODEL_DISPLAY_NAMES } from "./types";

export async function collectUsageData(
  currentModel: ClaudeModel
): Promise<UsageData | undefined> {
  // Step 1: Session usage %
  const sessionInput = await vscode.window.showInputBox({
    title: "Claude Usage: Session (Step 1/4)",
    prompt: "Enter your current session usage percentage (from claude.ai/settings/usage)",
    placeHolder: "e.g. 92",
    validateInput: validatePercent,
  });

  if (sessionInput === undefined) {
    return undefined;
  }

  // Step 2: Weekly all-models %
  const weeklyInput = await vscode.window.showInputBox({
    title: "Claude Usage: Weekly All Models (Step 2/4)",
    prompt: "Enter your weekly all-models usage percentage",
    placeHolder: "e.g. 11",
    validateInput: validatePercent,
  });

  if (weeklyInput === undefined) {
    return undefined;
  }

  // Step 3: Weekly Sonnet-only %
  const sonnetInput = await vscode.window.showInputBox({
    title: "Claude Usage: Weekly Sonnet Only (Step 3/4)",
    prompt: "Enter your weekly Sonnet-only usage percentage",
    placeHolder: "e.g. 0",
    validateInput: validatePercent,
  });

  if (sonnetInput === undefined) {
    return undefined;
  }

  // Step 4: Current model
  const modelItems: vscode.QuickPickItem[] = (
    Object.entries(MODEL_DISPLAY_NAMES) as [ClaudeModel, string][]
  ).map(([value, label]) => ({
    label,
    description: value === currentModel ? "(current)" : undefined,
    detail: getModelDescription(value),
  }));

  const selectedModel = await vscode.window.showQuickPick(modelItems, {
    title: "Claude Usage: Current Model (Step 4/4)",
    placeHolder: "Which model are you currently using?",
  });

  if (!selectedModel) {
    return undefined;
  }

  const modelKey = (
    Object.entries(MODEL_DISPLAY_NAMES) as [ClaudeModel, string][]
  ).find(([, label]) => label === selectedModel.label)?.[0] ?? currentModel;

  return {
    session: {
      percent: parseFloat(sessionInput),
      resetsIn: "a few minutes",
    },
    weeklyAllModels: {
      percent: parseFloat(weeklyInput),
      resetsIn: "end of week",
    },
    weeklySonnet: {
      percent: parseFloat(sonnetInput),
      resetsIn: "end of week",
    },
    currentModel: modelKey,
    lastUpdated: Date.now(),
    dataSource: "manual",
  };
}

export async function collectResetTimers(
  data: UsageData
): Promise<UsageData | undefined> {
  const sessionReset = await vscode.window.showInputBox({
    title: "Session Reset Timer (optional)",
    prompt: "When does your session reset? Press Enter to skip.",
    placeHolder: "e.g. 3 min",
    value: data.session.resetsIn,
  });

  if (sessionReset === undefined) {
    return undefined;
  }

  const weeklyReset = await vscode.window.showInputBox({
    title: "Weekly Reset Timer (optional)",
    prompt: "When do your weekly limits reset? Press Enter to skip.",
    placeHolder: "e.g. Fri 1:59 PM",
    value: data.weeklyAllModels.resetsIn,
  });

  if (weeklyReset === undefined) {
    return undefined;
  }

  const sonnetReset = await vscode.window.showInputBox({
    title: "Sonnet Reset Timer (optional)",
    prompt: "When does the Sonnet-only limit reset? Press Enter to skip.",
    placeHolder: "e.g. Mon 10:59 AM",
    value: data.weeklySonnet.resetsIn,
  });

  if (sonnetReset === undefined) {
    return undefined;
  }

  return {
    ...data,
    session: { ...data.session, resetsIn: sessionReset || data.session.resetsIn },
    weeklyAllModels: { ...data.weeklyAllModels, resetsIn: weeklyReset || data.weeklyAllModels.resetsIn },
    weeklySonnet: { ...data.weeklySonnet, resetsIn: sonnetReset || data.weeklySonnet.resetsIn },
  };
}

function validatePercent(value: string): string | undefined {
  const num = parseFloat(value);
  if (isNaN(num)) {
    return "Please enter a number";
  }
  if (num < 0 || num > 100) {
    return "Percentage must be between 0 and 100";
  }
  return undefined;
}

function getModelDescription(model: ClaudeModel): string {
  switch (model) {
    case "opus-4.6":
      return "Best for architecture, complex reasoning, multi-file refactors";
    case "sonnet-4.5":
      return "Best for standard coding, debugging, refactoring, test writing";
    case "haiku-4.5":
      return "Best for simple lookups, formatting, small edits, explanations";
  }
}
