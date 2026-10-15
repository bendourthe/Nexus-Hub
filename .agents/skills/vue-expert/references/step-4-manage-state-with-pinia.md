### Step 4: Manage State with Pinia

**Defining a Pinia store with TypeScript**:

```ts
// stores/useProductStore.ts
import { defineStore } from "pinia";
import { computed, ref } from "vue";

interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  inStock: boolean;
}

interface ProductFilters {
  category: string | null;
  minPrice: number;
  maxPrice: number;
  inStockOnly: boolean;
}

// Setup store syntax (Composition API style, recommended)
export const useProductStore = defineStore("products", () => {
  // State
  const products = ref<Product[]>([]);
  const filters = ref<ProductFilters>({
    category: null,
    minPrice: 0,
    maxPrice: Infinity,
    inStockOnly: false,
  });
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Getters (computed)
  const filteredProducts = computed(() => {
    return products.value.filter((product) => {
      if (filters.value.category && product.category !== filters.value.category) {
        return false;
      }
      if (product.price < filters.value.minPrice) return false;
      if (product.price > filters.value.maxPrice) return false;
      if (filters.value.inStockOnly && !product.inStock) return false;
      return true;
    });
  });

  const categories = computed(() => {
    const cats = new Set(products.value.map((p) => p.category));
    return Array.from(cats).sort();
  });

  const totalValue = computed(() =>
    products.value.reduce((sum, p) => sum + p.price, 0)
  );

  // Actions
  async function fetchProducts(): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response = await fetch("/api/products");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      products.value = await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to fetch products";
    } finally {
      loading.value = false;
    }
  }

  async function addProduct(product: Omit<Product, "id">): Promise<Product | null> {
    try {
      const response = await fetch("/api/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(product),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const created: Product = await response.json();
      products.value.push(created);
      return created;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to add product";
      return null;
    }
  }

  function updateFilters(newFilters: Partial<ProductFilters>) {
    filters.value = { ...filters.value, ...newFilters };
  }

  function $reset() {
    products.value = [];
    filters.value = { category: null, minPrice: 0, maxPrice: Infinity, inStockOnly: false };
    loading.value = false;
    error.value = null;
  }

  return {
    // State
    products,
    filters,
    loading,
    error,
    // Getters
    filteredProducts,
    categories,
    totalValue,
    // Actions
    fetchProducts,
    addProduct,
    updateFilters,
    $reset,
  };
});
```

**Pinia plugin for persistence and logging**:

```ts
// plugins/piniaLogger.ts
import type { PiniaPluginContext } from "pinia";

export function piniaLogger({ store }: PiniaPluginContext) {
  store.$onAction(({ name, args, after, onError }) => {
    const startTime = performance.now();

    after((result) => {
      const duration = (performance.now() - startTime).toFixed(2);
      console.debug(
        `[Pinia] ${store.$id}.${name}() completed in ${duration}ms`,
        { args, result }
      );
    });

    onError((error) => {
      console.error(`[Pinia] ${store.$id}.${name}() failed`, { args, error });
    });
  });
}

// plugins/piniaPersist.ts
export function piniaPersist({ store }: PiniaPluginContext) {
  const key = `pinia-${store.$id}`;

  // Hydrate from localStorage on store creation
  const saved = localStorage.getItem(key);
  if (saved) {
    try {
      store.$patch(JSON.parse(saved));
    } catch {
      localStorage.removeItem(key);
    }
  }

  // Persist on every state change
  store.$subscribe((_mutation, state) => {
    localStorage.setItem(key, JSON.stringify(state));
  });
}

// main.ts -- register plugins
import { createPinia } from "pinia";
import { piniaLogger } from "./plugins/piniaLogger";
import { piniaPersist } from "./plugins/piniaPersist";

const pinia = createPinia();
pinia.use(piniaLogger);
pinia.use(piniaPersist);
```

**Store composition (stores using other stores)**:

```ts
// stores/useCartStore.ts
import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { useProductStore } from "./useProductStore";
import { useAuthStore } from "./useAuthStore";

interface CartItem {
  productId: string;
  quantity: number;
}

export const useCartStore = defineStore("cart", () => {
  const productStore = useProductStore();
  const authStore = useAuthStore();

  const items = ref<CartItem[]>([]);

  const enrichedItems = computed(() =>
    items.value
      .map((item) => {
        const product = productStore.products.find((p) => p.id === item.productId);
        if (!product) return null;
        return {
          ...item,
          name: product.name,
          price: product.price,
          subtotal: product.price * item.quantity,
        };
      })
      .filter(Boolean)
  );

  const total = computed(() =>
    enrichedItems.value.reduce((sum, item) => sum + (item?.subtotal ?? 0), 0)
  );

  function addToCart(productId: string, quantity = 1) {
    if (!authStore.isAuthenticated) {
      throw new Error("Must be logged in to add items to cart");
    }
    const existing = items.value.find((i) => i.productId === productId);
    if (existing) {
      existing.quantity += quantity;
    } else {
      items.value.push({ productId, quantity });
    }
  }

  function removeFromCart(productId: string) {
    items.value = items.value.filter((i) => i.productId !== productId);
  }

  return { items, enrichedItems, total, addToCart, removeFromCart };
});
```
