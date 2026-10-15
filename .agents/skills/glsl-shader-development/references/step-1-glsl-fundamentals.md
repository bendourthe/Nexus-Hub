### Step 1: GLSL Fundamentals

GLSL (OpenGL Shading Language) runs on the GPU in two primary stages: the vertex shader transforms geometry, and the fragment shader computes per-pixel color. Understanding the data flow between these stages and the host application is essential.

**Shader Types and Pipeline**:

| Stage | Purpose | Runs Per | Key Outputs |
|-------|---------|----------|-------------|
| Vertex Shader | Transform vertex positions, pass data to fragment | Vertex | `gl_Position`, varyings |
| Fragment Shader | Compute final pixel color | Fragment/pixel | `gl_FragColor` / `fragColor` |
| Compute Shader | General GPU compute (GL 4.3+, not WebGL) | Work group | Buffer writes |

**Data Types**:

```glsl
// Scalar types
float f = 1.0;        // Always use decimal point (1.0 not 1)
int   i = 42;
bool  b = true;

// Vector types: vec2, vec3, vec4 (float); ivec2..4 (int); bvec2..4 (bool)
vec2 uv = vec2(0.5, 0.5);
vec3 color = vec3(1.0, 0.0, 0.0);        // Red
vec4 rgba = vec4(color, 1.0);             // Construct from vec3 + float

// Swizzling: access components as .xyzw, .rgba, or .stpq
vec3 normal = rgba.xyz;
vec2 rg = color.rg;
vec3 flipped = color.zyx;                 // Reorder components

// Matrix types: mat2, mat3, mat4 (column-major)
mat3 rotation = mat3(
    cos(a), -sin(a), 0.0,
    sin(a),  cos(a), 0.0,
    0.0,     0.0,    1.0
);

// Samplers (texture handles, set from host)
uniform sampler2D uTexture;
uniform samplerCube uEnvMap;
```

**Precision Qualifiers** (critical for mobile/WebGL):

```glsl
// Fragment shaders in GLSL ES require explicit precision
precision highp float;     // 32-bit; use for positions and ray marching
precision mediump float;   // 16-bit; adequate for color, UVs on mobile
precision lowp float;      // 10-bit; sufficient for simple color lookups

// Per-variable override when global precision is mediump
highp vec3 worldPos = uCameraPos + rd * t;
```

**Uniforms, Attributes, and Varyings**:

```glsl
// ---- Vertex Shader (GLSL ES 1.0 / WebGL 1) ----
attribute vec3 aPosition;          // Per-vertex input from buffer
attribute vec2 aTexCoord;
uniform mat4 uModelViewProjection; // Set by host once per draw call
uniform float uTime;
varying vec2 vTexCoord;            // Interpolated to fragment shader
varying vec3 vWorldPos;

void main() {
    vTexCoord = aTexCoord;
    vWorldPos = aPosition;
    gl_Position = uModelViewProjection * vec4(aPosition, 1.0);
}

// ---- Fragment Shader (GLSL ES 1.0 / WebGL 1) ----
precision highp float;
uniform sampler2D uTexture;
uniform vec3 uLightDir;
varying vec2 vTexCoord;
varying vec3 vWorldPos;

void main() {
    vec4 texColor = texture2D(uTexture, vTexCoord);
    gl_FragColor = texColor;
}
```

**GLSL ES 3.0 (WebGL 2) differences**:

```glsl
#version 300 es
precision highp float;

// 'attribute' becomes 'in', 'varying' becomes 'in'/'out'
in vec3 aPosition;          // vertex shader input
out vec2 vTexCoord;          // vertex shader output / fragment shader input

// texture2D() becomes texture()
// gl_FragColor is replaced by a declared output
out vec4 fragColor;

void main() {
    fragColor = texture(uTexture, vTexCoord);
}
```

**ShaderToy vs WebGL vs Three.js Pipeline Comparison**:

| Feature | ShaderToy | Raw WebGL | Three.js ShaderMaterial |
|---------|-----------|-----------|------------------------|
| Entry point | `mainImage(out vec4, in vec2)` | `void main()` | `void main()` |
| Screen coords | `fragCoord` (pixel), `iResolution` | `gl_FragCoord` | `vUv` (0-1 range) |
| Time | `iTime` | Custom `uniform float uTime` | Custom uniform |
| Mouse | `iMouse` (vec4) | Custom uniform | Custom uniform |
| Textures | `iChannel0..3` | Custom sampler2D | Custom sampler2D |
| Output | `fragColor` parameter | `gl_FragColor` / out var | `gl_FragColor` / out var |

**Built-in Functions** (most commonly used):

```glsl
// Math
float a = mix(x, y, t);          // Linear interpolation: x*(1-t) + y*t
float b = clamp(x, 0.0, 1.0);   // Constrain to range
float c = smoothstep(e0, e1, x); // Hermite interpolation (smooth clamp)
float d = step(edge, x);         // 0.0 if x < edge, else 1.0
float e = fract(x);              // x - floor(x)
float f = mod(x, y);             // x - y * floor(x/y)

// Vector operations
float  len = length(v);
vec3   n   = normalize(v);
float  d   = dot(a, b);
vec3   c   = cross(a, b);
float  dst = distance(a, b);
vec3   r   = reflect(incident, normal);
vec3   rf  = refract(incident, normal, eta);

// Trigonometry
float s = sin(x);   float c = cos(x);   float t = tan(x);
float a = asin(x);  float a = acos(x);  float a = atan(y, x);
```
