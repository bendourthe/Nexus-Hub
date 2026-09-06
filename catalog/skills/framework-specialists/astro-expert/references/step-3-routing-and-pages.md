### Step 3: Routing and Pages

**File-based routing rules**:

| File path                          | URL                 | Type             |
| ---------------------------------- | ------------------- | ---------------- |
| `src/pages/index.astro`           | `/`                 | Static page      |
| `src/pages/about.astro`           | `/about`            | Static page      |
| `src/pages/blog/[slug].astro`     | `/blog/:slug`       | Dynamic route    |
| `src/pages/blog/[...slug].astro`  | `/blog/*`           | Rest parameter   |
| `src/pages/[lang]/index.astro`    | `/:lang`            | i18n root        |
| `src/pages/api/search.ts`         | `/api/search`       | API endpoint     |

**Dynamic routes with `getStaticPaths`** (required for static output):

```astro
---
// src/pages/tags/[tag].astro
import { getCollection } from "astro:content";
import BaseLayout from "../../layouts/BaseLayout.astro";

export async function getStaticPaths() {
  const allPosts = await getCollection("blog", ({ data }) => !data.draft);

  // Extract unique tags
  const uniqueTags = [
    ...new Set(allPosts.flatMap((post) => post.data.tags)),
  ];

  return uniqueTags.map((tag) => ({
    params: { tag },
    props: {
      posts: allPosts.filter((post) => post.data.tags.includes(tag)),
    },
  }));
}

const { tag } = Astro.params;
const { posts } = Astro.props;
---

<BaseLayout title={`Posts tagged "${tag}"`}>
  <h1>#{tag}</h1>
  <ul>
    {posts.map((post) => (
      <li>
        <a href={`/blog/${post.slug}`}>{post.data.title}</a>
      </li>
    ))}
  </ul>
</BaseLayout>
```

**Pagination with `paginate()`**:

```astro
---
// src/pages/blog/[page].astro
import { getCollection } from "astro:content";
import type { GetStaticPaths } from "astro";
import BaseLayout from "../../layouts/BaseLayout.astro";

export const getStaticPaths = (async ({ paginate }) => {
  const allPosts = await getCollection("blog", ({ data }) => !data.draft);
  const sorted = allPosts.sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );
  return paginate(sorted, { pageSize: 10 });
}) satisfies GetStaticPaths;

const { page } = Astro.props;
// page.data       - array of posts for this page
// page.currentPage - current page number (1-based)
// page.lastPage   - total number of pages
// page.url.prev   - URL of previous page (or undefined)
// page.url.next   - URL of next page (or undefined)
// page.total      - total number of items
---

<BaseLayout title={`Blog - Page ${page.currentPage}`}>
  <h1>Blog</h1>
  {page.data.map((post) => (
    <article>
      <a href={`/blog/${post.slug}`}>{post.data.title}</a>
    </article>
  ))}

  <nav class="pagination" aria-label="Blog pagination">
    {page.url.prev && <a href={page.url.prev}>Previous</a>}
    <span>Page {page.currentPage} of {page.lastPage}</span>
    {page.url.next && <a href={page.url.next}>Next</a>}
  </nav>
</BaseLayout>
```

**Rendering modes** (configure in `astro.config.mjs`):

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import node from "@astrojs/node";

export default defineConfig({
  // Option 1: Static (default) - all pages pre-rendered at build time
  output: "static",

  // Option 2: Server - all pages rendered on demand
  // output: "server",
  // adapter: node({ mode: "standalone" }),

  // Option 3: Hybrid - static by default, opt-in to SSR per page
  // output: "hybrid",
  // adapter: node({ mode: "standalone" }),
});
```

**Per-page rendering overrides** (in hybrid or server mode):

```astro
---
// src/pages/dashboard.astro
// In hybrid mode (default static), opt this page into SSR:
export const prerender = false;

// In server mode (default SSR), opt this page into static:
// export const prerender = true;

const user = await getUser(Astro.cookies.get("session")?.value);
if (!user) {
  return Astro.redirect("/login");
}
---

<h1>Welcome, {user.name}</h1>
```

**i18n routing configuration**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";

export default defineConfig({
  i18n: {
    defaultLocale: "en",
    locales: ["en", "fr", "de", "ja"],
    routing: {
      prefixDefaultLocale: false, // / for English, /fr/ for French
    },
    fallback: {
      fr: "en",
      de: "en",
    },
  },
});
```

```astro
---
// src/pages/[lang]/about.astro
export function getStaticPaths() {
  return [
    { params: { lang: "en" }, props: { greeting: "About Us" } },
    { params: { lang: "fr" }, props: { greeting: "A Propos" } },
    { params: { lang: "de" }, props: { greeting: "Uber Uns" } },
  ];
}

const { lang } = Astro.params;
const { greeting } = Astro.props;
const currentLocale = Astro.currentLocale; // "en", "fr", or "de"
---

<h1>{greeting}</h1>
<p>Current locale: {currentLocale}</p>
```
