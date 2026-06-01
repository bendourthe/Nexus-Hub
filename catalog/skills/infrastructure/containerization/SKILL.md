---
name: containerization
description: Container best practices including Dockerfile optimization, multi-stage builds, image security scanning, and Docker Compose patterns. Use when containerizing applications, optimizing image size, or setting up local development environments.
summary_l0: "Containerize applications with optimized Dockerfiles, multi-stage builds, and security scanning"
overview_l1: "This skill provides comprehensive guidance on building production-ready containers, including Dockerfile optimization, multi-stage builds, image security, Docker Compose patterns, and CI/CD integration. Use it when containerizing applications, optimizing image size, setting up local development environments, implementing multi-stage builds, scanning images for vulnerabilities, designing Docker Compose configurations, or integrating containers into CI/CD pipelines. Key capabilities include Dockerfile optimization (layer caching, multi-stage builds, minimal base images), security scanning and hardening, Docker Compose patterns for development and production, volume and network management, health check configuration, and CI/CD container workflow design. The expected output is optimized Dockerfiles, Docker Compose configurations, and security-scanned container images ready for production. Trigger phrases: Docker, Dockerfile, container, multi-stage build, Docker Compose, image optimization, container security, containerize."
---

# Containerization

Comprehensive guidance on building production-ready containers, including Dockerfile optimization, multi-stage builds, image security, Docker Compose patterns for development and production, and CI/CD integration for container workflows.

## When to Use This Skill

Use this skill for:

- Writing optimized Dockerfiles with multi-stage builds
- Reducing container image size (slim bases, distroless)
- Securing containers (non-root users, read-only filesystems, vulnerability scanning)
- Setting up Docker Compose for local development
- Configuring healthchecks, resource limits, and networking
- Building container CI/CD pipelines with image scanning
- Managing container registries and tagging strategies
- Debugging containerized applications

**Trigger phrases**: "Docker", "Dockerfile", "container", "docker-compose", "multi-stage build", "container image", "image size", "distroless", "Trivy", "container security", "docker build", "containerize"

## What This Skill Does

Provides production-ready containerization patterns including:

- **Dockerfile Best Practices**: Layer caching, multi-stage builds, build arguments
- **Base Image Selection**: Slim, Alpine, distroless, scratch, and when to use each
- **Security Hardening**: Non-root execution, read-only filesystems, secret handling, scanning
- **Docker Compose**: Service orchestration, networking, volumes, profiles, healthchecks
- **Development Workflows**: Hot reload, debugging, and test execution in containers
- **CI/CD Integration**: Automated builds, vulnerability scanning, registry management

## Instructions

### Step 1: Choose the Right Base Image

**Base Image Decision Matrix**:

```
┌────────────────────┬──────────────┬──────────────┬──────────────────────────┐
│ Base Image         │ Size         │ Shell/Tools  │ Best For                 │
├────────────────────┼──────────────┼──────────────┼──────────────────────────┤
│ ubuntu:24.04       │ ~75 MB       │ Full         │ Apps needing system libs │
│ debian:bookworm-   │ ~80 MB       │ Full         │ Broad compatibility      │
│   slim             │              │              │                          │
│ alpine:3.19        │ ~7 MB        │ BusyBox      │ Minimal images, Go, Rust │
│ distroless         │ ~3-20 MB     │ None         │ Production (no debug)    │
│ scratch            │ 0 MB         │ None         │ Static binaries only     │
│ node:20-slim       │ ~200 MB      │ Partial      │ Node.js applications     │
│ python:3.12-slim   │ ~150 MB      │ Partial      │ Python applications      │
│ golang:1.22-alpine │ ~250 MB      │ Full (build) │ Go build stage only      │
└────────────────────┴──────────────┴──────────────┴──────────────────────────┘
```

### Step 2: Write Optimized Multi-Stage Dockerfiles

**Python Application**:

```dockerfile
# ============================================
# Stage 1: Build dependencies
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies (cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# Stage 2: Production image
# ============================================
FROM python:3.12-slim AS production

# Security: create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy only installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser alembic/ ./alembic/
COPY --chown=appuser:appuser alembic.ini .

# Security: non-root user
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

# Use exec form (PID 1 signal handling)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Node.js Application**:

```dockerfile
# ============================================
# Stage 1: Install dependencies
# ============================================
FROM node:20-slim AS deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

# ============================================
# Stage 2: Build
# ============================================
FROM node:20-slim AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# ============================================
# Stage 3: Production
# ============================================
FROM node:20-slim AS production

# Security: non-root user (node user exists in node images)
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV NODE_ENV=production

# Copy production dependencies and built code
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./

USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => { process.exit(r.statusCode === 200 ? 0 : 1) })"

EXPOSE 3000

# dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

**Go Application (minimal final image)**:

```dockerfile
# ============================================
# Stage 1: Build
# ============================================
FROM golang:1.22-alpine AS build

RUN apk add --no-cache git ca-certificates

WORKDIR /src

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build static binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s -X main.version=$(git describe --tags --always)" \
    -o /app ./cmd/server

# ============================================
# Stage 2: Minimal production image
# ============================================
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=build /app /app

EXPOSE 8080
USER nonroot:nonroot

ENTRYPOINT ["/app"]
```

**Rust Application**:

```dockerfile
# ============================================
# Stage 1: Build with cargo-chef for caching
# ============================================
FROM rust:1.76-slim AS planner
RUN cargo install cargo-chef
WORKDIR /app
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM rust:1.76-slim AS builder
RUN cargo install cargo-chef
WORKDIR /app

# Cache dependencies (only re-runs when Cargo.toml/lock changes)
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --recipe-path recipe.json

# Build application
COPY . .
RUN cargo build --release

# ============================================
# Stage 2: Minimal runtime
# ============================================
FROM gcr.io/distroless/cc-debian12:nonroot

COPY --from=builder /app/target/release/myapp /

USER nonroot:nonroot
EXPOSE 8080

ENTRYPOINT ["/myapp"]
```

### Step 3: Secure Container Images

**Security Hardening Checklist**:

```dockerfile
# 1. Run as non-root
USER 1001:1001

# 2. Read-only root filesystem (combine with tmpfs for writable dirs)
# docker run --read-only --tmpfs /tmp myapp

# 3. Drop all capabilities, add only what is needed
# docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp

# 4. No new privileges
# docker run --security-opt=no-new-privileges myapp

# 5. Never store secrets in images
# WRONG: COPY secrets.json /app/secrets.json
# CORRECT: Use runtime secrets (env vars, mounted volumes, or secret managers)

# 6. Pin base image digests for reproducibility
FROM python:3.12-slim@sha256:abc123...
```

**Vulnerability Scanning with Trivy**:

```bash
# Scan a local image
trivy image myapp:latest

# Scan and fail on critical/high severity
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:latest

# Scan a Dockerfile (misconfiguration check)
trivy config Dockerfile

# Generate SARIF report for GitHub Security tab
trivy image --format sarif --output trivy.sarif myapp:latest

# Scan with an ignore file for accepted vulnerabilities
trivy image --ignorefile .trivyignore myapp:latest
```

**.trivyignore**:

```
# Accepted vulnerabilities with justification
CVE-2023-12345  # No impact: library not used in our code path
CVE-2023-67890  # Fixed in next base image update (tracked in JIRA-456)
```

**Scanning with Grype**:

```bash
# Install and scan
grype myapp:latest

# Fail on high or critical
grype myapp:latest --fail-on high

# Output as JSON for CI processing
grype myapp:latest -o json > grype-results.json
```

### Step 4: Set Up Docker Compose for Development

**Full-Stack Development Environment**:

```yaml
# docker-compose.yaml
services:
  # ============================================
  # Application (with hot reload)
  # ============================================
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development    # Use dev stage of multi-stage build
    ports:
      - "3000:3000"
      - "9229:9229"          # Node.js debugger
    volumes:
      - ./src:/app/src:cached       # Mount source for hot reload
      - ./package.json:/app/package.json
      - node_modules:/app/node_modules  # Named volume (not host mount)
    environment:
      NODE_ENV: development
      DATABASE_URL: postgres://app:secret@postgres:5432/appdb
      REDIS_URL: redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 15s
    profiles: ["app"]

  # ============================================
  # Database
  # ============================================
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: appdb
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/01-init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ============================================
  # Cache
  # ============================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ============================================
  # Observability (optional profile)
  # ============================================
  grafana:
    image: grafana/grafana:10.3.0
    ports:
      - "3001:3000"
    profiles: ["observability"]

  prometheus:
    image: prom/prometheus:v2.49.0
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    profiles: ["observability"]

volumes:
  postgres-data:
  node_modules:
```

**Docker Compose Profiles**:

```bash
# Start only infrastructure (DB, cache)
docker compose up -d postgres redis

# Start app + infrastructure
docker compose --profile app up -d

# Start everything including observability
docker compose --profile app --profile observability up -d

# Run one-off commands
docker compose run --rm app npm test
docker compose run --rm app npm run migrate
```

### Step 5: Optimize Build Performance

**Layer Caching Strategy**:

```dockerfile
# WRONG: Invalidates cache on ANY source change
COPY . .
RUN pip install -r requirements.txt

# CORRECT: Dependencies cached separately from source code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

**.dockerignore (essential)**:

```
# Version control
.git
.gitignore

# Dependencies (installed in container)
node_modules
__pycache__
*.pyc
.venv
vendor

# Build artifacts
dist
build
target
*.o
*.a

# IDE and editor
.vscode
.idea
*.swp
*.swo

# Environment and secrets
.env
.env.*
*.pem
*.key

# Documentation and tests (not needed in production image)
docs
*.md
tests
__tests__
coverage
.pytest_cache

# Docker
Dockerfile*
docker-compose*
.dockerignore

# CI/CD
.github
.gitlab-ci.yml
Jenkinsfile
```

**BuildKit Features**:

```bash
# Enable BuildKit (default in Docker 23+)
export DOCKER_BUILDKIT=1

# Build with cache mount (keeps pip/npm cache between builds)
# In Dockerfile:
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Parallel multi-stage builds
docker build --target production .

# Build with SSH agent forwarding (for private repos)
docker build --ssh default .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t myapp:latest .
```

### Step 6: Implement Container CI/CD

**GitHub Actions Container Pipeline**:

```yaml
# .github/workflows/container.yml
name: Container Build & Push

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          target: production
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          severity: CRITICAL,HIGH

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trivy-results.sarif
```

### Step 7: Debug Containers

**Common Debugging Commands**:

```bash
# Inspect a running container
docker exec -it <container> sh

# View logs with timestamps
docker logs --timestamps --tail 100 <container>

# Inspect container metadata
docker inspect <container> | jq '.[0].State'

# Check resource usage
docker stats <container>

# Copy files from container for inspection
docker cp <container>:/app/logs/error.log ./error.log

# Run a temporary debug sidecar (for distroless images)
docker run --rm -it --pid=container:<container> --net=container:<container> \
    nicolaka/netshoot

# Inspect image layers
docker history myapp:latest
dive myapp:latest  # Interactive layer explorer
```

## Best Practices

- **Use multi-stage builds** to separate build tools from the runtime image
- **Pin base image versions** with digests for reproducible builds
- **Run as non-root** and drop all capabilities by default
- **Order Dockerfile instructions** from least to most frequently changing for optimal layer caching
- **Use .dockerignore** to exclude secrets, tests, docs, and version control from the build context
- **Set explicit healthchecks** in Dockerfiles for orchestrator integration
- **Use exec form** for CMD/ENTRYPOINT to ensure PID 1 signal handling
- **Scan images for vulnerabilities** in CI before pushing to a registry
- **Use named volumes** for dependencies in development (not host mounts)
- **Tag images with SHA and semver**; never rely solely on `latest`
- **Limit container resources** (memory, CPU) in Compose and orchestration configs

## Common Patterns

### Pattern 1: Development vs Production Stages

```dockerfile
# Shared base
FROM node:20-slim AS base
WORKDIR /app
COPY package.json package-lock.json ./

# Development stage (hot reload, dev tools)
FROM base AS development
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

# Production stage (optimized)
FROM base AS production
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist
USER node
CMD ["node", "dist/server.js"]
```

### Pattern 2: Init Container for Migrations

```yaml
# docker-compose.yaml
services:
  migrate:
    build: .
    command: ["npm", "run", "migrate"]
    depends_on:
      postgres:
        condition: service_healthy
    restart: "no"

  app:
    build: .
    depends_on:
      migrate:
        condition: service_completed_successfully
```

### Pattern 3: Secrets via Build Secrets (BuildKit)

```dockerfile
# Mount a secret at build time (never stored in a layer)
RUN --mount=type=secret,id=npmrc,target=/app/.npmrc \
    npm ci --omit=dev
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

## Quality Checklist

- [ ] Multi-stage build separates build dependencies from runtime
- [ ] Base image is pinned (tag + digest) and minimal (slim/distroless)
- [ ] Container runs as non-root with dropped capabilities
- [ ] .dockerignore excludes secrets, tests, docs, and .git
- [ ] Healthcheck defined in Dockerfile or Compose
- [ ] CMD/ENTRYPOINT uses exec form (JSON array)
- [ ] No secrets baked into the image (use runtime injection)
- [ ] Vulnerability scanning runs in CI and blocks on critical findings
- [ ] Image tagged with SHA and semantic version
- [ ] Resource limits (memory, CPU) specified in orchestration config
- [ ] Layer order optimized for cache efficiency
- [ ] Development Compose uses volumes for hot reload

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Running as root inside the container is fine, it's isolated" | A container escape from a root process gets root on the host; a non-root USER and a read-only root filesystem are what contain the blast radius when the runtime has a CVE. |
| "I'll use the full base image, multi-stage is over-engineering" | A full base image ships compilers, package managers, and shells the running app never needs, every one an attack-surface and image-size cost; a multi-stage build that copies only the artifact into a slim or distroless final stage removes them. |
| "COPYing the .env or build secret into a layer is convenient" | Secrets baked into a layer persist in the image history even if a later layer deletes them; anyone who pulls the image can extract them. Use build secrets / mounts, never COPY. |
| "Scanning the image is a release-day step" | Vulnerable base layers compound the longer they ship; running Trivy (or equivalent) in the build pipeline catches a critical CVE before the image is ever promoted, not after it is in production. |

## Verification

- [ ] The Dockerfile uses a multi-stage build; the final stage contains only the runtime artifact and its dependencies.
- [ ] The container runs as a non-root USER and, where feasible, a read-only root filesystem.
- [ ] No secrets are COPYed into any layer; image history is clean (`docker history` shows no secret values).
- [ ] The image passes a vulnerability scan in CI: `trivy image <tag>` reports no unaddressed CRITICAL findings.
- [ ] A HEALTHCHECK is defined and resource limits are set for the service.

## Related Skills

- [[cicd-architect]] -- container build pipelines and registry automation
- [[kubernetes-expert]] -- deploying containers to Kubernetes
- [[observability-setup]] -- monitoring containerized applications
- [[security-review]] -- container security assessment

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
