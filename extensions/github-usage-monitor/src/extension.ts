import * as vscode from "vscode";
import { GitHubTokenStore, type TokenMutationResult } from "./providers/auth";
import { GitHubBillingClient } from "./providers/github";
import { resolveBillingOwner } from "./providers/scope";
import type { BillingOwner, ProviderError } from "./types";

export function activate(context: vscode.ExtensionContext): void {
  const tokens = new GitHubTokenStore(context.secrets);
  const client = new GitHubBillingClient();

  context.subscriptions.push(
    vscode.commands.registerCommand("github-usage.setToken", async () => {
      await promptAndStoreToken("Store GitHub billing token", tokens, client, false);
    }),
    vscode.commands.registerCommand("github-usage.validateToken", async () => {
      const owner = configuredOwner();
      if (owner === null) {
        return;
      }
      const result = await tokens.validateToken((token) => client.validateCredential(owner, token));
      await showMutationResult(result, "Stored GitHub billing token is valid.");
    }),
    vscode.commands.registerCommand("github-usage.rotateToken", async () => {
      await promptAndStoreToken("Rotate GitHub billing token", tokens, client, true);
    }),
    vscode.commands.registerCommand("github-usage.clearToken", async () => {
      await tokens.clearToken();
      await vscode.window.showInformationMessage("GitHub billing token removed from SecretStorage.");
    })
  );
}

export function deactivate(): void {}

async function promptAndStoreToken(
  prompt: string,
  tokens: GitHubTokenStore,
  client: GitHubBillingClient,
  rotate: boolean
): Promise<void> {
  const owner = configuredOwner();
  if (owner === null) {
    return;
  }
  const token = await vscode.window.showInputBox({
    prompt,
    password: true,
    ignoreFocusOut: true,
    placeHolder: "Fine-grained or account-authorized GitHub token"
  });
  if (token === undefined) {
    return;
  }
  const validator = (candidate: string) => client.validateCredential(owner, candidate);
  const result = rotate
    ? await tokens.rotateToken(token, validator)
    : await tokens.setToken(token, validator);
  await showMutationResult(result, rotate ? "GitHub billing token rotated." : "GitHub billing token stored.");
}

function configuredOwner(): BillingOwner | null {
  const config = vscode.workspace.getConfiguration("githubUsage");
  const resolution = resolveBillingOwner(
    config.get<string>("billingScope", "user"),
    config.get<string>("billingOwner", "")
  );
  if (!resolution.ok) {
    void vscode.window.showErrorMessage(resolution.error.message);
    return null;
  }
  return resolution.owner;
}

async function showMutationResult(result: TokenMutationResult, successMessage: string): Promise<void> {
  if (result.ok) {
    await vscode.window.showInformationMessage(successMessage);
  } else {
    await showProviderError(result.error);
  }
}

async function showProviderError(error: ProviderError): Promise<void> {
  await vscode.window.showErrorMessage(error.message);
}
