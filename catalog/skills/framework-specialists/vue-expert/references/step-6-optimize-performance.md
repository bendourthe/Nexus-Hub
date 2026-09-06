### Step 6: Optimize Performance

**shallowRef and shallowReactive for large datasets**:

```vue
<script setup lang="ts">
import {
  shallowRef,
  triggerRef,
  computed,
  defineAsyncComponent,
} from "vue";

interface LogEntry {
  id: string;
  timestamp: number;
  level: "info" | "warn" | "error";
  message: string;
  metadata: Record<string, unknown>;
}

// shallowRef: only triggers updates when .value is reassigned,
// not when nested properties change. Ideal for large arrays and objects.
const logEntries = shallowRef<LogEntry[]>([]);

function appendLog(entry: LogEntry) {
  // Must reassign .value to trigger reactivity (push alone will not work)
  logEntries.value = [...logEntries.value, entry];
}

function bulkAppend(entries: LogEntry[]) {
  // Batch update: single reactivity trigger for multiple additions
  logEntries.value = [...logEntries.value, ...entries];
}

// For cases where you must mutate in place, use triggerRef
function clearOldEntries(maxAge: number) {
  const cutoff = Date.now() - maxAge;
  logEntries.value = logEntries.value.filter((e) => e.timestamp > cutoff);
  // If mutating in place instead of reassigning:
  // logEntries.value.splice(0, removeCount);
  // triggerRef(logEntries);
}

const errorCount = computed(
  () => logEntries.value.filter((e) => e.level === "error").length
);
</script>
```

**v-once, v-memo, and KeepAlive**:

```vue
<template>
  <!-- v-once: renders once, never re-renders (static content) -->
  <header v-once>
    <h1>{{ appTitle }}</h1>
    <nav>
      <a href="/about">About</a>
      <a href="/contact">Contact</a>
    </nav>
  </header>

  <!-- v-memo: skip re-render unless specified dependencies change -->
  <!-- Useful in v-for loops with expensive row rendering -->
  <div class="user-list">
    <div
      v-for="user in users"
      :key="user.id"
      v-memo="[user.name, user.avatar, user.id === selectedId]"
      class="user-card"
      :class="{ selected: user.id === selectedId }"
      @click="selectedId = user.id"
    >
      <img :src="user.avatar" :alt="user.name" />
      <span>{{ user.name }}</span>
      <ExpensiveStatusBadge :status="user.status" />
    </div>
  </div>

  <!-- KeepAlive: caches component instances instead of destroying them -->
  <KeepAlive :include="['ProductList', 'SearchResults']" :max="5">
    <component :is="currentTab" />
  </KeepAlive>
</template>

<script setup lang="ts">
import { ref, onActivated, onDeactivated } from "vue";

// KeepAlive lifecycle hooks
onActivated(() => {
  // Called when component is re-inserted from cache
  // Refresh data that may have gone stale
  refreshData();
});

onDeactivated(() => {
  // Called when component is cached (removed from DOM but kept alive)
  // Pause expensive operations like polling
  stopPolling();
});
</script>
```

**Async components and Suspense**:

```vue
<script setup lang="ts">
import { defineAsyncComponent, ref } from "vue";

// Async component with loading and error states
const HeavyChart = defineAsyncComponent({
  loader: () => import("./HeavyChart.vue"),
  loadingComponent: () => import("./ChartSkeleton.vue"),
  errorComponent: () => import("./ChartError.vue"),
  delay: 200,        // Show loading after 200ms (avoids flash for fast loads)
  timeout: 10000,    // Fail after 10 seconds
});

// Simple async component for code splitting
const AdminPanel = defineAsyncComponent(
  () => import("./AdminPanel.vue")
);

const showChart = ref(false);
</script>

<template>
  <button @click="showChart = true">Load Chart</button>

  <!-- Suspense for coordinating multiple async dependencies -->
  <Suspense v-if="showChart">
    <template #default>
      <HeavyChart :data="chartData" />
    </template>
    <template #fallback>
      <div class="skeleton">Loading chart data...</div>
    </template>
  </Suspense>
</template>
```

**Virtual scrolling for large lists**:

```vue
<script setup lang="ts">
import { ref, computed } from "vue";

interface VirtualListProps {
  items: unknown[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

const props = withDefaults(defineProps<VirtualListProps>(), {
  overscan: 5,
});

const scrollTop = ref(0);

const totalHeight = computed(() => props.items.length * props.itemHeight);

const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight);
  const visibleCount = Math.ceil(props.containerHeight / props.itemHeight);
  return {
    start: Math.max(0, start - props.overscan),
    end: Math.min(props.items.length, start + visibleCount + props.overscan),
  };
});

const visibleItems = computed(() =>
  props.items.slice(visibleRange.value.start, visibleRange.value.end).map(
    (item, index) => ({
      item,
      index: visibleRange.value.start + index,
      style: {
        position: "absolute" as const,
        top: `${(visibleRange.value.start + index) * props.itemHeight}px`,
        height: `${props.itemHeight}px`,
        width: "100%",
      },
    })
  )
);

function onScroll(event: UIEvent) {
  scrollTop.value = (event.target as HTMLElement).scrollTop;
}
</script>

<template>
  <div
    class="virtual-list"
    :style="{ height: `${containerHeight}px`, overflow: 'auto', position: 'relative' }"
    @scroll="onScroll"
  >
    <div :style="{ height: `${totalHeight}px`, position: 'relative' }">
      <div
        v-for="{ item, index, style } in visibleItems"
        :key="index"
        :style="style"
      >
        <slot :item="item" :index="index" />
      </div>
    </div>
  </div>
</template>
```
