import { createRequire } from "node:module";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const require_ = createRequire(__filename);
const { collectErrors, REQUIRED } = require_(
  resolve(__dirname, "../scripts/verify-package-contents.js")
) as {
  collectErrors: (files: string[]) => string[];
  REQUIRED: string[];
};

// A plausible clean package: every required runtime asset plus ordinary output.
const CLEAN = [...REQUIRED, "out/providers/github.js", "THIRD_PARTY_NOTICES.md"];

describe("VSIX content verification", () => {
  it("accepts a package carrying every runtime asset", () => {
    expect(collectErrors(CLEAN)).toEqual([]);
  });

  it("names the missing asset rather than failing generically", () => {
    const withoutFont = CLEAN.filter((file) => file !== "fonts/github-icons.woff2");
    expect(collectErrors(withoutFont)).toEqual([
      "missing required packaged file: fonts/github-icons.woff2"
    ]);
  });

  it.each([
    "coverage/index.html",
    "src/extension.ts",
    "test/ui.test.ts",
    "scripts/generate-icon-font.js",
    "node_modules/vitest/package.json",
    "github-usage-monitor-0.1.0.vsix",
    "out/extension.js.map"
  ])("rejects the build-time artifact %s", (artifact) => {
    expect(collectErrors([...CLEAN, artifact])).toHaveLength(1);
  });

  it.each([".env", "config/.env.local", "auth.json", "deploy.pem", "signing.key", "secrets.json"])(
    "rejects the credential-shaped file %s",
    (credential) => {
      expect(collectErrors([...CLEAN, credential])).toHaveLength(1);
    }
  );
});
