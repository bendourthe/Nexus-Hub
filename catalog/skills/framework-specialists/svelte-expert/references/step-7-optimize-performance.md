### Step 7: Optimize Performance

**Fine-grained reactivity with runes**:

```svelte
<script lang="ts">
  // Svelte 5 runes provide fine-grained reactivity at the signal level.
  // Only the specific DOM nodes that depend on a changed value will update.

  let firstName = $state("Alice");
  let lastName = $state("Smith");

  // Only elements reading fullName re-render when firstName or lastName changes
  let fullName = $derived(`${firstName} ${lastName}`);

  // Avoid $effect for derived state; use $derived instead
  // WRONG: $effect(() => { fullName = `${firstName} ${lastName}` });
  // RIGHT: let fullName = $derived(`${firstName} ${lastName}`);
</script>

<input bind:value={firstName} /> <!-- Updating this does NOT re-render the lastName input -->
<input bind:value={lastName} />
<p>Hello, {fullName}</p>
```

**Transitions and animations**:

```svelte
<script lang="ts">
  import { fade, fly, slide, scale } from "svelte/transition";
  import { flip } from "svelte/animate";
  import { quintOut } from "svelte/easing";

  let items = $state<{ id: string; text: string }[]>([]);
  let showPanel = $state(false);

  function addItem() {
    items.push({ id: crypto.randomUUID(), text: `Item ${items.length + 1}` });
  }

  function removeItem(id: string) {
    const index = items.findIndex((i) => i.id === id);
    if (index !== -1) items.splice(index, 1);
  }
</script>

<button onclick={() => (showPanel = !showPanel)}>Toggle Panel</button>

{#if showPanel}
  <div transition:slide={{ duration: 300, easing: quintOut }}>
    <p>This panel slides in and out.</p>
  </div>
{/if}

<button onclick={addItem}>Add Item</button>

<ul>
  {#each items as item (item.id)}
    <li
      animate:flip={{ duration: 200 }}
      in:fly={{ y: 20, duration: 200 }}
      out:fade={{ duration: 150 }}
    >
      {item.text}
      <button onclick={() => removeItem(item.id)}>Remove</button>
    </li>
  {/each}
</ul>
```

**Lazy loading with dynamic imports**:

```svelte
<script lang="ts">
  let showChart = $state(false);
  let ChartComponent: any = $state(null);

  async function loadChart() {
    showChart = true;
    // Dynamic import splits the chart library into a separate chunk
    const module = await import("$lib/components/HeavyChart.svelte");
    ChartComponent = module.default;
  }
</script>

<button onclick={loadChart}>Show Analytics</button>

{#if showChart}
  {#if ChartComponent}
    <ChartComponent data={chartData} />
  {:else}
    <p>Loading chart...</p>
  {/if}
{/if}
```

**Prerendering and adapter selection**:

```ts
// svelte.config.js
import adapter from "@sveltejs/adapter-auto"; // Auto-detects Vercel, Netlify, Cloudflare
// import adapter from "@sveltejs/adapter-node";     // Self-hosted Node.js
// import adapter from "@sveltejs/adapter-static";   // Fully static site
// import adapter from "@sveltejs/adapter-vercel";   // Vercel-specific features

import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter(),
    prerender: {
      // Prerender these routes at build time
      entries: ["/", "/about", "/pricing", "/blog"],
    },
    csp: {
      directives: {
        "script-src": ["self"],
        "style-src": ["self", "unsafe-inline"],
      },
    },
    alias: {
      $components: "src/lib/components",
      $stores: "src/lib/stores",
    },
  },
};

export default config;
```

**Per-page prerendering and SSR control**:

```ts
// src/routes/about/+page.ts
// Static page: prerender at build time
export const prerender = true;

// src/routes/dashboard/+page.ts
// Dynamic page: never prerender, always SSR
export const prerender = false;
export const ssr = true;

// src/routes/app/+page.ts
// SPA page: disable SSR, render client-only
export const ssr = false;
export const csr = true;
```
