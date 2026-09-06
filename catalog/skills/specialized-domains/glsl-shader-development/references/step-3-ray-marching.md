### Step 3: Ray Marching

Ray marching (sphere tracing) evaluates the scene SDF along each ray, stepping forward by the distance returned by the SDF. When the distance falls below a threshold, the ray has hit a surface.

**Core Sphere Tracing Algorithm**:

```glsl
const int MAX_STEPS = 128;
const float MAX_DIST = 100.0;
const float SURF_DIST = 0.001;  // Hit threshold

// Returns the distance along the ray to the nearest surface,
// or MAX_DIST if no hit was found.
float rayMarch(vec3 ro, vec3 rd) {
    float t = 0.0;
    for (int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * t;
        float d = map(p);       // Scene SDF
        if (d < SURF_DIST) break;
        t += d;
        if (t > MAX_DIST) break;
    }
    return t;
}
```

**Camera Setup** (look-at camera for ray marched scenes):

```glsl
// Build a camera matrix from eye position, target, and up vector.
// Returns the ray direction for a given screen coordinate.
mat3 setCamera(vec3 eye, vec3 target, float roll) {
    vec3 cw = normalize(target - eye);              // Forward
    vec3 cp = vec3(sin(roll), cos(roll), 0.0);      // Up with roll
    vec3 cu = normalize(cross(cw, cp));              // Right
    vec3 cv = normalize(cross(cu, cw));              // True up
    return mat3(cu, cv, cw);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalized coordinates: [-aspect, aspect] x [-1, 1]
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;

    // Camera position orbiting the origin
    float angle = iTime * 0.3;
    vec3 ro = vec3(4.0 * cos(angle), 2.5, 4.0 * sin(angle));
    vec3 target = vec3(0.0, 0.5, 0.0);

    // Camera-to-world matrix; 1.5 is the focal length (zoom)
    mat3 cam = setCamera(ro, target, 0.0);
    vec3 rd = cam * normalize(vec3(uv, 1.5));

    // Ray march
    float t = rayMarch(ro, rd);

    // Shade
    vec3 col = vec3(0.0);
    if (t < MAX_DIST) {
        vec3 p = ro + rd * t;
        vec3 n = getNormal(p);
        col = shade(p, n, rd);
    }

    // Gamma correction
    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

**Normal Estimation** (central differences on the SDF):

```glsl
vec3 getNormal(vec3 p) {
    vec2 e = vec2(0.0001, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

// Tetrahedron technique (4 samples instead of 6, slightly cheaper):
vec3 getNormalTet(vec3 p) {
    const vec2 e = vec2(1.0, -1.0) * 0.0001;
    return normalize(
        e.xyy * map(p + e.xyy) +
        e.yyx * map(p + e.yyx) +
        e.yxy * map(p + e.yxy) +
        e.xxx * map(p + e.xxx)
    );
}
```

**Ambient Occlusion** (approximated via SDF sampling along the normal):

```glsl
float calcAO(vec3 p, vec3 n) {
    float occ = 0.0;
    float decay = 1.0;
    for (int i = 1; i <= 5; i++) {
        float h = 0.01 + 0.12 * float(i);
        float d = map(p + n * h);
        occ += (h - d) * decay;
        decay *= 0.95;
    }
    return clamp(1.0 - 3.0 * occ, 0.0, 1.0);
}
```

**Soft Shadows** (penumbra via closest approach during marching):

```glsl
// March from surface point toward the light.
// k controls shadow softness (higher = harder, try 8.0-32.0).
float softShadow(vec3 ro, vec3 rd, float mint, float maxt, float k) {
    float res = 1.0;
    float t = mint;
    for (int i = 0; i < 64; i++) {
        float d = map(ro + rd * t);
        if (d < 0.001) return 0.0;   // Fully in shadow
        res = min(res, k * d / t);
        t += clamp(d, 0.02, 0.2);
        if (t > maxt) break;
    }
    return clamp(res, 0.0, 1.0);
}
```
