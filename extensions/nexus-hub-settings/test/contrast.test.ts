import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * The panel's text and control colors, computed from `media/panel.css` itself.
 *
 * The stylesheet combines theme colors with the logo's cyan palette. Forced-colors system colors are not modeled here.
 * This test resolves each rule that sets a color against the variable values of four themes (VS Code's
 * Dark Modern and Light Modern as shipped, and the two high-contrast themes as modeled below) and
 * computes the WCAG ratio of every text and control pair. Text needs 4.5:1 and a control's edge or
 * focus ring needs 3:1.
 *
 * What it proves: the stylesheet as written reaches those ratios in these four variable sets.
 * What it does not prove: the real high-contrast themes (their values here are the ones VS Code
 * documents, not read from a running VS Code), or any other theme, which can define any color.
 */

const here = path.dirname(fileURLToPath(import.meta.url));
const CSS = fs.readFileSync(path.join(here, "..", "media", "panel.css"), "utf8").replace(/@media \(forced-colors: active\)\s*\{[\s\S]*?\n\}/g, "");

interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

const THEMES: Record<string, Record<string, string>> = {
  dark: {
    foreground: "#cccccc", "sideBar-background": "#181818", "editor-background": "#1f1f1f", descriptionForeground: "#9d9d9d",
    "button-background": "#0078d4", "button-foreground": "#ffffff", "button-secondaryBackground": "#313131", "button-secondaryForeground": "#cccccc",
    "input-background": "#313131", "input-foreground": "#cccccc", "input-border": "#3c3c3c", focusBorder: "#0078d4",
    "panel-border": "#2b2b2b", "textBlockQuote-background": "#2b2b2b", "textCodeBlock-background": "#2b2b2b", "widget-border": "#313131",
    "editorWarning-foreground": "#cca700", "testing-iconPassed": "#73c991", "textLink-foreground": "#4daafc", "editorError-foreground": "#f85149",
  },
  light: {
    foreground: "#3b3b3b", "sideBar-background": "#f8f8f8", "editor-background": "#ffffff", descriptionForeground: "#717171",
    "button-background": "#005fb8", "button-foreground": "#ffffff", "button-secondaryBackground": "#e5e5e5", "button-secondaryForeground": "#3b3b3b",
    "input-background": "#ffffff", "input-foreground": "#3b3b3b", "input-border": "#cecece", focusBorder: "#005fb8",
    "panel-border": "#e5e5e5", "textBlockQuote-background": "#f8f8f8", "textCodeBlock-background": "#f8f8f8", "widget-border": "#e5e5e5",
    "editorWarning-foreground": "#bf8803", "testing-iconPassed": "#388a34", "textLink-foreground": "#005fb8", "editorError-foreground": "#e51400",
  },
  // Modeled: the documented values of VS Code's high-contrast themes. Neither defines a secondary button color.
  "hc-dark": {
    foreground: "#ffffff", "sideBar-background": "#000000", "editor-background": "#000000", descriptionForeground: "#ffffffb3",
    "button-background": "#000000", "button-foreground": "#ffffff", "button-border": "#6fc3df",
    "input-background": "#000000", "input-foreground": "#ffffff", "input-border": "#6fc3df", focusBorder: "#f38518",
    "panel-border": "#6fc3df", "textBlockQuote-background": "#000000", "textCodeBlock-background": "#000000", "widget-border": "#6fc3df",
    "editorWarning-foreground": "#ffff00", "testing-iconPassed": "#73c991", "textLink-foreground": "#21a6ff", "editorError-foreground": "#f48771",
  },
  "hc-light": {
    foreground: "#292929", "sideBar-background": "#ffffff", "editor-background": "#ffffff", descriptionForeground: "#292929b3",
    "button-background": "#0f4a85", "button-foreground": "#ffffff", "button-border": "#0f4a85",
    "input-background": "#ffffff", "input-foreground": "#292929", "input-border": "#0f4a85", focusBorder: "#006bb3",
    "panel-border": "#0f4a85", "textBlockQuote-background": "#ffffff", "textCodeBlock-background": "#ffffff", "widget-border": "#0f4a85",
    "editorWarning-foreground": "#b5200d", "testing-iconPassed": "#007100", "textLink-foreground": "#0f4a85", "editorError-foreground": "#b5200d",
  },
};

type Declarations = Record<string, string>;

function parseRules(css: string): Map<string, Declarations> {
  const noMedia = css.replace(/\/\*[\s\S]*?\*\//g, "").replace(/@media[^{]*\{[\s\S]*$/, "");
  const rules = new Map<string, Declarations>();
  for (const match of noMedia.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const declarations: Declarations = {};
    for (const part of match[2]!.split(";")) {
      const at = part.indexOf(":");
      if (at > 0) {
        declarations[part.slice(0, at).trim()] = part.slice(at + 1).trim();
      }
    }
    for (const selector of match[1]!.split(",").map((s) => s.trim())) {
      rules.set(selector, { ...(rules.get(selector) ?? {}), ...declarations });
    }
  }
  return rules;
}

const RULES = parseRules(CSS);

function rule(selector: string): Declarations {
  const found = RULES.get(selector);
  if (!found) {
    throw new Error(`panel.css has no rule for ${selector}`);
  }
  return found;
}

/** Split `a, b(c, d), e` at the commas outside any parentheses. */
function splitTop(text: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let current = "";
  for (const char of text) {
    if (char === "(") {
      depth += 1;
    } else if (char === ")") {
      depth -= 1;
    }
    if (char === "," && depth === 0) {
      parts.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  parts.push(current.trim());
  return parts;
}

function inner(text: string, name: string): string {
  return text.slice(name.length + 1, text.lastIndexOf(")"));
}

function resolve(expression: string, theme: Record<string, string>): Rgba {
  const text = expression.trim();
  if (text.startsWith("light-dark(")) {
    const choices = splitTop(inner(text, "light-dark"));
    return resolve(choices[luminance(resolve(theme["editor-background"]!, theme)) > 0.5 ? 0 : 1]!, theme);
  }
  if (text.startsWith("var(")) {
    const [name, ...fallback] = splitTop(inner(text, "var"));
    const key = name!.replace(/^--vscode-/, "");
    if (name!.startsWith("--vscode-") && theme[key] !== undefined) {
      return resolve(theme[key]!, theme);
    }
    if (!name!.startsWith("--vscode-")) {
      const declared = rule(":root")[name!];
      if (declared !== undefined) {
        return resolve(declared, theme);
      }
    }
    if (fallback.length === 0) {
      throw new Error(`${name} is not defined and has no fallback`);
    }
    return resolve(fallback.join(","), theme);
  }
  if (text.startsWith("color-mix(")) {
    const [, first, second] = splitTop(inner(text, "color-mix"));
    const [color, percent] = [first!.replace(/\s+[\d.]+%$/, ""), Number(/([\d.]+)%$/.exec(first!)?.[1])];
    if (second !== "transparent" || Number.isNaN(percent)) {
      throw new Error(`unsupported color-mix: ${text}`);
    }
    const base = resolve(color, theme);
    return { ...base, a: base.a * (percent / 100) };
  }
  if (text === "transparent") {
    return { r: 0, g: 0, b: 0, a: 0 };
  }
  const hex = /^#([0-9a-f]{6})([0-9a-f]{2})?$/i.exec(text);
  if (hex) {
    const n = parseInt(hex[1]!, 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255, a: hex[2] ? parseInt(hex[2], 16) / 255 : 1 };
  }
  throw new Error(`cannot resolve ${text}`);
}

function over(top: Rgba, bottom: Rgba): Rgba {
  const a = top.a + bottom.a * (1 - top.a);
  const mix = (t: number, b: number): number => (a === 0 ? 0 : (t * top.a + b * bottom.a * (1 - top.a)) / a);
  return { r: mix(top.r, bottom.r), g: mix(top.g, bottom.g), b: mix(top.b, bottom.b), a };
}

function luminance(c: Rgba): number {
  const channel = (v: number): number => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
}

function ratio(foreground: Rgba, background: Rgba): number {
  const bg = over(background, { r: 0, g: 0, b: 0, a: 1 });
  const fg = over(foreground, bg);
  const [light, dark] = [luminance(fg), luminance(bg)].sort((x, y) => y - x) as [number, number];
  return (light + 0.05) / (dark + 0.05);
}

function colorOf(selector: string, property: string, theme: Record<string, string>, fallback?: string): Rgba {
  return resolve(rule(selector)[property] ?? fallback ?? "transparent", theme);
}

const NAMES = Object.keys(THEMES);

describe.each(NAMES)("panel.css contrast in %s", (name) => {
  const theme = THEMES[name]!;
  const page = (): Rgba => over(colorOf("body", "background", theme), { r: 0, g: 0, b: 0, a: 1 });
  const body = (): Rgba => colorOf("body", "color", theme);

  it.each([
    ["body text", () => body(), () => page()],
    ["hint text", () => colorOf(".hint", "color", theme), () => page()],
    ["a notice", () => body(), () => over(colorOf(".notice", "background", theme), page())],
    ["a code block", () => body(), () => over(colorOf("pre", "background", theme), page())],
    ["an effort label", () => colorOf(".effort-label", "color", theme), () => page()],
    ["the selected effort label", () => colorOf(".effort-choice[aria-checked='true'] .effort-label", "color", theme), () => page()],
    ["the current effort", () => colorOf(".effort-value", "color", theme), () => page()],
    ["a plain button", () => colorOf("button", "color", theme), () => over(colorOf("button", "background", theme), page())],
  ])("gives %s at least 4.5:1", (_label, foreground, background) => {
    expect(ratio(foreground(), background())).toBeGreaterThanOrEqual(4.5);
  });

  it("gives the effort track edge at least 3:1 against both its fill and the page", () => {
    const edge = resolve(rule(".effort-choices::before").border!.replace(/^1px solid /, ""), theme);
    const fill = over(colorOf(".effort-choices::before", "background", theme), page());
    expect(ratio(edge, fill)).toBeGreaterThanOrEqual(3);
    expect(ratio(edge, page())).toBeGreaterThanOrEqual(3);
  });
  it("distinguishes the selected effort and enabled switch thumbs from the cyan track", () => {
    for (const selector of [".effort-choice[aria-checked='true'] .effort-dot::before", ".switch[aria-checked='true'] .switch-thumb"]) {
      const border = resolve(rule(selector).border!.replace(/^\dpx solid /, ""), theme);
      for (const stop of ["var(--nexus-blue)", "var(--nexus-cyan)"]) {
        expect(ratio(border, resolve(stop, theme))).toBeGreaterThanOrEqual(3);
      }
      expect(ratio(border, colorOf(selector, "background", theme))).toBeGreaterThanOrEqual(3);
    }
  });

  it("gives the focus ring at least 3:1 against the page", () => {
    const ring = resolve(rule("button:focus-visible").outline!.replace(/^2px solid /, ""), theme);
    expect(ratio(ring, page())).toBeGreaterThanOrEqual(3);
  });
});

describe("panel.css structure that the ratios rely on", () => {
  it("keeps settings controls keyboard reachable with visible focus", () => {
    expect(rule("button:focus-visible").outline).toContain("2px solid");
    expect(rule("select:focus-visible").outline).toContain("2px solid");
    expect(rule("button.switch").background).toBe("transparent");
    expect(CSS).not.toMatch(/outline:\s*none/);
  });

  it("measures the ratios it reports", () => {
    expect(ratio(resolve("#000000", {}), resolve("#ffffff", {}))).toBeCloseTo(21, 5);
    expect(ratio(resolve("#bf8803", {}), resolve("#f8f8f8", {}))).toBeLessThan(4.5); // the old warning tone as text: it failed
    expect(ratio(resolve("#388a34", {}), resolve("#f8f8f8", {}))).toBeLessThan(4.5);
  });
});
