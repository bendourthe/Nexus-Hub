### Step 6: Configure SvelteKit Hooks and Middleware

**Server hooks (src/hooks.server.ts)**:

```ts
// src/hooks.server.ts
import type { Handle, HandleFetch, HandleServerError } from "@sveltejs/kit";
import { db } from "$lib/server/db";
import { verifySession } from "$lib/server/auth";
import { sequence } from "@sveltejs/kit/hooks";

// Authentication hook
const authHandle: Handle = async ({ event, resolve }) => {
  const sessionToken = event.cookies.get("session");

  if (sessionToken) {
    try {
      const user = await verifySession(sessionToken);
      event.locals.user = user;
    } catch {
      // Invalid session; clear the cookie
      event.cookies.delete("session", { path: "/" });
    }
  }

  return resolve(event);
};

// Security headers hook
const securityHandle: Handle = async ({ event, resolve }) => {
  const response = await resolve(event);

  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=()"
  );

  return response;
};

// Protected routes hook
const protectedRoutes: Handle = async ({ event, resolve }) => {
  const protectedPaths = ["/dashboard", "/settings", "/admin"];
  const isProtected = protectedPaths.some((p) =>
    event.url.pathname.startsWith(p)
  );

  if (isProtected && !event.locals.user) {
    const redirectUrl = `/login?redirect=${encodeURIComponent(event.url.pathname)}`;
    return new Response(null, {
      status: 302,
      headers: { location: redirectUrl },
    });
  }

  if (event.url.pathname.startsWith("/admin")) {
    if (event.locals.user?.role !== "admin") {
      return new Response("Forbidden", { status: 403 });
    }
  }

  return resolve(event);
};

// Chain hooks with sequence
export const handle = sequence(authHandle, securityHandle, protectedRoutes);

// Modify outgoing fetch requests (e.g., attach auth headers to API calls)
export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
  if (request.url.startsWith("https://api.internal.example.com")) {
    request.headers.set(
      "Authorization",
      `Bearer ${event.locals.user?.apiToken ?? ""}`
    );
  }
  return fetch(request);
};

// Global error handler
export const handleError: HandleServerError = async ({ error, event, status, message }) => {
  const errorId = crypto.randomUUID();

  console.error(`[${errorId}] Unhandled error on ${event.url.pathname}:`, error);

  // Report to error tracking service
  // await reportError({ errorId, error, url: event.url.pathname });

  return {
    message: "An unexpected error occurred",
    errorId,
  };
};
```

**App.d.ts type declarations**:

```ts
// src/app.d.ts
declare global {
  namespace App {
    interface Error {
      message: string;
      errorId?: string;
    }
    interface Locals {
      user: {
        id: string;
        name: string;
        email: string;
        role: "admin" | "user";
        apiToken?: string;
      } | null;
    }
    interface PageData {
      user: App.Locals["user"];
    }
    interface PageState {}
    interface Platform {}
  }
}

export {};
```

**Environment variables**:

```ts
// Access public env variables (available on client and server)
import { PUBLIC_API_URL, PUBLIC_APP_NAME } from "$env/static/public";

// Access private env variables (server-only, build-time)
import { DATABASE_URL, JWT_SECRET } from "$env/static/private";

// Dynamic env variables (read at runtime, not inlined at build)
import { env } from "$env/dynamic/private";
const dbUrl = env.DATABASE_URL;

// SvelteKit will throw a build error if you try to import
// private env variables into client-side code
```

**Custom error page**:

```svelte
<!-- src/routes/+error.svelte -->
<script lang="ts">
  import { page } from "$app/stores";
</script>

<svelte:head>
  <title>Error {$page.status}</title>
</svelte:head>

<div class="error-page">
  <h1>{$page.status}</h1>
  <p>{$page.error?.message ?? "Something went wrong"}</p>
  {#if $page.error?.errorId}
    <p class="error-id">Error ID: {$page.error.errorId}</p>
  {/if}
  <a href="/">Go home</a>
</div>
```
