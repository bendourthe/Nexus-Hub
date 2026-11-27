import { execFile } from "node:child_process";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import type { Interpreter } from "./cliBridge";

const TOMLKIT = "0.15.1";
const preparing = new Map<string, Promise<void>>();
export const settingsRuntimePath = (root: string): string => path.join(root, "python-runtime", `tomlkit-${TOMLKIT}`);
export function runtimeEnvironment(env: NodeJS.ProcessEnv, directory: string): NodeJS.ProcessEnv {
  return {...env, PYTHONPATH: [directory, env.PYTHONPATH].filter(Boolean).join(path.delimiter)};
}
function run(interpreter: Interpreter, args: string[], env: NodeJS.ProcessEnv): Promise<void> {
  return new Promise((resolve, reject) => {
    execFile(interpreter.command, [...interpreter.args, ...args], {env, windowsHide: true, shell: false, timeout: 60_000, maxBuffer: 1024 * 1024, encoding: "utf8"}, error => {
      if (error) { reject(new Error("Required TOML support could not be prepared with the selected Python interpreter.")); }
      else { resolve(); }
    });
  });
}
async function prepare(root: string, interpreter: Interpreter, env: NodeJS.ProcessEnv): Promise<void> {
  const destination = settingsRuntimePath(root);
  const probe = (directory: string): Promise<void> => run(interpreter, ["-c", `import tomlkit; assert tomlkit.__version__ == '${TOMLKIT}'`], runtimeEnvironment(env, directory));
  try {
    await fs.lstat(destination);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") { throw error; }
    await fs.mkdir(path.dirname(destination), {recursive: true});
    const staging = await fs.mkdtemp(path.join(path.dirname(destination), ".tomlkit-install-"));
    try {
      await run(interpreter, ["-m", "pip", "--isolated", "install", "--quiet", "--disable-pip-version-check", "--no-input", "--no-deps", "--only-binary=:all:", "--target", staging, `tomlkit==${TOMLKIT}`], env);
      await probe(staging);
      try { await fs.rename(staging, destination); }
      catch (renameError) {
        if (!["EEXIST", "ENOTEMPTY", "EPERM"].includes((renameError as NodeJS.ErrnoException).code ?? "")) { throw renameError; }
        await probe(destination);
      }
    } finally { await fs.rm(staging, {recursive: true, force: true}); }
    return;
  }
  // Never replace an existing private runtime or follow a redirected package directory.
  if ((await fs.lstat(destination)).isSymbolicLink()) { throw new Error("The existing TOML support directory is redirected and was preserved."); }
  await probe(destination);
}

/** Called only after an explicit effort write reports the exact missing TOML dependency. */
export function ensureSettingsRuntime(root: string, interpreter: Interpreter, env: NodeJS.ProcessEnv): Promise<void> {
  const pending = preparing.get(root);
  if (pending) { return pending; }
  const work = prepare(root, interpreter, env);
  preparing.set(root, work);
  void work.then(() => preparing.delete(root), () => preparing.delete(root));
  return work;
}
