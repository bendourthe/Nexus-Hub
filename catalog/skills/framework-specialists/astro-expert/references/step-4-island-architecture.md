### Step 4: Island Architecture

Astro ships zero JavaScript by default. Interactive components become "islands" only when you add a `client:*` directive. Choose the directive that matches the component's loading priority.

**Client directive reference**:

| Directive         | When it hydrates                                       | Use for                                    |
| ----------------- | ------------------------------------------------------ | ------------------------------------------ |
| `client:load`     | Immediately on page load                               | Critical interactive UI (nav, modals)      |
| `client:idle`     | After the page finishes initial load (requestIdleCallback) | Below-fold interactive widgets             |
| `client:visible`  | When the component scrolls into the viewport           | Comments, carousels, footer widgets        |
| `client:media`    | When a CSS media query matches                         | Mobile-only sidebars, responsive widgets   |
| `client:only`     | Client-only render (no SSR HTML)                       | Components that cannot SSR (canvas, WebGL) |

**Applying hydration directives**:

```astro
---
// src/pages/index.astro
import BaseLayout from "../layouts/BaseLayout.astro";
import SearchBar from "../components/SearchBar.tsx";      // React
import Newsletter from "../components/Newsletter.vue";    // Vue
import ImageCarousel from "../components/Carousel.svelte"; // Svelte
import ThreeScene from "../components/Scene.tsx";          // React (canvas)
import MobileSidebar from "../components/Sidebar.tsx";     // React
---

<BaseLayout title="Home">
  <!-- Critical: hydrate immediately -->
  <SearchBar client:load placeholder="Search articles..." />

  <!-- Non-critical: hydrate when browser is idle -->
  <Newsletter client:idle />

  <!-- Deferred: hydrate when scrolled into view -->
  <ImageCarousel client:visible images={heroImages} />

  <!-- Conditional: hydrate only on narrow viewports -->
  <MobileSidebar client:media="(max-width: 768px)" />

  <!-- Client-only: no server-rendered HTML (for WebGL, canvas) -->
  <ThreeScene client:only="react" />

  <!-- Static by default: no directive = zero JS shipped -->
  <footer>
    <p>This Astro component ships no JavaScript.</p>
  </footer>
</BaseLayout>
```

**When to hydrate (decision framework)**:

```astro
---
// DECISION: Does this component need interactivity?
//
// NO  -> Use a plain .astro component (zero JS)
// YES -> Does it need to be interactive on first paint?
//        YES -> client:load
//        NO  -> Is it above the fold?
//               YES -> client:idle
//               NO  -> client:visible
//        Does it depend on viewport size?
//               YES -> client:media="(your query)"
//        Can it render on the server?
//               NO  -> client:only="framework"

// Example: A like button that is important but not above the fold
import LikeButton from "../components/LikeButton.tsx";
---

<!-- Hydrate when the user scrolls to it -->
<LikeButton client:visible postId="abc-123" />
```

**Passing props and children to islands**:

```astro
---
import Accordion from "../components/Accordion.tsx";

const faqItems = [
  { question: "What is Astro?", answer: "A web framework for content sites." },
  { question: "Is it fast?", answer: "Yes. Zero JS by default." },
];
---

<!--
  Props are serialized to the client.
  Only serializable data (strings, numbers, arrays, plain objects) can be passed.
  Functions, classes, and DOM nodes cannot be passed as props to islands.
-->
<Accordion client:visible items={faqItems} defaultOpen={0}>
  <p slot="footer">Can't find your answer? <a href="/contact">Contact us</a>.</p>
</Accordion>
```
