---
name: generative-art
description: "Produce algorithmic / generative-art artifacts (p5.js sketches, HTML viewers, deterministic image exports) through a two-step Algorithmic Philosophy + Generator-and-Viewer process. Use whenever the user asks for generative art, an algorithmic sketch, a p5.js visual, a flow field, a particle system, an L-system, a procedural pattern, a creative-coding piece, an interactive visualization, a generative wallpaper, a code-driven aesthetic experiment, or \"make me an art piece in code\", even if they don't explicitly say \"generative art\". The skill ALWAYS produces a Markdown philosophy manifesto first and a parameter-driven sketch second; never one without the other. SKIP: data dashboards (use ui-component-generation), static posters / .pdf print-output (use creative-generation Static Poster workflow), 3D shader work (use glsl-shader-development), one-off chart rendering, or any visual where the output is fixed rather than parameter-driven."
summary_l0: "Produce p5.js generative art with a philosophy manifesto, parameter-driven sketch, and HTML viewer"
overview_l1: "This skill produces generative-art artifacts through a strict two-step process. Step 1 - Algorithmic Philosophy is a Markdown manifesto that fixes the aesthetic movement, the underlying principle (flow, repetition, decay, emergence, tension), the color and density behavior, and 1-2 reference movements (suprematism, op-art, Vera Molnar, Casey Reas, James Paterson). Step 2 - Generator + Viewer ships a p5.js sketch with seeded randomness and exposes the parameters that drive its aesthetic via an HTML viewer with sliders. Default templates cover three foundational families: flow fields (vector-field traced particles), particle systems (force-directed swarms with optional noise perturbation), and L-systems (recursive grammar-driven branching). Outputs are deterministic given a fixed seed, so re-running the same sketch produces the same image. Trigger phrases: generative art, p5.js, creative coding, algorithmic art, flow field, particle system, L-system, procedural pattern, generative wallpaper, parametric sketch, seeded randomness, code-driven art, generative design."
---

# Generative Art

Structured guidance for producing algorithmic / generative-art artifacts. The skill enforces a two-step process - first a written philosophy manifesto, then a parameter-driven p5.js generator and HTML viewer - because generative output that skips the philosophy step collapses to perlin-noise clichés (washy gradient particles, generic ribbon-flow). The manifesto is the artistic constraint that distinguishes the artifact from the default.

## When to Use This Skill

Use this skill for:

- p5.js sketches, creative-coding pieces, algorithmic-art experiments
- Flow fields, particle systems, L-systems, reaction-diffusion patterns, cellular automata visuals
- Generative wallpapers, parametric posters, code-driven loop animations
- Interactive visualizations where parameters drive aesthetic outcomes
- Seeded-randomness work where a deterministic image must reproduce given the same seed
- Educational creative-coding demos that show one technique end-to-end

**Trigger phrases**: "generative art", "p5.js sketch", "creative coding", "algorithmic art", "flow field", "particle system", "L-system", "procedural pattern", "generative wallpaper", "parametric sketch", "seeded randomness", "code-driven art", "generative design", "make an art piece", "draw something generative".

**When NOT to use**:

- Data dashboards or chart rendering with quantitative meaning (use `developer-experience/ui-component-generation` for the surrounding UI; this skill is aesthetic, not analytic)
- Static .pdf / print posters where the output is a single fixed composition (use the Static Poster Workflow in `developer-experience/creative-generation`)
- 3D shader work, ray-marched scenes, or fragment-shader visuals (use `specialized-domains/glsl-shader-development`)
- One-off SVG icons or fixed illustrations (no parameter surface, no philosophy step worth its weight)
- Brand-applied marketing visuals where brand tokens dominate (use `specialized-domains/brand-styling` to drive the palette and re-enter this skill only after the tokens are fixed)

If the artifact is fixed rather than parameter-driven, this skill is the wrong shape. Generative art's value is in the ability to re-roll: change a seed, move a slider, watch the family of outputs.

## Instructions

The skill has two non-negotiable steps. Do not skip Step 1. Do not produce a sketch without first producing the philosophy manifesto, because the manifesto is what stops the agent from defaulting to perlin-noise clichés.

### Step 1: Algorithmic Philosophy (Markdown manifesto)

Goal: write a 30-80 line Markdown document that fixes the aesthetic constraints before any code is written.

The manifesto must contain the following sections, in this order:

1. **Movement** - one or two named references (e.g., "suprematism + Vera Molnar's hand-drawn Computer-aided plotter work"; "op-art rooted in Bridget Riley's parallel-line tension"; "Casey Reas's process compendiums; James Paterson's tactile loops"). Pick references the agent can honor concretely, not vague gestures.
2. **Underlying principle** - the single idea the piece embodies. Examples: "flow as accumulated intent" (flow fields), "swarm as distributed individual decisions" (particle systems), "growth as recursion under bounded grammar" (L-systems). One sentence. If the principle takes a paragraph, the principle is not yet picked.
3. **Color and density behavior** - palette type (monochrome, dyad, triad), how density changes across the canvas (uniform, gradient, focal cluster), and what color does in response to density (saturation drops at high density, hue shifts with vector angle, value tracks distance-from-seed-point). Concrete rules, not adjectives.
4. **Motion behavior** - if the piece animates, what does motion express? Drift? Decay? Pulsing? If static, write "static; one frame; rendered once at fixed seed." Do not skip this section by saying "tasteful motion" - that is not a behavior.
5. **Parameter surface** - the 3-6 parameters the viewer slider panel will expose. Each one must be named, given a range (e.g., `noiseScale: 0.001 - 0.05`), and tied back to one of the four sections above. A parameter that does not change Movement, Principle, Color, or Motion is decorative and should be removed.
6. **What the piece is NOT** - a 2-4 line negative space declaration. "This is not a data visualization." "This is not branded marketing material." "This is not a 3D scene." "This is not a perlin-noise field with a hue rotation slider." The negative space prevents drift back to clichés in Step 2.

Save the manifesto as `<piece-name>-philosophy.md` alongside the generator file. Stage 2 reads it back when generating code, so it is durable, not ephemeral.

**Do not move to Step 2** until all six sections have non-empty content. A vague manifesto produces a vague sketch.

### Step 2: Generator + Viewer

Goal: ship two files - a p5.js sketch (`<piece-name>.js`) and an HTML viewer (`<piece-name>.html`) - that honor the manifesto and expose the parameter surface as live sliders.

Implementation rules:

1. **Seeded randomness everywhere**. Call `randomSeed(seed)` and `noiseSeed(seed)` in `setup()` before any random or noise call. The same seed must always produce the same image. If the user re-loads with the same URL parameters, the canvas must be byte-identical (or render-identical given browser AA). This is the contract that lets users iterate.
2. **Parameter surface mirrors the manifesto**. Every slider in the viewer maps to a Step-1 parameter. No mystery sliders. No parameters that the manifesto did not call out. If a parameter "feels useful" but isn't in the manifesto, go back to Step 1 and add it (with its tie-back to one of the four behavior sections), then implement.
3. **Pure p5.js, no build step**. Use the global-mode p5.js loaded from a CDN (`https://cdn.jsdelivr.net/npm/p5@1/lib/p5.min.js`). No npm, no Vite, no bundler. The sketch should run by opening the .html file in a browser - no localhost, no install. This is what makes the artifact portable.
4. **Templates as starting point, not as final output**. Three templates ship in `assets/`: `flow-field.html`, `particle-system.html`, `l-system.html`. Each is <= 200 lines, self-contained (single HTML file with embedded p5 instance + sliders + sketch), and uses the parameter / seed / philosophy pattern. Pick the closest template, then rewrite the sketch body to honor the new manifesto. Do not ship the template unmodified.
5. **Export-deterministic**. Bind a key (default `s`) to `saveCanvas('<piece>-<seed>', 'png')`. The exported PNG file's filename includes the seed so the artifact is fully reproducible from the .js + the seed alone. No hidden state.
6. **Performance budget**. The sketch should run >= 30 fps on a mid-tier laptop. Particle counts above 5000, recursion depths above 8, or per-frame `loadPixels`/`updatePixels` calls usually break this. If the manifesto demands density that breaks 30 fps, drop the framerate to 15 explicitly via `frameRate(15)` rather than letting the browser stutter.

Output structure (alongside the .js / .html):

```
<piece-name>/
├── <piece-name>-philosophy.md     # Step 1 manifesto
├── <piece-name>.js                # p5.js sketch (sketch logic only, no DOM)
├── <piece-name>.html              # viewer (loads p5, mounts sketch, renders sliders)
└── README.md                      # one-paragraph: how to open, key bindings, seed range
```

The HTML viewer's slider panel is positioned bottom-left or top-right (off the canvas), uses native `<input type="range">` elements (no UI library), and calls a `regenerate()` function on slider change that re-runs setup() with the new parameter values. Every parameter change is a re-roll, not a tween.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll skip the philosophy step and just write a sketch directly - the user wants art, not a manifesto" | Without Step 1, the agent defaults to perlin-noise clichés (washy hue gradient + 5000 particles + black background). The manifesto is what locks in a non-default aesthetic. The user does not see the .md, but they see the difference in the output. |
| "The default p5 template (perlin-noise flow field, hue rotation) looks fine - that IS the art" | That is the AI-slop default for generative art. Pick a movement reference and an underlying principle. "Looks fine" means "looks like every other generative-art tutorial". |
| "Seeded randomness is overkill for a one-off piece" | Without seeds, the user cannot iterate. They run the sketch, it produces something they like, they want to tweak one slider - and the random state has moved. The whole iterative workflow collapses. Seeded randomness costs 2 lines of code. |
| "The viewer doesn't need sliders - the user can edit constants in the .js" | Editing constants in source forces a save-and-reload cycle every iteration. Sliders cost 20 lines of HTML and turn the sketch into an actual exploration tool. The cost is paid once; the value compounds with every tweak. |
| "I'll use a fancy UI library (React, dat.gui, lil-gui) for the slider panel" | The artifact must run by double-clicking the .html. A UI library means npm, a build step, a bundler. That breaks portability for a 20-line gain in panel polish. Native `<input type="range">` is the right tool. |
| "The manifesto is too restrictive - I'll improvise the parameter surface as I code" | Improvised parameters drift back to clichés (always exposing `noiseScale` and `particleCount` because that's what every example exposes). The manifesto's parameter section is the constraint that surfaces the piece's actual axes of variation. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] `<piece-name>-philosophy.md` exists with all six required sections (Movement, Principle, Color/Density, Motion, Parameter Surface, What This Is NOT).
- [ ] `<piece-name>.html` opens in a browser and renders a canvas without errors in the JS console.
- [ ] `<piece-name>.js` calls `randomSeed(seed)` AND `noiseSeed(seed)` in `setup()` before any random/noise call.
- [ ] Re-loading the .html with the same seed produces a render-identical image (verify by screenshot diff or visual inspection).
- [ ] Every slider in the viewer maps to a parameter named in the manifesto's Parameter Surface section. Count matches.
- [ ] Pressing the export key (default `s`) saves a `<piece>-<seed>.png` file containing the current canvas.
- [ ] The sketch runs at >= 30 fps on a mid-tier laptop, OR `frameRate()` is explicitly set to a lower value with a justification comment.
- [ ] The artifact runs by opening the .html directly (no npm, no localhost, no build step).

"The output looks generative" is not a valid verification criterion. The verification is: does the philosophy manifesto exist, do the seeds reproduce, and do the sliders map back to declared parameters?

## Bundled Resources

Three starter templates ship under `assets/`. Each is a single self-contained HTML file (sketch + viewer + sliders, no external assets, p5.js from CDN), <= 200 lines, demonstrating the seed + parameter + philosophy pattern. Pick the template closest to the manifesto, then rewrite the sketch body.

- `assets/flow-field.html` - vector-field traced particles. Parameter surface: `noiseScale`, `noiseStrength`, `particleCount`, `traceAlpha`, `seed`.
- `assets/particle-system.html` - force-directed swarm with optional noise perturbation. Parameter surface: `count`, `damping`, `attraction`, `noisePerturb`, `seed`.
- `assets/l-system.html` - recursive grammar-driven branching. Parameter surface: `axiom`, `rules`, `iterations`, `angle`, `seed`.

Each template's top comment block names a default movement reference (Casey Reas, Vera Molnar, Aristid Lindenmayer's grammars). The template's reference is the starting point for the new manifesto's Movement section; replace it with whatever the user's piece is reaching for.

## Related Skills

- [[creative-generation]] -- umbrella creative-direction skill; its Static Poster Workflow handles the complementary case where the output is a fixed .pdf rather than a parameter-driven sketch.
- [[glsl-shader-development]] -- 3D shader / fragment-shader visuals; the GPU-side counterpart to this skill's CPU-side p5.js sketches.
- [[brand-styling]] -- apply user-supplied brand tokens (palette, typography) to the manifesto's Color section when the piece is brand-applied; otherwise this skill picks color rules autonomously.
- [[ui-component-generation]] -- surrounding UI / app shell when the generative piece is embedded in a larger product; this skill handles only the canvas, not the chrome.
- [[gif-sticker-maker]] -- export the generative output as an animated .gif loop when the artifact's natural form is a short cycle rather than a re-rollable still.
