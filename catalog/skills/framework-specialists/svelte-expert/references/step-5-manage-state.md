### Step 5: Manage State

**Shared rune-based stores**:

```ts
// src/lib/stores/cart.svelte.ts
interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

function createCartStore() {
  let items = $state<CartItem[]>([]);

  let total = $derived(
    items.reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  let count = $derived(
    items.reduce((sum, item) => sum + item.quantity, 0)
  );

  function addItem(product: Omit<CartItem, "quantity">) {
    const existing = items.find((item) => item.id === product.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      items.push({ ...product, quantity: 1 });
    }
  }

  function removeItem(id: string) {
    const index = items.findIndex((item) => item.id === id);
    if (index !== -1) {
      items.splice(index, 1);
    }
  }

  function updateQuantity(id: string, quantity: number) {
    const item = items.find((i) => i.id === id);
    if (item) {
      item.quantity = Math.max(0, quantity);
      if (item.quantity === 0) removeItem(id);
    }
  }

  function clear() {
    items.length = 0;
  }

  return {
    get items() { return items; },
    get total() { return total; },
    get count() { return count; },
    addItem,
    removeItem,
    updateQuantity,
    clear,
  };
}

export const cart = createCartStore();
```

```svelte
<!-- CartWidget.svelte -->
<script lang="ts">
  import { cart } from "$lib/stores/cart.svelte";
</script>

<div class="cart-widget">
  <span>Cart ({cart.count} items): ${cart.total.toFixed(2)}</span>
  {#each cart.items as item}
    <div class="cart-item">
      <span>{item.name} x {item.quantity}</span>
      <button onclick={() => cart.updateQuantity(item.id, item.quantity - 1)}>-</button>
      <button onclick={() => cart.updateQuantity(item.id, item.quantity + 1)}>+</button>
      <button onclick={() => cart.removeItem(item.id)}>Remove</button>
    </div>
  {/each}
  {#if cart.count > 0}
    <button onclick={() => cart.clear()}>Clear Cart</button>
  {/if}
</div>
```

**Context API with getContext/setContext**:

```svelte
<!-- ThemeProvider.svelte -->
<script lang="ts">
  import { setContext } from "svelte";

  interface ThemeContext {
    theme: string;
    toggleTheme: () => void;
  }

  let theme = $state<"light" | "dark">("light");

  function toggleTheme() {
    theme = theme === "light" ? "dark" : "light";
  }

  // Context is available to all descendants
  setContext<ThemeContext>("theme", {
    get theme() { return theme; },
    toggleTheme,
  });

  let { children }: { children: any } = $props();
</script>

<div class="app" data-theme={theme}>
  {@render children()}
</div>

<!-- ThemeToggle.svelte (descendant component) -->
<script lang="ts">
  import { getContext } from "svelte";

  interface ThemeContext {
    theme: string;
    toggleTheme: () => void;
  }

  const { theme, toggleTheme } = getContext<ThemeContext>("theme");
</script>

<button onclick={toggleTheme}>
  Current theme: {theme}. Click to toggle.
</button>
```

**Derived state across multiple stores**:

```ts
// src/lib/stores/filters.svelte.ts
interface FilterState {
  category: string;
  minPrice: number;
  maxPrice: number;
  searchQuery: string;
}

function createFilterStore() {
  let filters = $state<FilterState>({
    category: "all",
    minPrice: 0,
    maxPrice: Infinity,
    searchQuery: "",
  });

  let activeFilterCount = $derived(
    [
      filters.category !== "all",
      filters.minPrice > 0,
      filters.maxPrice < Infinity,
      filters.searchQuery.length > 0,
    ].filter(Boolean).length
  );

  let queryParams = $derived.by(() => {
    const params = new URLSearchParams();
    if (filters.category !== "all") params.set("category", filters.category);
    if (filters.minPrice > 0) params.set("minPrice", String(filters.minPrice));
    if (filters.maxPrice < Infinity) params.set("maxPrice", String(filters.maxPrice));
    if (filters.searchQuery) params.set("q", filters.searchQuery);
    return params.toString();
  });

  function setCategory(category: string) {
    filters.category = category;
  }

  function setPriceRange(min: number, max: number) {
    filters.minPrice = min;
    filters.maxPrice = max;
  }

  function setSearch(query: string) {
    filters.searchQuery = query;
  }

  function reset() {
    filters.category = "all";
    filters.minPrice = 0;
    filters.maxPrice = Infinity;
    filters.searchQuery = "";
  }

  return {
    get filters() { return filters; },
    get activeFilterCount() { return activeFilterCount; },
    get queryParams() { return queryParams; },
    setCategory,
    setPriceRange,
    setSearch,
    reset,
  };
}

export const filterStore = createFilterStore();
```
