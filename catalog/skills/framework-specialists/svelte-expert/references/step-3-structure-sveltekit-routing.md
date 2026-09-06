### Step 3: Structure SvelteKit Routing

**Standard SvelteKit file structure**:

```
src/
  routes/
    +page.svelte              # Home page (/)
    +layout.svelte            # Root layout
    +layout.server.ts         # Root layout server load
    +error.svelte             # Root error page
    about/
      +page.svelte            # /about
    blog/
      +page.svelte            # /blog (list)
      +page.server.ts         # Blog list data loading
      [slug]/
        +page.svelte          # /blog/:slug (dynamic)
        +page.server.ts       # Single post data loading
    dashboard/
      +layout.svelte          # Dashboard layout (nested)
      +layout.server.ts       # Dashboard auth check
      +page.svelte            # /dashboard
      settings/
        +page.svelte          # /dashboard/settings
    api/
      health/
        +server.ts            # GET /api/health
      users/
        +server.ts            # GET/POST /api/users
        [id]/
          +server.ts          # GET/PUT/DELETE /api/users/:id
    (marketing)/              # Route group (no URL segment)
      pricing/
        +page.svelte          # /pricing
      contact/
        +page.svelte          # /contact
  lib/
    server/                   # Server-only modules ($lib/server/)
      db.ts
      auth.ts
    components/               # Shared components ($lib/components/)
    stores/                   # Shared state ($lib/stores/)
```

**Root layout with navigation**:

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
  import type { LayoutData } from "./$types";
  import { page } from "$app/stores";

  let { data, children }: { data: LayoutData; children: any } = $props();
</script>

<div class="app">
  <header>
    <nav aria-label="Main navigation">
      <a href="/" class:active={$page.url.pathname === "/"}>Home</a>
      <a href="/blog" class:active={$page.url.pathname.startsWith("/blog")}>Blog</a>
      <a href="/dashboard" class:active={$page.url.pathname.startsWith("/dashboard")}>
        Dashboard
      </a>
      {#if data.user}
        <span>Welcome, {data.user.name}</span>
      {:else}
        <a href="/login">Sign In</a>
      {/if}
    </nav>
  </header>
  <main>
    {@render children()}
  </main>
  <footer>
    <p>Built with SvelteKit</p>
  </footer>
</div>

<style>
  .active {
    font-weight: bold;
    text-decoration: underline;
  }
</style>
```

**Dynamic route with params and error handling**:

```svelte
<!-- src/routes/blog/[slug]/+page.svelte -->
<script lang="ts">
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();
</script>

<svelte:head>
  <title>{data.post.title} | My Blog</title>
  <meta name="description" content={data.post.excerpt} />
</svelte:head>

<article>
  <h1>{data.post.title}</h1>
  <time datetime={data.post.publishedAt}>
    {new Date(data.post.publishedAt).toLocaleDateString()}
  </time>
  <div class="content">
    {@html data.post.htmlContent}
  </div>
</article>
```

**Route groups and layout resets**:

```svelte
<!-- src/routes/(marketing)/+layout.svelte -->
<script lang="ts">
  // Marketing pages get a different layout than the dashboard
  let { children }: { children: any } = $props();
</script>

<div class="marketing-layout">
  <header class="marketing-header">
    <a href="/">Brand Logo</a>
    <a href="/pricing">Pricing</a>
    <a href="/contact">Contact</a>
  </header>
  {@render children()}
</div>
```

**API route handlers (+server.ts)**:

```ts
// src/routes/api/users/+server.ts
import { json, error } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { db } from "$lib/server/db";

export const GET: RequestHandler = async ({ url }) => {
  const page = parseInt(url.searchParams.get("page") ?? "1", 10);
  const limit = parseInt(url.searchParams.get("limit") ?? "20", 10);

  const users = await db.user.findMany({
    skip: (page - 1) * limit,
    take: limit,
  });

  return json({ data: users, page, limit });
};

export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();

  if (!body.email || !body.name) {
    error(400, { message: "Name and email are required" });
  }

  const user = await db.user.create({ data: body });
  return json(user, { status: 201 });
};
```
