import { spawn } from "node:child_process";

/** Streaming native sessions must never pass through a shell or create a console window. */
export function startNativeStream(executable: string, args: readonly string[], env: NodeJS.ProcessEnv) {
  return spawn(executable, [...args], { env, windowsHide: true, shell: false, stdio: ["pipe", "pipe", "pipe"] });
}
