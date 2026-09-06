### Step 6: Data Fetching and API Routes

**Fetch data in frontmatter** (runs at build time for static, request time for SSR):

```astro
---
// src/pages/users.astro
import BaseLayout from "../layouts/BaseLayout.astro";

interface User {
  id: number;
  name: string;
  email: string;
}

// Top-level await is supported in Astro frontmatter
const response = await fetch("https://jsonplaceholder.typicode.com/users");
if (!response.ok) {
  throw new Error(`Failed to fetch users: ${response.status}`);
}
const users: User[] = await response.json();
---

<BaseLayout title="Users">
  <h1>Users</h1>
  <ul>
    {users.map((user) => (
      <li>
        <strong>{user.name}</strong> ({user.email})
      </li>
    ))}
  </ul>
</BaseLayout>
```

**API endpoints** (server-side route handlers):

```ts
// src/pages/api/search.ts
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

export const GET: APIRoute = async ({ url }) => {
  const query = url.searchParams.get("q")?.toLowerCase();
  if (!query || query.length < 2) {
    return new Response(JSON.stringify({ error: "Query too short" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const posts = await getCollection("blog", ({ data }) => !data.draft);
  const results = posts
    .filter(
      (post) =>
        post.data.title.toLowerCase().includes(query) ||
        post.data.description.toLowerCase().includes(query)
    )
    .map((post) => ({
      slug: post.slug,
      title: post.data.title,
      description: post.data.description,
    }));

  return new Response(JSON.stringify({ results }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json();

  // Validate input
  if (!body.email || typeof body.email !== "string") {
    return new Response(JSON.stringify({ error: "Email required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  // Process subscription (e.g., save to database)
  // await db.subscribers.create({ email: body.email });

  return new Response(JSON.stringify({ success: true }), {
    status: 201,
    headers: { "Content-Type": "application/json" },
  });
};
```

**Middleware** (for SSR/hybrid mode):

```ts
// src/middleware.ts
import { defineMiddleware, sequence } from "astro:middleware";

const authMiddleware = defineMiddleware(async (context, next) => {
  const { cookies, redirect, url } = context;

  // Skip auth for public routes
  const publicPaths = ["/", "/login", "/api/auth"];
  if (publicPaths.some((path) => url.pathname.startsWith(path))) {
    return next();
  }

  const sessionToken = cookies.get("session")?.value;
  if (!sessionToken) {
    return redirect("/login?returnTo=" + encodeURIComponent(url.pathname));
  }

  // Validate session and attach user to locals
  try {
    const user = await validateSession(sessionToken);
    context.locals.user = user;
  } catch {
    cookies.delete("session", { path: "/" });
    return redirect("/login");
  }

  return next();
});

const loggingMiddleware = defineMiddleware(async (context, next) => {
  const start = performance.now();
  const response = await next();
  const duration = (performance.now() - start).toFixed(2);
  console.log(`${context.request.method} ${context.url.pathname} - ${duration}ms`);
  return response;
});

// Chain middleware in order
export const onRequest = sequence(loggingMiddleware, authMiddleware);
```

**Type-safe locals** (define in `env.d.ts`):

```ts
// src/env.d.ts
/// <reference types="astro/client" />

interface User {
  id: string;
  name: string;
  role: "admin" | "user";
}

declare namespace App {
  interface Locals {
    user?: User;
  }
}
```

**Authentication pattern with cookies**:

```ts
// src/pages/api/auth/login.ts
import type { APIRoute } from "astro";

export const POST: APIRoute = async ({ request, cookies, redirect }) => {
  const formData = await request.formData();
  const email = formData.get("email")?.toString();
  const password = formData.get("password")?.toString();

  if (!email || !password) {
    return new Response("Missing credentials", { status: 400 });
  }

  // Verify credentials against your auth provider
  const user = await authenticateUser(email, password);
  if (!user) {
    return new Response("Invalid credentials", { status: 401 });
  }

  // Set session cookie
  const sessionToken = await createSession(user.id);
  cookies.set("session", sessionToken, {
    path: "/",
    httpOnly: true,
    secure: import.meta.env.PROD,
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });

  return redirect("/dashboard");
};
```
