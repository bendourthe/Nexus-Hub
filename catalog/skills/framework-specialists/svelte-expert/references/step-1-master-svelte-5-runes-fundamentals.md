### Step 1: Master Svelte 5 Runes Fundamentals

Svelte 5 replaces stores and reactive declarations with runes, a set of compiler-level primitives for fine-grained reactivity.

**$state: reactive state declaration**:

```svelte
<script lang="ts">
  let count = $state(0);
  let user = $state<{ name: string; email: string }>({
    name: "Alice",
    email: "alice@example.com",
  });

  // $state creates deeply reactive objects; nested mutations trigger updates
  function updateEmail(email: string) {
    user.email = email; // Triggers reactivity without reassignment
  }
</script>

<button onclick={() => count++}>
  Clicked {count} {count === 1 ? "time" : "times"}
</button>
<p>{user.name} ({user.email})</p>
```

**$state.raw: non-deeply-reactive state for large objects**:

```svelte
<script lang="ts">
  // Use $state.raw when you do not need deep reactivity (large arrays, immutable data)
  let items = $state.raw<string[]>([]);

  function setItems(newItems: string[]) {
    items = newItems; // Must reassign the entire value; mutations are not tracked
  }
</script>
```

**$derived: computed values that update automatically**:

```svelte
<script lang="ts">
  let items = $state<{ name: string; price: number; quantity: number }[]>([
    { name: "Widget", price: 9.99, quantity: 3 },
    { name: "Gadget", price: 24.99, quantity: 1 },
  ]);

  let total = $derived(
    items.reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  let formattedTotal = $derived(`$${total.toFixed(2)}`);

  // $derived.by for multi-statement computations
  let summary = $derived.by(() => {
    const count = items.length;
    const avgPrice = count > 0 ? total / count : 0;
    return { count, avgPrice, total };
  });
</script>

<p>Cart: {summary.count} items, total {formattedTotal}</p>
```

**$effect: side effects that run when dependencies change**:

```svelte
<script lang="ts">
  let query = $state("");
  let results = $state<string[]>([]);

  // $effect tracks which reactive values are read and reruns when they change
  $effect(() => {
    if (query.length < 2) {
      results = [];
      return;
    }

    const controller = new AbortController();

    fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      signal: controller.signal,
    })
      .then((res) => res.json())
      .then((data) => {
        results = data.items;
      })
      .catch((err) => {
        if (err.name !== "AbortError") console.error(err);
      });

    // Return a cleanup function (runs before the effect re-executes)
    return () => controller.abort();
  });
</script>

<input bind:value={query} placeholder="Search..." />
<ul>
  {#each results as result}
    <li>{result}</li>
  {/each}
</ul>
```

**$props and $bindable: component inputs**:

```ts
// UserCard.svelte
<script lang="ts">
  interface Props {
    name: string;
    email: string;
    role?: "admin" | "user";
    onSave?: (data: { name: string; email: string }) => void;
  }

  let { name, email, role = "user", onSave }: Props = $props();
</script>

<div class="card">
  <h3>{name}</h3>
  <p>{email} ({role})</p>
  {#if onSave}
    <button onclick={() => onSave?.({ name, email })}>Save</button>
  {/if}
</div>
```

**$bindable: props that support two-way binding**:

```svelte
<!-- TextInput.svelte -->
<script lang="ts">
  interface Props {
    value: string;
    placeholder?: string;
  }

  let { value = $bindable(""), placeholder = "" }: Props = $props();
</script>

<input bind:value {placeholder} />

<!-- Parent.svelte -->
<script lang="ts">
  import TextInput from "./TextInput.svelte";

  let searchQuery = $state("");
</script>

<TextInput bind:value={searchQuery} placeholder="Search..." />
<p>Current query: {searchQuery}</p>
```
