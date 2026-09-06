### Step 2: Design Component Patterns

**Single File Component structure with typed props and emits**:

```vue
<script setup lang="ts">
import { computed, useSlots } from "vue";

// Typed props with defaults using withDefaults
interface DataTableProps {
  rows: Record<string, unknown>[];
  columns: {
    key: string;
    label: string;
    sortable?: boolean;
    width?: string;
  }[];
  loading?: boolean;
  striped?: boolean;
  stickyHeader?: boolean;
  emptyMessage?: string;
}

const props = withDefaults(defineProps<DataTableProps>(), {
  loading: false,
  striped: true,
  stickyHeader: false,
  emptyMessage: "No data available",
});

// Typed emits with payload validation
const emit = defineEmits<{
  sort: [column: string, direction: "asc" | "desc"];
  "row-click": [row: Record<string, unknown>, index: number];
  "selection-change": [selectedRows: Record<string, unknown>[]];
}>();

const slots = useSlots();
const hasFooter = computed(() => !!slots.footer);

function handleSort(columnKey: string) {
  const currentDirection = sortState.value.key === columnKey
    ? sortState.value.direction
    : "asc";
  const nextDirection = currentDirection === "asc" ? "desc" : "asc";
  emit("sort", columnKey, nextDirection);
}
</script>

<template>
  <div class="data-table" :class="{ 'data-table--striped': striped }">
    <div v-if="loading" class="data-table__loading">
      <slot name="loading">
        <span>Loading...</span>
      </slot>
    </div>
    <table v-else-if="rows.length > 0">
      <thead :class="{ 'sticky-header': stickyHeader }">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width }"
            :class="{ sortable: col.sortable }"
            @click="col.sortable ? handleSort(col.key) : undefined"
          >
            <slot :name="`header-${col.key}`" :column="col">
              {{ col.label }}
            </slot>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in rows"
          :key="index"
          @click="emit('row-click', row, index)"
        >
          <td v-for="col in columns" :key="col.key">
            <slot :name="`cell-${col.key}`" :value="row[col.key]" :row="row">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
      <tfoot v-if="hasFooter">
        <tr>
          <td :colspan="columns.length">
            <slot name="footer" />
          </td>
        </tr>
      </tfoot>
    </table>
    <div v-else class="data-table__empty">
      <slot name="empty">
        <p>{{ emptyMessage }}</p>
      </slot>
    </div>
  </div>
</template>
```

**v-model with multiple bindings**:

```vue
<!-- DateRangePicker.vue -->
<script setup lang="ts">
interface DateRange {
  start: string;
  end: string;
}

const startDate = defineModel<string>("start", { required: true });
const endDate = defineModel<string>("end", { required: true });
const isOpen = defineModel<boolean>("open", { default: false });

function selectPreset(preset: "today" | "week" | "month") {
  const now = new Date();
  const start = new Date();
  if (preset === "week") start.setDate(now.getDate() - 7);
  else if (preset === "month") start.setMonth(now.getMonth() - 1);
  startDate.value = start.toISOString().split("T")[0];
  endDate.value = now.toISOString().split("T")[0];
}
</script>

<template>
  <div class="date-range-picker">
    <input type="date" v-model="startDate" />
    <span>to</span>
    <input type="date" v-model="endDate" />
    <div class="presets">
      <button @click="selectPreset('today')">Today</button>
      <button @click="selectPreset('week')">Last 7 days</button>
      <button @click="selectPreset('month')">Last 30 days</button>
    </div>
  </div>
</template>

<!-- Parent usage with multiple v-model bindings -->
<!-- <DateRangePicker v-model:start="from" v-model:end="to" v-model:open="pickerOpen" /> -->
```

**provide/inject for dependency injection**:

```vue
<!-- NotificationProvider.vue -->
<script setup lang="ts">
import { provide, reactive, readonly } from "vue";
import type { InjectionKey } from "vue";

interface Notification {
  id: string;
  type: "success" | "error" | "warning" | "info";
  message: string;
  duration?: number;
}

interface NotificationContext {
  notifications: readonly Notification[];
  notify: (notification: Omit<Notification, "id">) => void;
  dismiss: (id: string) => void;
}

export const NotificationKey: InjectionKey<NotificationContext> =
  Symbol("notification");

const state = reactive<{ notifications: Notification[] }>({
  notifications: [],
});

function notify(notification: Omit<Notification, "id">) {
  const id = crypto.randomUUID();
  state.notifications.push({ ...notification, id });
  const duration = notification.duration ?? 5000;
  if (duration > 0) {
    setTimeout(() => dismiss(id), duration);
  }
}

function dismiss(id: string) {
  const index = state.notifications.findIndex((n) => n.id === id);
  if (index !== -1) state.notifications.splice(index, 1);
}

provide(NotificationKey, {
  notifications: readonly(state.notifications),
  notify,
  dismiss,
});
</script>

<template>
  <slot />
  <Teleport to="body">
    <TransitionGroup name="notification" tag="div" class="notification-stack">
      <div
        v-for="n in state.notifications"
        :key="n.id"
        :class="['notification', `notification--${n.type}`]"
        role="alert"
      >
        <span>{{ n.message }}</span>
        <button @click="dismiss(n.id)" aria-label="Dismiss notification">
          &times;
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>
```

```vue
<!-- Any descendant component -->
<script setup lang="ts">
import { inject } from "vue";
import { NotificationKey } from "./NotificationProvider.vue";

const { notify } = inject(NotificationKey)!;

function handleSave() {
  try {
    // save logic...
    notify({ type: "success", message: "Settings saved successfully." });
  } catch {
    notify({ type: "error", message: "Failed to save settings.", duration: 0 });
  }
}
</script>
```
