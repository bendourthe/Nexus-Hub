### Step 8: Deployment and Adapters

**Adapter selection guide**:

| Target              | Adapter               | Install command                    |
| ------------------- | --------------------- | ---------------------------------- |
| Static hosting      | (none, default)       | N/A                                |
| Node.js server      | `@astrojs/node`       | `npx astro add node`              |
| Vercel              | `@astrojs/vercel`     | `npx astro add vercel`            |
| Netlify             | `@astrojs/netlify`    | `npx astro add netlify`           |
| Cloudflare Workers  | `@astrojs/cloudflare` | `npx astro add cloudflare`        |
| Deno                | `@astrojs/deno`       | `npx astro add deno`              |

**Static deployment (default)**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://example.com",
  output: "static", // Pre-render all pages at build time
  build: {
    assets: "_assets", // Custom assets directory in output
  },
  compressHTML: true, // Minify HTML output
});
```

```bash
# Build and preview locally
npx astro build    # Outputs to dist/
npx astro preview  # Serves the built site locally
```

**Node.js adapter (standalone server)**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import node from "@astrojs/node";

export default defineConfig({
  output: "server",
  adapter: node({
    mode: "standalone", // Self-contained server (or "middleware" for Express)
  }),
  server: {
    host: "0.0.0.0",
    port: 4321,
  },
});
```

```dockerfile
# Dockerfile for Node.js standalone deployment
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

ENV HOST=0.0.0.0
ENV PORT=4321
EXPOSE 4321

CMD ["node", "./dist/server/entry.mjs"]
```

**Vercel adapter**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import vercel from "@astrojs/vercel";

export default defineConfig({
  output: "server", // or "hybrid" for mostly static + some SSR
  adapter: vercel({
    webAnalytics: { enabled: true },
    imageService: true, // Use Vercel image optimization
    isr: {
      expiration: 60, // ISR: revalidate every 60 seconds
    },
  }),
});
```

**Netlify adapter**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import netlify from "@astrojs/netlify";

export default defineConfig({
  output: "server",
  adapter: netlify({
    edgeMiddleware: true, // Run middleware at the edge
    imageCDN: true,       // Use Netlify Image CDN
  }),
});
```

**Cloudflare adapter**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import cloudflare from "@astrojs/cloudflare";

export default defineConfig({
  output: "server",
  adapter: cloudflare({
    platformProxy: {
      enabled: true, // Access KV, D1, R2 bindings via platform.env
    },
  }),
});
```

```ts
// src/pages/api/kv-example.ts
// Accessing Cloudflare bindings in API routes
import type { APIRoute } from "astro";

export const GET: APIRoute = async ({ locals }) => {
  const runtime = locals.runtime;
  const value = await runtime.env.MY_KV_NAMESPACE.get("key");
  return new Response(JSON.stringify({ value }), {
    headers: { "Content-Type": "application/json" },
  });
};
```

**Environment variables**:

```ts
// astro.config.mjs - define expected environment variables
import { defineConfig, envField } from "astro/config";

export default defineConfig({
  env: {
    schema: {
      // Server-only (never exposed to client)
      DATABASE_URL: envField.string({
        context: "server",
        access: "secret",
      }),
      API_KEY: envField.string({
        context: "server",
        access: "secret",
      }),
      // Public (available in client JS)
      PUBLIC_SITE_URL: envField.string({
        context: "client",
        access: "public",
        default: "http://localhost:4321",
      }),
    },
  },
});
```

```astro
---
// Accessing environment variables in Astro components
// Server-side (frontmatter): use import.meta.env
const apiKey = import.meta.env.API_KEY;           // Server secret
const siteUrl = import.meta.env.PUBLIC_SITE_URL;  // Public variable

// Convention: PUBLIC_ prefix exposes to client bundles
// Variables without PUBLIC_ prefix are server-only
---

<p>Site: {siteUrl}</p>

<script>
  // Client-side: only PUBLIC_ variables are available
  const url = import.meta.env.PUBLIC_SITE_URL;
  console.log(url);
  // import.meta.env.API_KEY would be undefined here
</script>
```

**Production configuration checklist**:

```ts
// astro.config.mjs - production-ready configuration
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import mdx from "@astrojs/mdx";
import react from "@astrojs/react";
import node from "@astrojs/node";

export default defineConfig({
  site: "https://example.com",
  output: "hybrid",
  adapter: node({ mode: "standalone" }),

  integrations: [
    react(),
    mdx(),
    sitemap({
      filter: (page) => !page.includes("/admin/"),
    }),
  ],

  image: {
    domains: ["images.unsplash.com"],
  },

  prefetch: {
    defaultStrategy: "hover",
  },

  compressHTML: true,

  vite: {
    build: {
      cssMinify: true,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom"],
          },
        },
      },
    },
    ssr: {
      noExternal: [], // Add packages that need to be bundled for SSR
    },
  },

  security: {
    checkOrigin: true, // CSRF protection for form submissions
  },
});
```
