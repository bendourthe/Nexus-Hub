### Step 5: Multi-Framework Integration

Astro supports multiple UI frameworks simultaneously. Each framework is added as an integration.

**Configuration**:

```ts
// astro.config.mjs
import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import vue from "@astrojs/vue";
import svelte from "@astrojs/svelte";
import solid from "@astrojs/solid-js";

export default defineConfig({
  integrations: [
    react({
      include: ["**/react/*"], // Only process files in react/ directories
    }),
    vue({
      include: ["**/vue/*"],
    }),
    svelte(),
    solid({
      include: ["**/solid/*"],
    }),
  ],
});
```

**React component as an island**:

```tsx
// src/components/react/Counter.tsx
import { useState } from "react";

interface CounterProps {
  initialCount?: number;
  label: string;
}

export default function Counter({ initialCount = 0, label }: CounterProps) {
  const [count, setCount] = useState(initialCount);

  return (
    <div className="counter">
      <span>{label}: {count}</span>
      <button onClick={() => setCount((c) => c + 1)}>+</button>
      <button onClick={() => setCount((c) => c - 1)}>-</button>
    </div>
  );
}
```

**Vue component as an island**:

```vue
<!-- src/components/vue/ToggleTheme.vue -->
<script setup lang="ts">
import { ref } from "vue";

const isDark = ref(false);

function toggle() {
  isDark.value = !isDark.value;
  document.documentElement.classList.toggle("dark", isDark.value);
}
</script>

<template>
  <button @click="toggle" class="theme-toggle">
    {{ isDark ? "Light Mode" : "Dark Mode" }}
  </button>
</template>

<style scoped>
.theme-toggle {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
}
</style>
```

**Svelte component as an island**:

```svelte
<!-- src/components/Tabs.svelte -->
<script lang="ts">
  export let tabs: { label: string; content: string }[] = [];
  let activeIndex = 0;
</script>

<div class="tabs">
  <div class="tab-headers" role="tablist">
    {#each tabs as tab, i}
      <button
        role="tab"
        aria-selected={i === activeIndex}
        on:click={() => (activeIndex = i)}
      >
        {tab.label}
      </button>
    {/each}
  </div>
  <div class="tab-content" role="tabpanel">
    {tabs[activeIndex]?.content}
  </div>
</div>
```

**Composing multiple frameworks on one page**:

```astro
---
// src/pages/showcase.astro
import BaseLayout from "../layouts/BaseLayout.astro";
import Counter from "../components/react/Counter.tsx";
import ToggleTheme from "../components/vue/ToggleTheme.vue";
import Tabs from "../components/Tabs.svelte";

const tabData = [
  { label: "React", content: "React component rendered as an island." },
  { label: "Vue", content: "Vue component alongside React on the same page." },
  { label: "Svelte", content: "Svelte too. Each framework hydrates independently." },
];
---

<BaseLayout title="Multi-Framework Showcase">
  <h1>Framework Islands</h1>

  <!-- Each island hydrates independently with its own framework runtime -->
  <Counter client:load label="Visitors" initialCount={42} />
  <ToggleTheme client:idle />
  <Tabs client:visible tabs={tabData} />

  <!-- Static Astro content between islands (zero JS) -->
  <section>
    <h2>Why Islands?</h2>
    <p>Each interactive component loads only the JS it needs.</p>
    <p>Static content between islands ships no JavaScript at all.</p>
  </section>
</BaseLayout>
```

**Sharing state between framework islands** using nano stores:

```ts
// src/stores/cartStore.ts
// Use nanostores for cross-framework state sharing
import { atom, computed } from "nanostores";

export interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

export const $cartItems = atom<CartItem[]>([]);

export const $cartTotal = computed($cartItems, (items) =>
  items.reduce((sum, item) => sum + item.price * item.quantity, 0)
);

export function addToCart(item: Omit<CartItem, "quantity">) {
  const items = $cartItems.get();
  const existing = items.find((i) => i.id === item.id);
  if (existing) {
    $cartItems.set(
      items.map((i) =>
        i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
      )
    );
  } else {
    $cartItems.set([...items, { ...item, quantity: 1 }]);
  }
}
```

```tsx
// src/components/react/CartButton.tsx
// React component reading from the shared store
import { useStore } from "@nanostores/react";
import { $cartItems, $cartTotal } from "../../stores/cartStore";

export default function CartButton() {
  const items = useStore($cartItems);
  const total = useStore($cartTotal);

  return (
    <button className="cart-button">
      Cart ({items.length}) - ${total.toFixed(2)}
    </button>
  );
}
```

```vue
<!-- src/components/vue/AddToCartButton.vue -->
<!-- Vue component writing to the same shared store -->
<script setup lang="ts">
import { addToCart } from "../../stores/cartStore";

const props = defineProps<{
  productId: string;
  productName: string;
  price: number;
}>();

function handleAdd() {
  addToCart({ id: props.productId, name: props.productName, price: props.price });
}
</script>

<template>
  <button @click="handleAdd">Add to Cart - ${{ price.toFixed(2) }}</button>
</template>
```
