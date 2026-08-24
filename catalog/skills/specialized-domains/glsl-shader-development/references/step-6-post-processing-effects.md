### Step 6: Post-Processing Effects

Post-processing effects operate on the rendered image as a full-screen fragment shader pass. The scene is first rendered to a framebuffer texture, then processed.

**Bloom** (glow from bright areas):

```glsl
// Step 1: Extract bright pixels (threshold pass)
vec3 brightnessThreshold(vec3 color, float threshold) {
    float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722)); // Luminance
    return (brightness > threshold) ? color : vec3(0.0);
}

// Step 2: Gaussian blur (two-pass separable, horizontal then vertical)
vec3 gaussianBlur(sampler2D tex, vec2 uv, vec2 direction, vec2 resolution) {
    vec3 result = vec3(0.0);
    float weights[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
    vec2 texelSize = 1.0 / resolution;

    result += texture(tex, uv).rgb * weights[0];
    for (int i = 1; i < 5; i++) {
        vec2 offset = direction * texelSize * float(i);
        result += texture(tex, uv + offset).rgb * weights[i];
        result += texture(tex, uv - offset).rgb * weights[i];
    }
    return result;
}

// Step 3: Combine original + blurred bright pixels
vec3 applyBloom(sampler2D sceneTex, sampler2D bloomTex, vec2 uv, float strength) {
    vec3 scene = texture(sceneTex, uv).rgb;
    vec3 bloom = texture(bloomTex, uv).rgb;
    return scene + bloom * strength;
}
```

**Depth of Field** (circle of confusion based on depth):

```glsl
vec3 depthOfField(sampler2D sceneTex, sampler2D depthTex, vec2 uv,
                  vec2 resolution, float focusDist, float aperture) {
    float depth = texture(depthTex, uv).r;
    float coc = abs(depth - focusDist) * aperture; // Circle of confusion
    coc = clamp(coc, 0.0, 1.0);

    vec3 result = vec3(0.0);
    float total = 0.0;
    int samples = 16;

    // Poisson disk sampling for bokeh shape
    for (int i = 0; i < samples; i++) {
        float angle = float(i) * 2.39996323;  // Golden angle
        float radius = sqrt(float(i) / float(samples)) * coc;
        vec2 offset = vec2(cos(angle), sin(angle)) * radius / resolution;
        result += texture(sceneTex, uv + offset).rgb;
        total += 1.0;
    }
    return result / total;
}
```

**Chromatic Aberration** (color channel separation):

```glsl
vec3 chromaticAberration(sampler2D tex, vec2 uv, float intensity) {
    vec2 dir = uv - 0.5; // Direction from center
    float d = length(dir);
    vec2 offset = dir * d * intensity;

    float r = texture(tex, uv + offset).r;
    float g = texture(tex, uv).g;
    float b = texture(tex, uv - offset).b;
    return vec3(r, g, b);
}
```

**Vignette** (darken edges):

```glsl
vec3 vignette(vec3 color, vec2 uv, float intensity, float smoothness) {
    float d = distance(uv, vec2(0.5));
    float vig = smoothstep(0.5, 0.5 - smoothness, d * (1.0 + intensity));
    return color * vig;
}
```

**Color Grading** (tone mapping and color adjustment):

```glsl
// ACES filmic tone mapping (standard for HDR to LDR conversion)
vec3 acesToneMap(vec3 x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

// Reinhard tone mapping (simpler alternative)
vec3 reinhardToneMap(vec3 color) {
    return color / (color + vec3(1.0));
}

// Color temperature adjustment (warm = positive, cool = negative)
vec3 colorTemperature(vec3 color, float temperature) {
    color.r *= 1.0 + temperature * 0.1;
    color.b *= 1.0 - temperature * 0.1;
    return clamp(color, 0.0, 1.0);
}

// Contrast and saturation
vec3 adjustContrast(vec3 color, float contrast) {
    return 0.5 + (color - 0.5) * contrast;
}

vec3 adjustSaturation(vec3 color, float saturation) {
    float luma = dot(color, vec3(0.2126, 0.7152, 0.0722));
    return mix(vec3(luma), color, saturation);
}

// Complete post-processing chain
vec3 postProcess(vec3 color, vec2 uv) {
    color = acesToneMap(color);                         // Tone map HDR to LDR
    color = adjustContrast(color, 1.1);                // Slight contrast boost
    color = adjustSaturation(color, 1.15);             // Slight saturation boost
    color = colorTemperature(color, 0.3);              // Warm tint
    color = vignette(color, uv, 0.3, 0.4);            // Subtle vignette
    color = pow(color, vec3(1.0 / 2.2));               // Gamma correction
    return color;
}
```

**FXAA** (Fast Approximate Anti-Aliasing):

```glsl
// Simplified single-pass FXAA
vec3 fxaa(sampler2D tex, vec2 uv, vec2 resolution) {
    vec2 texel = 1.0 / resolution;

    // Sample luminance at center and four neighbors
    float lumC  = dot(texture(tex, uv).rgb, vec3(0.299, 0.587, 0.114));
    float lumN  = dot(texture(tex, uv + vec2(0.0,  texel.y)).rgb, vec3(0.299, 0.587, 0.114));
    float lumS  = dot(texture(tex, uv + vec2(0.0, -texel.y)).rgb, vec3(0.299, 0.587, 0.114));
    float lumE  = dot(texture(tex, uv + vec2( texel.x, 0.0)).rgb, vec3(0.299, 0.587, 0.114));
    float lumW  = dot(texture(tex, uv + vec2(-texel.x, 0.0)).rgb, vec3(0.299, 0.587, 0.114));

    float lumMin = min(lumC, min(min(lumN, lumS), min(lumE, lumW)));
    float lumMax = max(lumC, max(max(lumN, lumS), max(lumE, lumW)));
    float lumRange = lumMax - lumMin;

    // Skip anti-aliasing if contrast is low
    if (lumRange < max(0.0312, lumMax * 0.125)) {
        return texture(tex, uv).rgb;
    }

    // Determine blur direction from gradient
    vec2 dir;
    dir.x = -((lumN + lumS) - 2.0 * lumC);
    dir.y =  ((lumE + lumW) - 2.0 * lumC);
    float dirReduce = max((lumN + lumS + lumE + lumW) * 0.25 * 0.25, 1.0 / 128.0);
    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = clamp(dir * rcpDirMin, -8.0, 8.0) * texel;

    // Two-tap filter along the edge
    vec3 rgbA = 0.5 * (texture(tex, uv + dir * (1.0 / 3.0 - 0.5)).rgb
                      + texture(tex, uv + dir * (2.0 / 3.0 - 0.5)).rgb);
    vec3 rgbB = rgbA * 0.5 + 0.25 * (
                texture(tex, uv + dir * -0.5).rgb
              + texture(tex, uv + dir *  0.5).rgb);

    float lumB = dot(rgbB, vec3(0.299, 0.587, 0.114));
    return (lumB < lumMin || lumB > lumMax) ? rgbA : rgbB;
}
```
