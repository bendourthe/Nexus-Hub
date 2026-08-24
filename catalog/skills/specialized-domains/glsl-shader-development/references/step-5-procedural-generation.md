### Step 5: Procedural Generation

Procedural generation uses mathematical functions to create textures, terrain, and organic forms without pre-authored image data. Noise functions are the fundamental building blocks.

**Hash and Value Noise**:

```glsl
// Integer hash (for noise seed generation)
float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// 2D value noise
float valueNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    // Hermite interpolation (smoother than linear)
    vec2 u = f * f * (3.0 - 2.0 * f);

    float a = hash(i + vec2(0.0, 0.0));
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
```

**Gradient Noise (Perlin-style)**:

```glsl
// 2D gradient noise
vec2 hashGrad(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
             dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float gradientNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0); // Quintic curve

    return mix(
        mix(dot(hashGrad(i + vec2(0.0, 0.0)), f - vec2(0.0, 0.0)),
            dot(hashGrad(i + vec2(1.0, 0.0)), f - vec2(1.0, 0.0)), u.x),
        mix(dot(hashGrad(i + vec2(0.0, 1.0)), f - vec2(0.0, 1.0)),
            dot(hashGrad(i + vec2(1.0, 1.0)), f - vec2(1.0, 1.0)), u.x),
        u.y
    );
}
```

**Simplex Noise** (3D, fewer artifacts than Perlin):

```glsl
// 3D Simplex noise (based on Ashima Arts implementation)
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x * 34.0) + 10.0) * x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
    const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i  = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0) * 2.0 + 1.0;
    vec4 s1 = floor(b1) * 2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
    vec3 p0 = vec3(a0.xy, h.x);
    vec3 p1 = vec3(a0.zw, h.y);
    vec3 p2 = vec3(a1.xy, h.z);
    vec3 p3 = vec3(a1.zw, h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.5 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 105.0 * dot(m * m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
```

**Worley (Cellular) Noise**:

```glsl
// 2D Worley noise: returns distance to nearest cell center
vec2 worley(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float d1 = 1.0;  // Nearest distance
    float d2 = 1.0;  // Second nearest distance

    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 cellCenter = hash2(i + neighbor); // Random offset 0..1
            vec2 diff = neighbor + cellCenter - f;
            float d = length(diff);
            if (d < d1) {
                d2 = d1;
                d1 = d;
            } else if (d < d2) {
                d2 = d;
            }
        }
    }
    return vec2(d1, d2); // .x = nearest, .y = second nearest
}

vec2 hash2(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}
```

**Fractal Brownian Motion (FBM)** (layered noise octaves):

```glsl
// FBM with configurable octaves, lacunarity, and gain
float fbm(vec2 p, int octaves) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    float lacunarity = 2.0;   // Frequency multiplier per octave
    float gain = 0.5;         // Amplitude multiplier per octave (persistence)

    for (int i = 0; i < octaves; i++) {
        value += amplitude * gradientNoise(p * frequency);
        frequency *= lacunarity;
        amplitude *= gain;
    }
    return value;
}
```

**Domain Warping** (feed noise into itself for organic distortion):

```glsl
// Single-pass domain warp
float warpedNoise(vec2 p) {
    vec2 q = vec2(
        fbm(p + vec2(0.0, 0.0), 6),
        fbm(p + vec2(5.2, 1.3), 6)
    );
    return fbm(p + 4.0 * q, 6);
}

// Double-pass domain warp (more complex, painterly look)
float doubleWarp(vec2 p) {
    vec2 q = vec2(
        fbm(p + vec2(0.0, 0.0), 6),
        fbm(p + vec2(5.2, 1.3), 6)
    );
    vec2 r = vec2(
        fbm(p + 4.0 * q + vec2(1.7, 9.2), 6),
        fbm(p + 4.0 * q + vec2(8.3, 2.8), 6)
    );
    return fbm(p + 4.0 * r, 6);
}
```

**Terrain Generation** (height field from FBM for a ray marched landscape):

```glsl
float terrainHeight(vec2 xz) {
    float h = 0.0;
    float amp = 1.0;
    float freq = 0.005;
    for (int i = 0; i < 8; i++) {
        h += amp * gradientNoise(xz * freq);
        freq *= 2.0;
        amp *= 0.5;
    }
    // Ridge noise variant: fold the noise for sharp peaks
    // h = abs(h);
    return h * 40.0; // Scale to world units
}

// SDF for terrain: compare y against the height field
float mapTerrain(vec3 p) {
    return p.y - terrainHeight(p.xz);
}
```
