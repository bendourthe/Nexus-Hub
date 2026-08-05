import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(__dirname, "..");

function sha256(file: string): string {
  return createHash("sha256").update(readFileSync(resolve(root, file))).digest("hex");
}

describe("Cursor brand assets", () => {
  it("ships one normalized currentColor glyph on a square grid", () => {
    const svg = readFileSync(resolve(root, "icons/cursor.svg"), "utf8");

    // The grid SIZE is deliberately not pinned. generate-icon-font.js derives its
    // scale from this viewBox, so any square grid is valid; pinning 20x20 here is
    // what previously locked the artwork to a placeholder.
    const viewBox = svg.match(/viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/u);
    expect(viewBox, "icons/cursor.svg needs a `viewBox=\"0 0 W H\"`").not.toBeNull();
    expect(Number(viewBox![1])).toBe(Number(viewBox![2]));

    expect(svg.match(/<path\b/gu)).toHaveLength(1);
    expect(svg).toContain('fill="currentColor"');
    expect(svg).not.toMatch(/<g\b|<script\b|<image\b|(?:href|src)="https?:/u);
    expect(svg).not.toContain("transform=");
  });

  it("is the real Cursor mark, not a placeholder silhouette", () => {
    const svg = readFileSync(resolve(root, "icons/cursor.svg"), "utf8");
    const d = svg.match(/<path[^>]*\sd="([^"]+)"/u)?.[1] ?? "";

    // The shipped glyph was a bare 6-point hexagon for one release; the status bar
    // rendered a plain polygon instead of the Cursor mark. Guard the exact string
    // so a revert to it fails loudly rather than looking merely "simplified".
    expect(d).not.toContain("M10 1.667 17.083 5.833v8.334L10 18.333l-7.083-4.166V5.833L10 1.667Z");

    // The real mark is a cube outline plus an interior stroke, so it carries a
    // second subpath. A single-subpath silhouette is the placeholder shape.
    const subpaths = d.match(/M/gu) ?? [];
    expect(subpaths.length).toBeGreaterThanOrEqual(2);
  });

  it("scales inside the 1024 em box on the grid it declares", () => {
    // Regression guard for the generator's previously hardcoded 51.2 scale
    // (1024/20). Artwork on a 24-unit grid would have reached x=1126 and been
    // clipped, with no error explaining why the glyph looked wrong.
    const svg = readFileSync(resolve(root, "icons/cursor.svg"), "utf8");
    const width = Number(svg.match(/viewBox="0 0 (\d+(?:\.\d+)?)/u)![1]);
    const d = svg.match(/<path[^>]*\sd="([^"]+)"/u)![1];

    const scale = 1024 / width;
    const coords = (d.match(/-?\d+(?:\.\d+)?/gu) ?? []).map(Number);
    const largest = Math.max(...coords.map(Math.abs));

    expect(largest * scale).toBeLessThanOrEqual(1024);
  });

  it("preserves the audited source artwork", () => {
    expect(sha256("icons/cursor-ai-480.png")).toBe(
      "5706468f30fc4bc45c96f8909b94fa110cc5014d4ddb7e1a3f360d51f75cf459"
    );
    expect(sha256("icons/cursor-ai-48.png")).toBe(
      "2804dc1cd9720988d3e561114d6c3fa39b554aaced40c92af1bc848133699dab"
    );

    const large = readFileSync(resolve(root, "icons/cursor-ai-480.png"));
    const compact = readFileSync(resolve(root, "icons/cursor-ai-48.png"));
    expect([large.readUInt32BE(16), large.readUInt32BE(20), large[25]]).toEqual([480, 480, 6]);
    expect([compact.readUInt32BE(16), compact.readUInt32BE(20), compact[25]]).toEqual([48, 48, 6]);
  });

  it("ships the warning vector and generated Cursor font", () => {
    const warning = readFileSync(resolve(root, "icons/warning.svg"), "utf8");
    expect(warning).toContain('fill="currentColor"');
    expect(warning.match(/<path\b/gu)).toHaveLength(1);

    const font = readFileSync(resolve(root, "fonts/cursor-icons.woff2"));
    expect(statSync(resolve(root, "fonts/cursor-icons.woff2")).size).toBeGreaterThan(100);
    expect(font.subarray(0, 4).toString("ascii")).toBe("wOF2");
  });

  it("ships a transparent 256x256 package icon and registers U+E103", () => {
    const png = readFileSync(resolve(root, "icon.png"));
    expect([png.readUInt32BE(16), png.readUInt32BE(20), png[25]]).toEqual([256, 256, 6]);

    const manifest = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
    expect(manifest.icon).toBe("icon.png");
    expect(manifest.description).toContain("Independent Nexus-Hub monitor");
    expect(manifest.contributes.icons["cursor-icon"].default).toEqual({
      fontPath: "./fonts/cursor-icons.woff2",
      fontCharacter: "\\E103"
    });
  });

  it("records attribution and keeps generators on demand", () => {
    const notices = readFileSync(resolve(root, "THIRD_PARTY_NOTICES.md"), "utf8");
    expect(notices).toContain("https://icons8.com/icon/DiGZkjCzyZXn/cursor-ai");
    expect(notices).toContain("independent Nexus-Hub extension");

    const manifest = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
    const lockfile = JSON.parse(readFileSync(resolve(root, "package-lock.json"), "utf8"));
    for (const dependency of ["sharp", "svgpath", "svg2ttf", "ttf2woff2"]) {
      expect(manifest.devDependencies[dependency]).toBeUndefined();
      expect(manifest.dependencies?.[dependency]).toBeUndefined();
      expect(lockfile.packages[""].devDependencies?.[dependency]).toBeUndefined();
      expect(lockfile.packages[""].dependencies?.[dependency]).toBeUndefined();
    }

    const fontGenerator = readFileSync(resolve(root, "scripts/generate-icon-font.js"), "utf8");
    const packageGenerator = readFileSync(resolve(root, "scripts/generate-package-icon.js"), "utf8");
    expect(fontGenerator).toContain("&#xE103;");
    expect(packageGenerator).toContain('icons", "cursor-ai-480.png');
    expect(packageGenerator).toContain(".resize(256, 256");
  });
});
