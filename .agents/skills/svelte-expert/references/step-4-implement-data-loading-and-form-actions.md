### Step 4: Implement Data Loading and Form Actions

**Server load functions (+page.server.ts)**:

```ts
// src/routes/blog/+page.server.ts
import type { PageServerLoad } from "./$types";
import { db } from "$lib/server/db";

export const load: PageServerLoad = async ({ url, depends }) => {
  const page = parseInt(url.searchParams.get("page") ?? "1", 10);
  const limit = 10;

  // depends() registers a custom invalidation key
  depends("app:posts");

  const [posts, total] = await Promise.all([
    db.post.findMany({
      skip: (page - 1) * limit,
      take: limit,
      orderBy: { publishedAt: "desc" },
      select: { slug: true, title: true, excerpt: true, publishedAt: true },
    }),
    db.post.count(),
  ]);

  return {
    posts,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
};
```

**Dynamic route load with error handling**:

```ts
// src/routes/blog/[slug]/+page.server.ts
import { error } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { db } from "$lib/server/db";

export const load: PageServerLoad = async ({ params }) => {
  const post = await db.post.findUnique({
    where: { slug: params.slug },
  });

  if (!post) {
    error(404, { message: `Post "${params.slug}" not found` });
  }

  return { post };
};
```

**Form actions with progressive enhancement**:

```ts
// src/routes/blog/new/+page.server.ts
import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { db } from "$lib/server/db";
import { z } from "zod";

const CreatePostSchema = z.object({
  title: z.string().min(1, "Title is required").max(200),
  content: z.string().min(10, "Content must be at least 10 characters"),
  published: z.boolean().default(false),
});

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) {
    redirect(302, "/login");
  }
  return {};
};

export const actions = {
  default: async ({ request, locals }) => {
    const formData = await request.formData();

    const parsed = CreatePostSchema.safeParse({
      title: formData.get("title"),
      content: formData.get("content"),
      published: formData.has("published"),
    });

    if (!parsed.success) {
      return fail(400, {
        errors: parsed.error.flatten().fieldErrors,
        values: {
          title: formData.get("title") as string,
          content: formData.get("content") as string,
        },
      });
    }

    const post = await db.post.create({
      data: {
        ...parsed.data,
        slug: parsed.data.title.toLowerCase().replace(/\s+/g, "-"),
        authorId: locals.user!.id,
      },
    });

    redirect(303, `/blog/${post.slug}`);
  },
} satisfies Actions;
```

**Form component with progressive enhancement**:

```svelte
<!-- src/routes/blog/new/+page.svelte -->
<script lang="ts">
  import { enhance } from "$app/forms";
  import type { ActionData } from "./$types";

  let { form }: { form: ActionData } = $props();
  let submitting = $state(false);
</script>

<h1>New Blog Post</h1>

<form
  method="POST"
  use:enhance={() => {
    submitting = true;
    return async ({ update }) => {
      submitting = false;
      await update();
    };
  }}
>
  <label for="title">Title</label>
  <input
    id="title"
    name="title"
    value={form?.values?.title ?? ""}
    required
    aria-invalid={form?.errors?.title ? "true" : undefined}
    aria-describedby={form?.errors?.title ? "title-error" : undefined}
  />
  {#if form?.errors?.title}
    <p id="title-error" class="error">{form.errors.title[0]}</p>
  {/if}

  <label for="content">Content</label>
  <textarea
    id="content"
    name="content"
    required
    aria-invalid={form?.errors?.content ? "true" : undefined}
    aria-describedby={form?.errors?.content ? "content-error" : undefined}
  >{form?.values?.content ?? ""}</textarea>
  {#if form?.errors?.content}
    <p id="content-error" class="error">{form.errors.content[0]}</p>
  {/if}

  <label>
    <input type="checkbox" name="published" />
    Publish immediately
  </label>

  <button type="submit" disabled={submitting}>
    {submitting ? "Creating..." : "Create Post"}
  </button>
</form>
```

**Streaming with promises in load functions**:

```ts
// src/routes/dashboard/+page.server.ts
import type { PageServerLoad } from "./$types";
import { db } from "$lib/server/db";

export const load: PageServerLoad = async ({ locals }) => {
  // Return fast data immediately, stream slow data
  const quickStats = await db.stats.getQuick(locals.user!.id);

  return {
    stats: quickStats,
    // These promises stream to the client as they resolve
    recentActivity: db.activity.findRecent(locals.user!.id),
    recommendations: db.recommendations.generate(locals.user!.id),
  };
};
```

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<script lang="ts">
  import type { PageData } from "./$types";

  let { data }: { data: PageData } = $props();
</script>

<h1>Dashboard</h1>

<!-- Immediately available -->
<div class="stats">
  <p>Total posts: {data.stats.postCount}</p>
  <p>Total views: {data.stats.viewCount}</p>
</div>

<!-- Streamed in when ready -->
{#await data.recentActivity}
  <div class="skeleton">Loading recent activity...</div>
{:then activity}
  <ul>
    {#each activity as item}
      <li>{item.description} - {item.timestamp}</li>
    {/each}
  </ul>
{:catch error}
  <p class="error">Failed to load activity: {error.message}</p>
{/await}

{#await data.recommendations}
  <div class="skeleton">Generating recommendations...</div>
{:then recs}
  <ul>
    {#each recs as rec}
      <li>{rec.title}</li>
    {/each}
  </ul>
{:catch}
  <p class="error">Could not generate recommendations.</p>
{/await}
```
