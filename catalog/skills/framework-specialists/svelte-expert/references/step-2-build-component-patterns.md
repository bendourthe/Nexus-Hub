### Step 2: Build Component Patterns

**Snippets: the Svelte 5 replacement for slots**:

```svelte
<!-- Card.svelte -->
<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    header: Snippet;
    children: Snippet;
    footer?: Snippet;
  }

  let { header, children, footer }: Props = $props();
</script>

<div class="card">
  <div class="card-header">
    {@render header()}
  </div>
  <div class="card-body">
    {@render children()}
  </div>
  {#if footer}
    <div class="card-footer">
      {@render footer()}
    </div>
  {/if}
</div>

<!-- Usage -->
<script lang="ts">
  import Card from "./Card.svelte";
</script>

<Card>
  {#snippet header()}
    <h2>User Profile</h2>
  {/snippet}

  <p>This is the card body content.</p>

  {#snippet footer()}
    <button>Save Changes</button>
  {/snippet}
</Card>
```

**Typed snippets with parameters**:

```svelte
<!-- DataList.svelte -->
<script lang="ts" generics="T">
  import type { Snippet } from "svelte";

  interface Props {
    items: T[];
    renderItem: Snippet<[T, number]>;
    empty?: Snippet;
  }

  let { items, renderItem, empty }: Props = $props();
</script>

{#if items.length === 0}
  {#if empty}
    {@render empty()}
  {:else}
    <p>No items found.</p>
  {/if}
{:else}
  <ul>
    {#each items as item, index}
      <li>{@render renderItem(item, index)}</li>
    {/each}
  </ul>
{/if}

<!-- Usage -->
<script lang="ts">
  import DataList from "./DataList.svelte";

  interface User {
    id: string;
    name: string;
    email: string;
  }

  let users = $state<User[]>([
    { id: "1", name: "Alice", email: "alice@example.com" },
    { id: "2", name: "Bob", email: "bob@example.com" },
  ]);
</script>

<DataList items={users}>
  {#snippet renderItem(user, index)}
    <span>{index + 1}. {user.name} ({user.email})</span>
  {/snippet}
  {#snippet empty()}
    <p>No users registered yet.</p>
  {/snippet}
</DataList>
```

**Event handling and component composition**:

```svelte
<!-- SearchForm.svelte -->
<script lang="ts">
  interface Props {
    onSearch: (query: string) => void;
    initialQuery?: string;
  }

  let { onSearch, initialQuery = "" }: Props = $props();
  let query = $state(initialQuery);
  let inputRef = $state<HTMLInputElement | null>(null);

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length > 0) {
      onSearch(trimmed);
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      query = "";
      inputRef?.focus();
    }
  }

  // Focus input on mount
  $effect(() => {
    inputRef?.focus();
  });
</script>

<form onsubmit={handleSubmit}>
  <input
    bind:this={inputRef}
    bind:value={query}
    onkeydown={handleKeydown}
    placeholder="Search..."
    aria-label="Search"
  />
  <button type="submit">Search</button>
</form>
```

**Two-way binding with custom components**:

```svelte
<!-- ColorPicker.svelte -->
<script lang="ts">
  interface Props {
    color: string;
    label?: string;
  }

  let { color = $bindable("#000000"), label = "Color" }: Props = $props();

  let hue = $derived(hexToHue(color));

  function hexToHue(hex: string): number {
    // Simplified hex-to-hue conversion
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    if (max === min) return 0;
    const d = max - min;
    let h = 0;
    if (max === r) h = ((g - b) / d + 6) % 6;
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    return Math.round(h * 60);
  }
</script>

<label>
  {label} (hue: {hue})
  <input type="color" bind:value={color} />
</label>
```
