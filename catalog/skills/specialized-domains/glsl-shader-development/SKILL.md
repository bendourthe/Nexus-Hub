---
name: glsl-shader-development
description: GLSL shader programming expertise for visual effects, 3D graphics, and GPU computing. Use when writing fragment/vertex shaders, implementing ray marching, building procedural generation, creating post-processing effects, or working with WebGL/Three.js shaders.
summary_l0: "Write GLSL shaders for visual effects, ray marching, procedural generation, and 3D graphics"
overview_l1: "This skill provides GLSL shader programming expertise for visual effects, 3D graphics, and GPU computing. Use it when writing fragment or vertex shaders, implementing ray marching and sphere tracing, building procedural generation with noise functions, creating post-processing effects like bloom and depth of field, or working with WebGL and Three.js shader pipelines. Key capabilities include signed distance function (SDF) modeling with CSG operations, physically-based rendering with Cook-Torrance BRDF, procedural noise (Perlin, Simplex, Worley) and fractal brownian motion, camera and lighting setup for ray marched scenes, animation and mouse interaction in real-time shaders, and integration with Three.js ShaderMaterial and raw WebGL. The expected output is correct, performant GLSL shader code with proper precision qualifiers, optimized loops, and clean uniform interfaces. Trigger phrases: GLSL, shader, fragment shader, vertex shader, ray marching, SDF, signed distance function, procedural generation, noise function, post-processing, ShaderToy, WebGL, Three.js shader, PBR shader, Cook-Torrance, Perlin noise, Simplex noise, FBM."
---

# GLSL Shader Development

Structured guidance for writing GLSL shaders that produce correct visual output, run efficiently on the GPU, and integrate cleanly with WebGL and Three.js pipelines. Covers shader fundamentals, signed distance functions, ray marching, lighting models, procedural generation, post-processing effects, animation, and integration patterns.

## When to Use This Skill

Use this skill for:

- Writing vertex or fragment shaders in GLSL (ES 1.0, ES 3.0, or desktop GL)
- Implementing ray marching with signed distance functions for 3D scenes
- Building procedural textures and terrain with noise functions and FBM
- Creating post-processing effects (bloom, blur, chromatic aberration, color grading)
- Implementing physically-based rendering (PBR) or classical lighting models in shaders
- Integrating custom shaders into Three.js, WebGL, or ShaderToy
- Optimizing shader performance for mobile and low-end GPUs
- Animating shader parameters with time, mouse input, or audio data

**Trigger phrases**: "GLSL", "shader", "fragment shader", "vertex shader", "ray marching", "SDF", "signed distance function", "procedural generation", "noise function", "post-processing", "bloom", "depth of field", "ShaderToy", "WebGL", "Three.js shader", "PBR shader", "Cook-Torrance", "Perlin noise", "Simplex noise", "domain warping", "FBM", "sphere tracing", "screen-space effects"

## What This Skill Does

Provides GLSL shader development patterns including:

- **Shader Fundamentals**: Data types, precision qualifiers, uniforms, varyings, built-in variables, pipeline stages
- **Signed Distance Functions**: SDF primitives, CSG operations, smooth blending, repetition, domain transforms
- **Ray Marching**: Sphere tracing, camera setup, normal estimation, ambient occlusion, soft shadows
- **Lighting Models**: Phong, Blinn-Phong, PBR Cook-Torrance, Fresnel, environment mapping, HDR
- **Procedural Generation**: Perlin noise, Simplex noise, Worley noise, FBM, domain warping, terrain synthesis
- **Post-Processing**: Bloom, motion blur, depth of field, chromatic aberration, vignette, FXAA, color grading
- **Animation**: Time-based motion, easing functions, mouse interaction, morphing, particle systems
- **Integration**: Three.js ShaderMaterial, raw WebGL setup, uniform management, performance profiling

## Instructions

### Step 1: GLSL Fundamentals

Full walkthrough: [step-1-glsl-fundamentals.md](references/step-1-glsl-fundamentals.md) (load this step when you reach it).

### Step 2: Signed Distance Functions (SDFs)

Full walkthrough: [step-2-signed-distance-functions-sdfs.md](references/step-2-signed-distance-functions-sdfs.md) (load this step when you reach it).

### Step 3: Ray Marching

Full walkthrough: [step-3-ray-marching.md](references/step-3-ray-marching.md) (load this step when you reach it).

### Step 4: Lighting Models

Full walkthrough: [step-4-lighting-models.md](references/step-4-lighting-models.md) (load this step when you reach it).

### Step 5: Procedural Generation

Full walkthrough: [step-5-procedural-generation.md](references/step-5-procedural-generation.md) (load this step when you reach it).

### Step 6: Post-Processing Effects

Full walkthrough: [step-6-post-processing-effects.md](references/step-6-post-processing-effects.md) (load this step when you reach it).

### Step 7: Animation and Interaction

Full walkthrough: [step-7-animation-and-interaction.md](references/step-7-animation-and-interaction.md) (load this step when you reach it).

### Step 8: Integration and Optimization

Full walkthrough: [step-8-integration-and-optimization.md](references/step-8-integration-and-optimization.md) (load this step when you reach it).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It compiles, so the shader is correct" | A GLSL shader that compiles can still read uninitialized varyings as garbage or produce NaN from a divide-by-zero in the ray-march loop. Visual output plus a NaN/precision check is the only proof it is correct. |
| "I'll omit the precision qualifier, it works on desktop" | Desktop GL defaults to highp; mobile WebGL fragment shaders require an explicit `precision` declaration and fail to compile without it. The shader that runs on your laptop is a black screen on a phone. |
| "ray-march with 256 steps for quality, performance later" | A high step count plus heavy per-pixel ALU drops mobile below 60fps and may exceed the driver's loop-unroll limit so it will not compile at all. Budget steps against the fragment-cost target from the start. |
| "sin(iTime) is fine for the animation" | As iTime grows, mobile float precision turns sin(largeNumber) into visible jitter. Wrapping the input with `mod(iTime, 6.2831)` is what keeps the animation stable over a long session. |

## Verification

- [ ] The shader compiles with no errors: `gl.getShaderInfoLog()` is empty after `compileShader()`
- [ ] Every fragment shader declares an explicit `precision` qualifier
- [ ] All varyings written by the vertex shader are read (and initialized) in the fragment shader
- [ ] The output contains no NaN/black artifacts (divide-by-zero and unbounded values are guarded)
- [ ] Ray-march / loop bounds use a constant (`#define` or `const int`) so the driver can unroll them
- [ ] Per-pixel cost meets the documented fragment budget (under ~50 ALU ops for 60fps mobile)

## Related Skills

- [[generative-art]] -- p5.js generative-art pipeline that often pairs with shader-driven visuals
- [[creative-generation]] -- creative direction and ideation for the visual effect a shader implements
- [[code-optimizer]] -- profiling and ALU-reduction techniques for hot fragment shaders
- [[web-artifacts-builder]] -- scaffold the WebGL / Three.js host page that runs the shader
