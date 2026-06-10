// Sample TypeScript module fixture for the compression accuracy harness.
//
// Read as text and run through the CodeCompressor; never executed. Each
// function/method body is long enough (>= ccr_min_lines) that the compressor
// elides it behind a reversible CCR marker, exercising the code-body round-trip.
// TypeScript uses the BRACE family, which the regex fallback handles even when
// the tree-sitter AST path is unavailable.

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

export interface Config {
  name: string;
  retries: number;
  verbose: boolean;
}

export async function loadConfig(path: string): Promise<Config> {
  const raw = await readFile(resolve(path), "utf-8");
  const parsed = JSON.parse(raw) as Partial<Config>;
  const name = parsed.name ?? "default";
  const retries = parsed.retries ?? 3;
  return { name, retries, verbose: Boolean(parsed.verbose) };
}

export class Service {
  private calls = 0;

  constructor(private readonly config: Config) {}

  process(payload: Record<string, unknown>): Record<string, unknown> {
    this.calls += 1;
    const result = { ...payload };
    result.service = this.config.name;
    result.ok = true;
    return result;
  }
}
