## Common Patterns

### Pattern 1: Debounced Search with Runes

```svelte
<script lang="ts">
  let query = $state("");
  let results = $state<string[]>([]);
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  $effect(() => {
    clearTimeout(debounceTimer);

    if (query.length < 2) {
      results = [];
      return;
    }

    debounceTimer = setTimeout(async () => {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      if (res.ok) {
        results = await res.json();
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  });
</script>

<input bind:value={query} placeholder="Search..." />
{#each results as result}
  <p>{result}</p>
{/each}
```

### Pattern 2: Authenticated Layout with Redirect

```ts
// src/routes/dashboard/+layout.server.ts
import { redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = async ({ locals }) => {
  if (!locals.user) {
    redirect(302, "/login");
  }

  return {
    user: locals.user,
  };
};
```

```svelte
<!-- src/routes/dashboard/+layout.svelte -->
<script lang="ts">
  import type { LayoutData } from "./$types";

  let { data, children }: { data: LayoutData; children: any } = $props();
</script>

<div class="dashboard-layout">
  <aside>
    <nav>
      <p>Signed in as {data.user.name}</p>
      <a href="/dashboard">Overview</a>
      <a href="/dashboard/settings">Settings</a>
    </nav>
  </aside>
  <div class="dashboard-content">
    {@render children()}
  </div>
</div>
```
