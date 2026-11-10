import * as fs from "node:fs";
import type { FileHandle } from "node:fs/promises";

export interface SafeReadOptions {
  maxBytes: number;
  /** Refuse a symbolic link at the final path component. */
  refuseSymlink?: boolean;
  /** Message used for every refusal (not a regular file, a link, or too large). */
  refusal: string;
}

/**
 * Reads a small regular file through one open handle, so the type and size checks apply to the bytes
 * that are read and cannot race a swap of the path. A missing file still fails with the native ENOENT.
 */
export function readRegularFileSync(file: string, options: SafeReadOptions): string {
  const noFollow = options.refuseSymlink ? fs.constants.O_NOFOLLOW || 0 : 0;
  let fd: number;
  try { fd = fs.openSync(file, fs.constants.O_RDONLY | noFollow | (fs.constants.O_NONBLOCK || 0)); }
  catch (error) { throw (error as NodeJS.ErrnoException).code === "ELOOP" ? new Error(options.refusal) : error; }
  try {
    const stat = fs.fstatSync(fd);
    if (!stat.isFile() || stat.size > options.maxBytes) { throw new Error(options.refusal); }
    // Windows has no O_NOFOLLOW: a link is refused by asking for its target after the open.
    if (options.refuseSymlink && !noFollow) {
      let link = false;
      try { fs.readlinkSync(file); link = true; } catch { /* Not a link. */ }
      if (link) { throw new Error(options.refusal); }
    }
    const text = fs.readFileSync(fd, "utf8");
    if (Buffer.byteLength(text) > options.maxBytes) { throw new Error(options.refusal); }
    return text;
  } finally { fs.closeSync(fd); }
}

/** Async counterpart that follows links, for callers that only bound the size of a regular file. */
export async function readBoundedFile(file: string, maxBytes: number, refusal: string): Promise<string> {
  const { open } = fs.promises;
  const handle: FileHandle = await open(file, "r");
  try {
    if ((await handle.stat()).size > maxBytes) { throw new Error(refusal); }
    return await handle.readFile("utf8");
  } finally { await handle.close(); }
}
