### Step 2: Content Collections

**Define collection schemas** in `src/content/config.ts` using Zod:

```ts
// src/content/config.ts
import { defineCollection, z, reference } from "astro:content";

const blogCollection = defineCollection({
  type: "content", // Markdown/MDX files
  schema: ({ image }) =>
    z.object({
      title: z.string().max(100),
      description: z.string().max(200),
      pubDate: z.coerce.date(),
      updatedDate: z.coerce.date().optional(),
      heroImage: image().optional(), // Validated image import
      tags: z.array(z.string()).default([]),
      draft: z.boolean().default(false),
      author: reference("authors"), // Reference to another collection
    }),
});

const authorsCollection = defineCollection({
  type: "data", // JSON or YAML files
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      email: z.string().email(),
      bio: z.string().max(500),
      avatar: image().optional(),
      social: z
        .object({
          twitter: z.string().url().optional(),
          github: z.string().url().optional(),
        })
        .optional(),
    }),
});

const changelogCollection = defineCollection({
  type: "content",
  schema: z.object({
    version: z.string().regex(/^\d+\.\d+\.\d+$/),
    date: z.coerce.date(),
    breaking: z.boolean().default(false),
  }),
});

export const collections = {
  blog: blogCollection,
  authors: authorsCollection,
  changelog: changelogCollection,
};
```

**Example content files**:

```markdown
---
# src/content/blog/getting-started.md
title: "Getting Started with Astro"
description: "Learn how to build your first Astro site from scratch."
pubDate: 2025-01-15
tags: ["astro", "tutorial"]
draft: false
author: alice
heroImage: "./images/getting-started-hero.jpg"
---

## Introduction

Astro is a web framework for building content-driven websites...
```

```json
// src/content/authors/alice.json
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "bio": "Full-stack developer and technical writer.",
  "social": {
    "twitter": "https://twitter.com/alice",
    "github": "https://github.com/alice"
  }
}
```

**Query and render collections**:

```astro
---
// src/pages/blog/index.astro
import { getCollection } from "astro:content";
import BaseLayout from "../../layouts/BaseLayout.astro";
import BlogCard from "../../components/BlogCard.astro";

// Filter out drafts in production
const allPosts = await getCollection("blog", ({ data }) => {
  return import.meta.env.PROD ? !data.draft : true;
});

// Sort by publication date (newest first)
const sortedPosts = allPosts.sort(
  (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
);
---

<BaseLayout title="Blog">
  <h1>Blog</h1>
  <ul class="post-list">
    {sortedPosts.map((post) => (
      <li>
        <BlogCard
          title={post.data.title}
          description={post.data.description}
          pubDate={post.data.pubDate}
          tags={post.data.tags}
          href={`/blog/${post.slug}`}
        />
      </li>
    ))}
  </ul>
</BaseLayout>
```

**Generate pages from collection entries**:

```astro
---
// src/pages/blog/[slug].astro
import { getCollection, type CollectionEntry } from "astro:content";
import BlogPost from "../../layouts/BlogPost.astro";

export async function getStaticPaths() {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  return posts.map((post) => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

interface Props {
  post: CollectionEntry<"blog">;
}

const { post } = Astro.props;
const { Content, headings, remarkPluginFrontmatter } = await post.render();

// Resolve the author reference
const authorEntry = await getEntry(post.data.author);
---

<BlogPost
  title={post.data.title}
  pubDate={post.data.pubDate}
  author={authorEntry.data.name}
  headings={headings}
>
  <Content />
</BlogPost>
```

**MDX integration for rich content**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export default defineConfig({
  integrations: [mdx()],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
    shikiConfig: {
      theme: "github-dark",
      wrap: true,
    },
  },
});
```
