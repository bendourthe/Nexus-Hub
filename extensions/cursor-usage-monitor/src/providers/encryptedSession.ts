import { execFile } from "node:child_process";
import { createDecipheriv } from "node:crypto";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";

export const ENCRYPTED_SESSION_PREFIX = "cursor-safe-storage:v1:";

export interface SessionDecryptionDependencies {
  platform?: NodeJS.Platform;
  readLocalState?: (path: string) => Promise<string>;
  unprotect?: (encrypted: Buffer) => Promise<Buffer>;
}

/** Decrypt only Cursor's named session, using its application key on Windows. */
export async function decryptStoredSession(
  value: string,
  statePath: string,
  dependencies: SessionDecryptionDependencies = {}
): Promise<string> {
  let key: Buffer | undefined;
  let plaintext: Buffer | undefined;
  try {
    if ((dependencies.platform ?? process.platform) !== "win32" ||
        !value.startsWith(ENCRYPTED_SESSION_PREFIX)) {
      throw new Error();
    }
    const blob = strictBase64(value.slice(ENCRYPTED_SESSION_PREFIX.length));
    // Chromium v10: version, 12-byte nonce, ciphertext, 16-byte GCM tag.
    if (blob.length <= 31 || blob.subarray(0, 3).toString("ascii") !== "v10") {
      throw new Error();
    }
    const localStatePath = resolve(dirname(statePath), "..", "..", "Local State");
    const text = await (dependencies.readLocalState ??
      ((path: string) => readFile(path, "utf8")))(localStatePath);
    const localState: unknown = JSON.parse(text);
    const protectedKey = readProtectedKey(localState);
    key = await (dependencies.unprotect ?? unprotectWindows)(protectedKey);
    if (key.length !== 32) {
      throw new Error();
    }
    const decipher = createDecipheriv("aes-256-gcm", key, blob.subarray(3, 15));
    decipher.setAuthTag(blob.subarray(-16));
    plaintext = Buffer.concat([decipher.update(blob.subarray(15, -16)), decipher.final()]);
    return plaintext.toString("utf8");
  } catch {
    // Native errors may contain paths or input. None can leave this boundary.
    throw new Error("Cursor session decryption is unavailable.");
  } finally {
    key?.fill(0);
    plaintext?.fill(0);
  }
}

function strictBase64(value: string): Buffer {
  if (value.length === 0 || value.length > 16384 ||
      !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new Error();
  }
  return Buffer.from(value, "base64");
}

function readProtectedKey(value: unknown): Buffer {
  if (typeof value !== "object" || value === null) {
    throw new Error();
  }
  const osCrypt: unknown = (value as Record<string, unknown>).os_crypt;
  if (typeof osCrypt !== "object" || osCrypt === null) {
    throw new Error();
  }
  const encoded: unknown = (osCrypt as Record<string, unknown>).encrypted_key;
  if (typeof encoded !== "string") {
    throw new Error();
  }
  const key = strictBase64(encoded);
  if (key.subarray(0, 5).toString("ascii") !== "DPAPI" || key.length <= 5) {
    throw new Error();
  }
  return key.subarray(5);
}

function unprotectWindows(encrypted: Buffer): Promise<Buffer> {
  // Static script; encrypted bytes travel over stdin, never command-line args.
  const script = "$ErrorActionPreference='Stop'; Add-Type -AssemblyName System.Security; " +
    "$b=[Convert]::FromBase64String([Console]::In.ReadToEnd()); " +
    "$p=[Security.Cryptography.ProtectedData]::Unprotect($b,$null," +
    "[Security.Cryptography.DataProtectionScope]::CurrentUser); " +
    "[Console]::Out.Write([Convert]::ToBase64String($p)); [Array]::Clear($p,0,$p.Length)";
  const executable = resolve(process.env.SystemRoot ?? "C:\\Windows",
    "System32", "WindowsPowerShell", "v1.0", "powershell.exe");
  return new Promise((resolveKey, reject) => {
    const child = execFile(executable, ["-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
      { windowsHide: true, timeout: 10000, maxBuffer: 4096, encoding: "utf8" },
      (error, stdout) => {
        if (error !== null) {
          reject(new Error("Native decryption failed."));
          return;
        }
        try {
          resolveKey(strictBase64(stdout.trim()));
        } catch {
          reject(new Error("Native decryption failed."));
        }
      });
    child.stdin?.on("error", () => reject(new Error("Native decryption failed.")));
    child.stdin?.end(encrypted.toString("base64"));
  });
}
