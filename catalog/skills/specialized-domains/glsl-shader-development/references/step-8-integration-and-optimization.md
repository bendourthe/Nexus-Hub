### Step 8: Integration and Optimization

This step covers integrating custom shaders into real applications and ensuring they perform well across devices.

**Three.js ShaderMaterial Integration**:

```javascript
// JavaScript: create a custom shader material in Three.js
import * as THREE from "three";

const vertexShader = `
    varying vec2 vUv;
    varying vec3 vWorldPos;

    void main() {
        vUv = uv;
        vWorldPos = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
`;

const fragmentShader = `
    precision highp float;
    uniform float uTime;
    uniform vec2 uResolution;
    uniform vec3 uCameraPos;
    varying vec2 vUv;
    varying vec3 vWorldPos;

    // Paste GLSL functions here (noise, SDFs, lighting, etc.)

    void main() {
        vec2 uv = vUv;
        vec3 color = vec3(0.0);
        // Your shader logic here
        gl_FragColor = vec4(color, 1.0);
    }
`;

const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
        uTime: { value: 0.0 },
        uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
        uCameraPos: { value: new THREE.Vector3() },
    },
    // Optional settings:
    transparent: true,           // Enable if using alpha
    side: THREE.DoubleSide,      // Render both faces
    depthWrite: false,           // Disable for transparent overlays
});

// Update uniforms in the render loop
function animate(time) {
    material.uniforms.uTime.value = time * 0.001; // ms to seconds
    material.uniforms.uCameraPos.value.copy(camera.position);
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}

// Handle window resize
window.addEventListener("resize", () => {
    material.uniforms.uResolution.value.set(window.innerWidth, window.innerHeight);
});
```

**Raw WebGL Shader Setup** (minimal boilerplate):

```javascript
// Compile and link a shader program from source strings
function createShaderProgram(gl, vertSrc, fragSrc) {
    function compileShader(type, source) {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            const log = gl.getShaderInfoLog(shader);
            gl.deleteShader(shader);
            throw new Error(`Shader compile error: ${log}`);
        }
        return shader;
    }

    const vert = compileShader(gl.VERTEX_SHADER, vertSrc);
    const frag = compileShader(gl.FRAGMENT_SHADER, fragSrc);
    const program = gl.createProgram();
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.linkProgram(program);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        const log = gl.getProgramInfoLog(program);
        gl.deleteProgram(program);
        throw new Error(`Program link error: ${log}`);
    }

    gl.deleteShader(vert);
    gl.deleteShader(frag);
    return program;
}

// Set uniform values by type
function setUniforms(gl, program, uniforms) {
    for (const [name, value] of Object.entries(uniforms)) {
        const loc = gl.getUniformLocation(program, name);
        if (loc === null) continue; // Uniform optimized away

        if (typeof value === "number") {
            gl.uniform1f(loc, value);
        } else if (value.length === 2) {
            gl.uniform2fv(loc, value);
        } else if (value.length === 3) {
            gl.uniform3fv(loc, value);
        } else if (value.length === 4) {
            gl.uniform4fv(loc, value);
        }
    }
}
```

**Uniform Management Pattern** (typed wrapper for shader uniforms):

```typescript
// TypeScript: type-safe uniform manager
interface UniformDefs {
    [name: string]: "float" | "vec2" | "vec3" | "vec4" | "mat4" | "sampler2D";
}

class UniformManager<T extends UniformDefs> {
    private locations: Map<string, WebGLUniformLocation | null> = new Map();

    constructor(
        private gl: WebGL2RenderingContext,
        private program: WebGLProgram,
        defs: T,
    ) {
        for (const name of Object.keys(defs)) {
            this.locations.set(name, gl.getUniformLocation(program, name));
        }
    }

    set(name: keyof T, value: number | Float32Array): void {
        const loc = this.locations.get(name as string);
        if (loc === null || loc === undefined) return;

        if (typeof value === "number") {
            this.gl.uniform1f(loc, value);
        } else {
            switch (value.length) {
                case 2:  this.gl.uniform2fv(loc, value); break;
                case 3:  this.gl.uniform3fv(loc, value); break;
                case 4:  this.gl.uniform4fv(loc, value); break;
                case 16: this.gl.uniformMatrix4fv(loc, false, value); break;
            }
        }
    }
}
```

**Performance Profiling and Optimization**:

GPU shaders are limited by ALU (arithmetic), texture fetches, and bandwidth. Profile with browser DevTools (Chrome GPU profiling) or `EXT_disjoint_timer_query` for per-draw-call timing.

Common optimizations:

```glsl
// 1. Reduce ray march steps for distant objects (LOD)
float rayMarchLOD(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        // Increase threshold with distance (distant detail is invisible)
        float threshold = SURF_DIST * (1.0 + t * 0.1);
        if (d < threshold) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return t;
}

// 2. Avoid expensive functions in inner loops
// BAD: calling pow() per step
for (int i = 0; i < 128; i++) {
    float d = pow(length(p), 2.0); // pow is expensive
}
// GOOD: use multiplication
for (int i = 0; i < 128; i++) {
    float l = length(p);
    float d = l * l; // Same result, cheaper
}

// 3. Use step/smoothstep instead of if/else (avoids branch divergence)
// BAD:
if (d < 0.5) { color = vec3(1.0, 0.0, 0.0); }
else { color = vec3(0.0, 0.0, 1.0); }
// GOOD:
color = mix(vec3(0.0, 0.0, 1.0), vec3(1.0, 0.0, 0.0), step(d, 0.5));

// 4. Precompute constants outside loops
float invRes = 1.0 / iResolution.y; // Compute once, not per pixel

// 5. Reduce texture samples: combine lookups, use mipmaps
// Use textureLod() with explicit LOD when you know the needed detail level

// 6. Use half-precision where full precision is unnecessary (mobile)
// mediump is 16-bit; sufficient for colors and UVs
mediump vec3 color = texture(uTex, uv).rgb;
```

**Mobile and WebGL Considerations**:

| Concern | Guideline |
|---------|-----------|
| Precision | Use `mediump` globally, `highp` only for positions and ray marching |
| Loop limits | Keep ray march steps under 64 on mobile; use early exit |
| Texture size | Power-of-two textures for WebGL 1 compatibility |
| Fragment cost | Target under 50 ALU operations per pixel for 60fps on mobile |
| Extensions | Check `gl.getExtension()` before using OES_texture_float, etc. |
| Overdraw | Minimize transparent layers; each adds a full-screen pass |
| Compile time | Large shaders may cause visible hitches on first use; warm up off-screen |

**Common Pitfalls**:

1. **Floating-point precision**: On mobile, `sin(largeNumber)` produces garbage. Reduce the input range: `sin(mod(iTime, 6.2831))`.
2. **Uninitialized varyings**: If the vertex shader does not write to a varying, the fragment shader reads undefined values. Always initialize all varyings.
3. **Integer division**: GLSL ES does not guarantee integer division behavior for negative values. Cast to float, divide, then floor.
4. **Texture coordinate clamping**: Use `clamp(uv, 0.0, 1.0)` or set the sampler wrap mode to avoid sampling outside [0,1].
5. **Depth buffer precision**: Z-fighting occurs when near/far planes are too far apart. Keep the near plane as large as practical.
6. **Shader compilation errors**: Compilation errors are only available via `gl.getShaderInfoLog()`. Always check after `compileShader()`.
7. **Missing precision qualifier**: WebGL fragment shaders require an explicit `precision` declaration. Omitting it is a compile error on mobile.
8. **Loop unrolling limits**: Some drivers refuse to compile loops with non-constant bounds. Use `#define MAX_STEPS 128` or `const int`.
