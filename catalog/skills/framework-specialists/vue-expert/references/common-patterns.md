## Common Patterns

### Pattern 1: Debounced Search with Composable

```vue
<script setup lang="ts">
import { ref, watch } from "vue";

function useDebouncedRef<T>(initialValue: T, delayMs: number) {
  const value = ref(initialValue) as Ref<T>;
  const debouncedValue = ref(initialValue) as Ref<T>;
  let timeout: ReturnType<typeof setTimeout>;

  watch(value, (newVal) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      debouncedValue.value = newVal;
    }, delayMs);
  });

  return { value, debouncedValue };
}

const { value: searchInput, debouncedValue: debouncedQuery } =
  useDebouncedRef("", 300);

watch(debouncedQuery, async (query) => {
  if (query.length >= 2) {
    results.value = await searchProducts(query);
  }
});
</script>

<template>
  <input v-model="searchInput" placeholder="Search products..." />
  <ProductList :products="results" />
</template>
```

### Pattern 2: Teleport Modal with Focus Trap

```vue
<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from "vue";

const props = defineProps<{
  open: boolean;
  title: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const dialogRef = ref<HTMLDialogElement | null>(null);

watch(
  () => props.open,
  async (isOpen) => {
    await nextTick();
    if (isOpen) {
      dialogRef.value?.showModal();
    } else {
      dialogRef.value?.close();
    }
  }
);

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") emit("close");
}
</script>

<template>
  <Teleport to="body">
    <dialog
      ref="dialogRef"
      :aria-label="title"
      @keydown="handleKeydown"
      @close="emit('close')"
    >
      <header>
        <h2>{{ title }}</h2>
        <button @click="emit('close')" aria-label="Close dialog">
          &times;
        </button>
      </header>
      <div class="dialog-body">
        <slot />
      </div>
      <footer>
        <slot name="actions" />
      </footer>
    </dialog>
  </Teleport>
</template>
```
