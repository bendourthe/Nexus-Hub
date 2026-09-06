### Step 2: Signed Distance Functions (SDFs)

A signed distance function returns the shortest distance from a point to the surface of an object. Negative values indicate the point is inside the object. SDFs are the building blocks for ray marched scenes.

**SDF Primitives**:

```glsl
// Sphere centered at origin with given radius
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

// Box centered at origin with half-extents b
float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

// Round box: box with rounded edges
float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b + r;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
}

// Torus centered at origin, lying in the XZ plane
// t.x = major radius, t.y = minor radius
float sdTorus(vec3 p, vec2 t) {
    vec2 q = vec2(length(p.xz) - t.x, p.y);
    return length(q) - t.y;
}

// Infinite cylinder along the Y axis
float sdCylinder(vec3 p, float r) {
    return length(p.xz) - r;
}

// Capped cylinder with height h and radius r
float sdCappedCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
}

// Plane with normal n (must be normalized) at height h
float sdPlane(vec3 p, vec3 n, float h) {
    return dot(p, n) + h;
}

// Capsule from point a to point b with radius r
float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h) - r;
}
```

**CSG (Constructive Solid Geometry) Operations**:

```glsl
// Union: combine two shapes (take the closer surface)
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

// Intersection: keep only the overlapping region
float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

// Subtraction: cut d2 out of d1
float opSubtraction(float d1, float d2) {
    return max(d1, -d2);
}

// Smooth union: blend two shapes with smooth transition
// k controls the blending radius (try 0.1 to 0.5)
float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

// Smooth subtraction
float opSmoothSubtraction(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 + d1) / k, 0.0, 1.0);
    return mix(d2, -d1, h) + k * h * (1.0 - h);
}

// Smooth intersection
float opSmoothIntersection(float d1, float d2, float k) {
    float h = clamp(0.5 - 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) + k * h * (1.0 - h);
}
```

**Domain Operations** (transform space, not geometry):

```glsl
// Infinite repetition along all axes with spacing s
float opRep(vec3 p, vec3 s) {
    vec3 q = mod(p + 0.5 * s, s) - 0.5 * s;
    return sdSphere(q, 0.25); // Replace with any SDF
}

// Limited repetition: repeat n times in each direction
float opRepLimited(vec3 p, vec3 s, vec3 n) {
    vec3 q = p - s * clamp(round(p / s), -n, n);
    return sdSphere(q, 0.25);
}

// Symmetry: mirror across the YZ plane
float opSymX(vec3 p) {
    p.x = abs(p.x);
    return sdBox(p - vec3(1.0, 0.0, 0.0), vec3(0.5));
}

// Twist around the Y axis
vec3 opTwist(vec3 p, float k) {
    float c = cos(k * p.y);
    float s = sin(k * p.y);
    mat2 m = mat2(c, -s, s, c);
    return vec3(m * p.xz, p.y);
}

// Bend along the X axis
vec3 opBend(vec3 p, float k) {
    float c = cos(k * p.x);
    float s = sin(k * p.x);
    mat2 m = mat2(c, -s, s, c);
    vec2 bent = m * p.xy;
    return vec3(bent, p.z);
}
```

**Complete SDF Scene Example**:

```glsl
// Scene: a sphere sitting on a plane with a smooth-blended torus
float map(vec3 p) {
    float ground = sdPlane(p, vec3(0.0, 1.0, 0.0), 0.0);
    float sphere = sdSphere(p - vec3(0.0, 1.0, 0.0), 1.0);
    float torus  = sdTorus(p - vec3(0.0, 1.0, 0.0), vec2(1.2, 0.3));
    float blob   = opSmoothUnion(sphere, torus, 0.3);
    return opUnion(ground, blob);
}
```
