### Step 7: Performance and SEO

**Image optimization with `astro:assets`**:

```astro
---
// src/components/OptimizedImage.astro
import { Image, Picture } from "astro:assets";
import heroImage from "../assets/hero.jpg"; // Import for static optimization

interface Props {
  src: ImageMetadata;
  alt: string;
  widths?: number[];
}

const { src, alt, widths = [400, 800, 1200] } = Astro.props;
---

<!-- Basic optimized image (auto-generates WebP, sets width/height) -->
<Image src={heroImage} alt="Hero banner" />

<!-- Responsive image with multiple sizes -->
<Image
  src={heroImage}
  alt="Hero banner"
  widths={[400, 800, 1200]}
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
/>

<!-- Picture element for art direction with multiple formats -->
<Picture
  src={heroImage}
  formats={["avif", "webp"]}
  alt="Hero banner"
  widths={[400, 800, 1200]}
  sizes="(max-width: 600px) 400px, 800px"
/>
```

**Remote image optimization**:

```astro
---
import { Image } from "astro:assets";
---

<!-- Remote images require explicit dimensions -->
<Image
  src="https://example.com/photo.jpg"
  alt="Remote photo"
  width={800}
  height={600}
  inferSize={false}
/>
```

```ts
// astro.config.mjs - authorize remote image domains
import { defineConfig } from "astro/config";

export default defineConfig({
  image: {
    domains: ["example.com", "images.unsplash.com"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.amazonaws.com",
      },
    ],
  },
});
```

**View Transitions for SPA-like navigation**:

```astro
---
// src/layouts/BaseLayout.astro
import { ViewTransitions } from "astro:transitions";
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>{title}</title>
    <!-- Enables client-side navigation with animated transitions -->
    <ViewTransitions />
  </head>
  <body>
    <nav>
      <a href="/">Home</a>
      <a href="/blog">Blog</a>
      <a href="/about">About</a>
    </nav>
    <main transition:animate="slide">
      <slot />
    </main>
  </body>
</html>
```

**Named transition animations**:

```astro
---
// src/components/BlogCard.astro
const { slug, title, image } = Astro.props;
---

<!-- Give elements a shared transition:name so they animate between pages -->
<article>
  <img
    src={image}
    alt={title}
    transition:name={`hero-${slug}`}
    transition:animate="morph"
  />
  <h2 transition:name={`title-${slug}`}>{title}</h2>
</article>
```

```astro
---
// src/pages/blog/[slug].astro (the target page)
const { slug } = Astro.params;
---

<!-- Same transition:name values connect elements across pages -->
<img
  src={post.data.heroImage}
  alt={post.data.title}
  transition:name={`hero-${slug}`}
/>
<h1 transition:name={`title-${slug}`}>{post.data.title}</h1>
```

**Prefetching configuration**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";

export default defineConfig({
  prefetch: {
    prefetchAll: false, // Do not prefetch every link
    defaultStrategy: "hover", // Prefetch on hover (default)
  },
});
```

```astro
<!-- Per-link prefetch control -->
<a href="/blog" data-astro-prefetch="viewport">Blog</a>   <!-- Prefetch when visible -->
<a href="/about" data-astro-prefetch="hover">About</a>    <!-- Prefetch on hover -->
<a href="/large-page" data-astro-prefetch="false">Skip</a> <!-- Never prefetch -->
```

**Sitemap and RSS integration**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://example.com",
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/admin/"),
      changefreq: "weekly",
      priority: 0.7,
      lastmod: new Date(),
      i18n: {
        defaultLocale: "en",
        locales: { en: "en-US", fr: "fr-FR" },
      },
    }),
  ],
});
```

```ts
// src/pages/rss.xml.ts
import rss from "@astrojs/rss";
import { getCollection } from "astro:content";
import type { APIContext } from "astro";

export async function GET(context: APIContext) {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  const sorted = posts.sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf()
  );

  return rss({
    title: "My Blog",
    description: "A blog about web development",
    site: context.site!,
    items: sorted.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/blog/${post.slug}/`,
      categories: post.data.tags,
    })),
    customData: "<language>en-us</language>",
  });
}
```

**Structured data (JSON-LD)**:

```astro
---
// src/layouts/BlogPost.astro
const { title, description, pubDate, author, image } = Astro.props;

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  headline: title,
  description: description,
  datePublished: pubDate.toISOString(),
  author: {
    "@type": "Person",
    name: author,
  },
  image: image ? new URL(image, Astro.site).href : undefined,
};
---

<head>
  <script type="application/ld+json" set:html={JSON.stringify(jsonLd)} />
</head>
```
