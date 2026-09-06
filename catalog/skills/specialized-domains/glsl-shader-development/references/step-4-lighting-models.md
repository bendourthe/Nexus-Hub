### Step 4: Lighting Models

Lighting models compute surface color from material properties, light direction, view direction, and surface normals.

**Blinn-Phong Lighting** (classical model, suitable for non-photorealistic rendering):

```glsl
struct Light {
    vec3 direction;  // Normalized direction toward the light
    vec3 color;
    float intensity;
};

vec3 blinnPhong(vec3 p, vec3 n, vec3 viewDir, vec3 albedo) {
    Light sun;
    sun.direction = normalize(vec3(0.8, 0.4, 0.6));
    sun.color = vec3(1.0, 0.95, 0.9);
    sun.intensity = 1.2;

    // Ambient
    vec3 ambient = 0.15 * albedo;

    // Diffuse (Lambertian)
    float diff = max(dot(n, sun.direction), 0.0);
    vec3 diffuse = diff * albedo * sun.color * sun.intensity;

    // Specular (Blinn-Phong half-vector)
    vec3 halfDir = normalize(sun.direction + viewDir);
    float spec = pow(max(dot(n, halfDir), 0.0), 64.0);
    vec3 specular = spec * sun.color * 0.5;

    // Shadow
    float shadow = softShadow(p + n * 0.01, sun.direction, 0.01, 20.0, 16.0);

    // Ambient occlusion
    float ao = calcAO(p, n);

    return ambient * ao + (diffuse + specular) * shadow;
}
```

**Physically-Based Rendering (PBR) with Cook-Torrance BRDF**:

```glsl
// Material parameters
struct Material {
    vec3  albedo;      // Base color
    float metallic;    // 0.0 = dielectric, 1.0 = metal
    float roughness;   // 0.0 = mirror, 1.0 = diffuse
    float ao;          // Ambient occlusion (pre-baked or computed)
};

const float PI = 3.14159265359;

// Normal Distribution Function (GGX/Trowbridge-Reitz)
float distributionGGX(vec3 N, vec3 H, float roughness) {
    float a  = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;
    float denom = NdotH2 * (a2 - 1.0) + 1.0;
    return a2 / (PI * denom * denom);
}

// Geometry function (Smith's method with Schlick-GGX)
float geometrySchlickGGX(float NdotV, float roughness) {
    float r = roughness + 1.0;
    float k = (r * r) / 8.0;
    return NdotV / (NdotV * (1.0 - k) + k);
}

float geometrySmith(vec3 N, vec3 V, vec3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    return geometrySchlickGGX(NdotV, roughness)
         * geometrySchlickGGX(NdotL, roughness);
}

// Fresnel (Schlick approximation)
vec3 fresnelSchlick(float cosTheta, vec3 F0) {
    return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

// Fresnel with roughness correction for ambient term
vec3 fresnelSchlickRoughness(float cosTheta, vec3 F0, float roughness) {
    return F0 + (max(vec3(1.0 - roughness), F0) - F0)
         * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}

// Full PBR shading for a single point light
vec3 pbrShade(vec3 p, vec3 N, vec3 V, Material mat,
              vec3 lightPos, vec3 lightColor) {
    vec3 L = normalize(lightPos - p);
    vec3 H = normalize(V + L);

    float dist = length(lightPos - p);
    float attenuation = 1.0 / (dist * dist);
    vec3 radiance = lightColor * attenuation;

    // F0: reflectance at normal incidence
    // Dielectrics use 0.04; metals tint F0 with albedo
    vec3 F0 = mix(vec3(0.04), mat.albedo, mat.metallic);

    // Cook-Torrance specular BRDF
    float D = distributionGGX(N, H, mat.roughness);
    float G = geometrySmith(N, V, L, mat.roughness);
    vec3  F = fresnelSchlick(max(dot(H, V), 0.0), F0);

    vec3 numerator = D * G * F;
    float denominator = 4.0 * max(dot(N, V), 0.0)
                            * max(dot(N, L), 0.0) + 0.0001;
    vec3 specular = numerator / denominator;

    // Energy conservation: diffuse component
    vec3 kD = (vec3(1.0) - F) * (1.0 - mat.metallic);
    float NdotL = max(dot(N, L), 0.0);

    return (kD * mat.albedo / PI + specular) * radiance * NdotL;
}
```

**Environment Mapping** (approximate image-based lighting):

```glsl
// Sample a cubemap for reflections
vec3 envReflection(vec3 N, vec3 V, float roughness, samplerCube envMap) {
    vec3 R = reflect(-V, N);
    // Approximate LOD from roughness for pre-filtered env maps
    float lod = roughness * 6.0;
    vec3 envColor = textureLod(envMap, R, lod).rgb;
    return envColor;
}

// Simple sky gradient as a procedural environment (no cubemap needed)
vec3 skyColor(vec3 rd) {
    float t = 0.5 * (rd.y + 1.0);
    vec3 horizon = vec3(0.8, 0.85, 0.95);
    vec3 zenith  = vec3(0.3, 0.5, 0.9);
    return mix(horizon, zenith, t);
}
```
