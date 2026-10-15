### Step 1: Astro Fundamentals

**Standard Astro project structure**:

```
src/
  components/        # Reusable .astro and framework components
    Header.astro
    Footer.astro
    Button.tsx       # React component (island)
  content/           # Content collections (Markdown, MDX, JSON)
    blog/
      first-post.md
      second-post.mdx
    authors/
      alice.json
    config.ts        # Collection schema definitions
  layouts/           # Page layouts
    BaseLayout.astro
    BlogPost.astro
  pages/             # File-based routing
    index.astro      # /
    about.astro      # /about
    blog/
      index.astro    # /blog
      [slug].astro   # /blog/:slug
    api/
      search.ts      # /api/search (API endpoint)
  styles/            # Global styles
    global.css
  middleware.ts      # Request middleware (SSR mode)
public/              # Static assets (served as-is)
  favicon.svg
  robots.txt
astro.config.mjs     # Astro configuration
tsconfig.json        # TypeScript configuration
```

**Astro component anatomy** (`.astro` files have a frontmatter script fence and an HTML template):

```astro
---
// src/components/Greeting.astro
// --- Frontmatter: runs at build time (or request time in SSR) ---
// This is server-side TypeScript. It never ships to the browser.

interface Props {
  name: string;
  greeting?: string;
}

const { name, greeting = "Hello" } = Astro.props;
const capitalizedName = name.charAt(0).toUpperCase() + name.slice(1);
const timestamp = new Date().toLocaleDateString("en-US", {
  year: "numeric",
  month: "long",
  day: "numeric",
});
---

<!-- Template: standard HTML with expressions in curly braces -->
<div class="greeting-card">
  <h2>{greeting}, {capitalizedName}!</h2>
  <p>Generated on {timestamp}</p>
  <slot />           <!-- Default slot for child content -->
  <slot name="footer" /> <!-- Named slot -->
</div>

<style>
  /* Scoped styles: only apply to this component */
  .greeting-card {
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
  }
  h2 {
    color: #1a202c;
    margin: 0 0 0.5rem;
  }
</style>
```

**Using the component with slots**:

```astro
---
// src/pages/index.astro
import Greeting from "../components/Greeting.astro";
import BaseLayout from "../layouts/BaseLayout.astro";
---

<BaseLayout title="Home">
  <Greeting name="developer" greeting="Welcome">
    <p>This content fills the default slot.</p>
    <p slot="footer">This goes into the named "footer" slot.</p>
  </Greeting>
</BaseLayout>
```

**Base layout with `<head>` management**:

```astro
---
// src/layouts/BaseLayout.astro
interface Props {
  title: string;
  description?: string;
}

const { title, description = "An Astro site" } = Astro.props;
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={description} />
    <link rel="canonical" href={canonicalURL} />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>{title}</title>
  </head>
  <body>
    <header>
      <nav>
        <a href="/">Home</a>
        <a href="/blog">Blog</a>
        <a href="/about">About</a>
      </nav>
    </header>
    <main>
      <slot />
    </main>
    <footer>
      <p>&copy; {new Date().getFullYear()} My Site</p>
    </footer>
  </body>
</html>

<style is:global>
  /* is:global escapes scoping for base styles */
  *,
  *::before,
  *::after {
    box-sizing: border-box;
    margin: 0;
  }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    color: #1a202c;
  }
</style>
```

**Conditional rendering and list iteration**:

```astro
---
// src/components/FeatureList.astro
interface Props {
  features: { title: string; available: boolean }[];
  showUnavailable?: boolean;
}

const { features, showUnavailable = false } = Astro.props;
const visibleFeatures = showUnavailable
  ? features
  : features.filter((f) => f.available);
---

{visibleFeatures.length > 0 ? (
  <ul class="feature-list">
    {visibleFeatures.map((feature) => (
      <li class:list={["feature", { unavailable: !feature.available }]}>
        {feature.title}
        {feature.available ? <span class="badge">Available</span> : null}
      </li>
    ))}
  </ul>
) : (
  <p>No features to display.</p>
)}
```
