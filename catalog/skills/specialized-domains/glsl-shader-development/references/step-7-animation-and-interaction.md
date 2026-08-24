### Step 7: Animation and Interaction

Shaders run every frame. Animation is driven by uniforms (time, mouse position, audio data) that the host application updates each frame.

**Time-Based Animation**:

```glsl
// Oscillation patterns
float pulse    = sin(iTime * 2.0) * 0.5 + 0.5;       // 0..1 sine wave
float sawtooth = fract(iTime * 0.5);                    // 0..1 repeating ramp
float triangle = abs(fract(iTime * 0.5) * 2.0 - 1.0);  // 0..1..0 triangle

// Animate an SDF object position
vec3 animatedPos = vec3(
    sin(iTime) * 2.0,
    abs(sin(iTime * 2.0)) + 0.5,   // Bouncing (abs(sin) for always positive)
    cos(iTime) * 2.0
);

// Smooth start/stop with easing
float t = clamp(iTime / 3.0, 0.0, 1.0); // 0 to 1 over 3 seconds
float easeInOut = t * t * (3.0 - 2.0 * t);             // Smoothstep easing
float easeOutBounce = 1.0 - pow(1.0 - t, 3.0);         // Decelerate
float easeInElastic = pow(2.0, 10.0 * (t - 1.0))
                    * sin((t - 1.075) * 2.0 * PI / 0.3); // Elastic snap
```

**Mouse Interaction** (ShaderToy conventions):

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // iMouse: .xy = current position (while pressed), .zw = click position
    vec2 mouse = iMouse.xy / iResolution.xy;

    // Use mouse to control camera orbit angle
    float yaw   = (mouse.x - 0.5) * PI * 2.0;
    float pitch  = (mouse.y - 0.5) * PI * 0.5;
    vec3 ro = vec3(
        5.0 * cos(yaw) * cos(pitch),
        5.0 * sin(pitch) + 1.0,
        5.0 * sin(yaw) * cos(pitch)
    );

    // Or use mouse to control a parameter (e.g., roughness slider)
    float roughness = mouse.x;
    float metallic  = mouse.y;
}
```

**Morphing Between Shapes** (SDF interpolation):

```glsl
float morphScene(vec3 p) {
    float sphere = sdSphere(p, 1.0);
    float box    = sdBox(p, vec3(0.8));
    float torus  = sdTorus(p, vec2(1.0, 0.3));

    // Cycle through shapes over time
    float t = fract(iTime * 0.2);  // 0..1 repeating
    float phase = t * 3.0;          // 0..3

    float d;
    if (phase < 1.0) {
        d = mix(sphere, box, smoothstep(0.0, 1.0, phase));
    } else if (phase < 2.0) {
        d = mix(box, torus, smoothstep(0.0, 1.0, phase - 1.0));
    } else {
        d = mix(torus, sphere, smoothstep(0.0, 1.0, phase - 2.0));
    }
    return d;
}
```

**Simple Particle System** (stateless, computed from time and index):

```glsl
// Stateless particle: position derived from hash and time
vec3 particlePos(int id, float time) {
    float fid = float(id);
    vec3 seed = vec3(
        hash(vec2(fid, 0.0)),
        hash(vec2(fid, 1.0)),
        hash(vec2(fid, 2.0))
    );

    float lifetime = 2.0 + seed.z * 3.0;           // 2-5 seconds
    float t = mod(time + seed.x * lifetime, lifetime) / lifetime; // 0..1

    vec3 origin = vec3(seed.x - 0.5, 0.0, seed.y - 0.5) * 4.0;
    vec3 velocity = vec3(0.0, 2.0, 0.0) + (seed - 0.5) * 0.5;
    vec3 gravity = vec3(0.0, -1.0, 0.0);

    return origin + velocity * t * lifetime + 0.5 * gravity * t * t * lifetime * lifetime;
}

// Render particles as glowing spheres in a ray marched scene
float particleField(vec3 p, float time) {
    float d = 1e10;
    for (int i = 0; i < 50; i++) {
        vec3 pp = particlePos(i, time);
        float fid = float(i);
        float lifetime = 2.0 + hash(vec2(fid, 2.0)) * 3.0;
        float t = mod(time + hash(vec2(fid, 0.0)) * lifetime, lifetime) / lifetime;
        float radius = 0.05 * sin(t * PI); // Grow then shrink
        d = min(d, sdSphere(p - pp, radius));
    }
    return d;
}
```

**Fluid Simulation Basics** (2D advection with noise for visual effect, not physical simulation):

```glsl
// Pseudo-fluid: advect UVs through a time-varying velocity field
vec3 fluidEffect(vec2 uv, float time) {
    vec2 vel = vec2(
        gradientNoise(uv * 3.0 + vec2(time * 0.3, 0.0)),
        gradientNoise(uv * 3.0 + vec2(0.0, time * 0.3))
    );

    // Advect the UV coordinates
    vec2 advected = uv + vel * 0.05;

    // Layer multiple noise scales for turbulence appearance
    float n1 = gradientNoise(advected * 4.0 + time * 0.2);
    float n2 = gradientNoise(advected * 8.0 - time * 0.15) * 0.5;
    float n3 = gradientNoise(advected * 16.0 + time * 0.1) * 0.25;
    float turbulence = n1 + n2 + n3;

    // Color map
    vec3 color = mix(
        vec3(0.0, 0.2, 0.4),  // Deep blue
        vec3(0.1, 0.6, 0.9),  // Light blue
        smoothstep(-0.5, 0.5, turbulence)
    );
    return color;
}
```
