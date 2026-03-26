# Next.js Data Fetching Patterns Reference

Quick-lookup guide for App Router data fetching, caching, and revalidation strategies. Use alongside the main nextjs-expert skill when designing data pipelines.

## Fetching Decision Matrix

| Scenario | Approach | Cache | Revalidation |
|----------|----------|-------|-------------|
| Static content (docs, blog) | `fetch()` in Server Component | `force-cache` (default) | `revalidate: 3600` or on-demand |
| User-specific data | `fetch()` with `cache: "no-store"` | None | Every request |
| Frequently changing data | `fetch()` with `next: { revalidate: 60 }` | Time-based | Every 60 seconds |
| On-demand after mutation | Server Action + `revalidatePath`/`revalidateTag` | Tag-based | After mutation |
| Client-side interactive | `useSWR` or `@tanstack/react-query` | Client cache | Stale-while-revalidate |

## Server Component Data Fetching

```tsx
// app/dashboard/page.tsx
// This fetch is automatically deduped if called in multiple components
async function getMetrics(): Promise<Metrics> {
  const res = await fetch("https://api.example.com/metrics", {
    next: { revalidate: 300, tags: ["metrics"] },
  });
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export default async function DashboardPage() {
  const metrics = await getMetrics();
  return <MetricsGrid data={metrics} />;
}
```

## Parallel Data Fetching

```tsx
// app/dashboard/page.tsx
export default async function DashboardPage() {
  // Parallel fetches (not waterfall)
  const [metrics, notifications, userProfile] = await Promise.all([
    getMetrics(),
    getNotifications(),
    getUserProfile(),
  ]);

  return (
    <div>
      <MetricsGrid data={metrics} />
      <NotificationList items={notifications} />
      <ProfileCard user={userProfile} />
    </div>
  );
}
```

## Streaming with Suspense

```tsx
// app/dashboard/page.tsx
import { Suspense } from "react";

export default function DashboardPage() {
  return (
    <div>
      {/* Renders immediately */}
      <h1>Dashboard</h1>

      {/* Streams in when ready */}
      <Suspense fallback={<MetricsSkeleton />}>
        <MetricsSection />
      </Suspense>

      <Suspense fallback={<ActivitySkeleton />}>
        <RecentActivity />
      </Suspense>
    </div>
  );
}

// Each section fetches its own data
async function MetricsSection() {
  const metrics = await getMetrics(); // Slow API
  return <MetricsGrid data={metrics} />;
}
```

## Server Actions for Mutations

```tsx
// app/posts/actions.ts
"use server";

import { revalidateTag } from "next/cache";
import { redirect } from "next/navigation";

export async function createPost(formData: FormData): Promise<void> {
  const title = formData.get("title") as string;
  const content = formData.get("content") as string;

  const res = await fetch("https://api.example.com/posts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content }),
  });

  if (!res.ok) {
    throw new Error("Failed to create post");
  }

  revalidateTag("posts");
  redirect("/posts");
}
```

```tsx
// app/posts/new/page.tsx
import { createPost } from "../actions";

export default function NewPostPage() {
  return (
    <form action={createPost}>
      <input name="title" required />
      <textarea name="content" required />
      <button type="submit">Publish</button>
    </form>
  );
}
```

## On-Demand Revalidation

```tsx
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from "next/cache";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const { tag, path, secret } = await request.json();

  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (tag) {
    revalidateTag(tag);
    return NextResponse.json({ revalidated: true, tag });
  }

  if (path) {
    revalidatePath(path);
    return NextResponse.json({ revalidated: true, path });
  }

  return NextResponse.json({ error: "Missing tag or path" }, { status: 400 });
}
```

## Caching Strategy Quick Reference

| API | Default Cache | Override |
|-----|--------------|---------|
| `fetch()` in Server Component | `force-cache` | `cache: "no-store"` or `next: { revalidate: N }` |
| Route Handlers (GET) | Cached | `export const dynamic = "force-dynamic"` |
| Route Handlers (POST/PUT/DELETE) | Not cached | N/A |
| Server Actions | Not cached | Call `revalidatePath`/`revalidateTag` |
| `unstable_cache()` | Cached with tags | `revalidateTag()` |
| `cookies()` / `headers()` | Opts out of cache | N/A (dynamic by nature) |
