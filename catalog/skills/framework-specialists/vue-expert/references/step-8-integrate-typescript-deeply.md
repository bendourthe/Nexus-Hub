### Step 8: Integrate TypeScript Deeply

**Typed props with complex types and runtime validation**:

```vue
<script setup lang="ts">
import type { PropType } from "vue";

// Approach 1: defineProps with type-only syntax (preferred)
interface ChartDataset {
  label: string;
  data: number[];
  color: string;
  type: "line" | "bar" | "area";
}

interface ChartConfig {
  title: string;
  datasets: ChartDataset[];
  xLabels: string[];
  yAxis?: {
    min?: number;
    max?: number;
    format?: (value: number) => string;
  };
}

const props = defineProps<{
  config: ChartConfig;
  width?: number;
  height?: number;
  animate?: boolean;
}>();

// Approach 2: defineProps with runtime validation (when defaults are complex)
// Use this when you need validator functions or complex defaults
const propsAlt = defineProps({
  config: {
    type: Object as PropType<ChartConfig>,
    required: true,
    validator: (value: ChartConfig) => {
      return value.datasets.length > 0 && value.xLabels.length > 0;
    },
  },
  width: { type: Number, default: 600 },
  height: { type: Number, default: 400 },
});
</script>
```

**Typed emits with complex payloads**:

```vue
<script setup lang="ts">
interface FormValues {
  name: string;
  email: string;
  role: "admin" | "editor" | "viewer";
}

interface ValidationError {
  field: keyof FormValues;
  message: string;
}

// Typed emits ensure compile-time safety for event payloads
const emit = defineEmits<{
  submit: [values: FormValues];
  cancel: [];
  "validation-error": [errors: ValidationError[]];
  "field-change": [field: keyof FormValues, value: string];
}>();

function handleSubmit() {
  const errors = validate();
  if (errors.length > 0) {
    emit("validation-error", errors);
    return;
  }
  emit("submit", { name: name.value, email: email.value, role: role.value });
}

// TypeScript enforces correct payload types:
// emit("submit", { name: 123 })  // Type error: number is not assignable to string
// emit("cancel", "arg")          // Type error: expected 0 arguments
</script>
```

**Generic components**:

```vue
<!-- GenericSelect.vue -->
<script setup lang="ts" generic="T extends { id: string; label: string }">
import { computed } from "vue";

const props = defineProps<{
  options: T[];
  modelValue: T | null;
  placeholder?: string;
  disabled?: boolean;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: T | null];
}>();

const selectedId = computed(() => props.modelValue?.id ?? "");

function handleChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  const selected = props.options.find((opt) => opt.id === target.value) ?? null;
  emit("update:modelValue", selected);
}
</script>

<template>
  <select
    :value="selectedId"
    :disabled="disabled"
    @change="handleChange"
  >
    <option value="" disabled>
      {{ placeholder ?? "Select an option" }}
    </option>
    <option
      v-for="option in options"
      :key="option.id"
      :value="option.id"
    >
      {{ option.label }}
    </option>
  </select>
</template>

<!-- Usage: TypeScript infers T from the options prop -->
<!--
<GenericSelect
  :options="countries"
  v-model="selectedCountry"
  placeholder="Choose a country"
/>
-->
```

**Typed slots**:

```vue
<!-- TypedDataList.vue -->
<script setup lang="ts" generic="T">
defineProps<{
  items: T[];
  loading?: boolean;
}>();

// Typed slots ensure consumers provide correct slot prop types
defineSlots<{
  default: (props: { item: T; index: number }) => unknown;
  empty: () => unknown;
  loading: () => unknown;
  header: (props: { count: number }) => unknown;
}>();
</script>

<template>
  <div class="data-list">
    <div class="data-list__header">
      <slot name="header" :count="items.length" />
    </div>
    <div v-if="loading" class="data-list__loading">
      <slot name="loading">
        <span>Loading...</span>
      </slot>
    </div>
    <div v-else-if="items.length === 0" class="data-list__empty">
      <slot name="empty">
        <p>No items found.</p>
      </slot>
    </div>
    <div v-else class="data-list__items">
      <div v-for="(item, index) in items" :key="index">
        <slot :item="item" :index="index" />
      </div>
    </div>
  </div>
</template>

<!-- Usage: slot props are fully typed based on T -->
<!--
<TypedDataList :items="users">
  <template #default="{ item, index }">
    <UserCard :user="item" :rank="index + 1" />
  </template>
  <template #header="{ count }">
    <h2>{{ count }} users found</h2>
  </template>
  <template #empty>
    <EmptyState message="No users match your search." />
  </template>
</TypedDataList>
-->
```

**Augmenting global properties and component types**:

```ts
// types/vue-shims.d.ts
import type { AxiosInstance } from "axios";
import type { Router } from "vue-router";

// Augment Vue's ComponentCustomProperties to type this.$http, this.$router, etc.
declare module "vue" {
  interface ComponentCustomProperties {
    $http: AxiosInstance;
    $formatDate: (date: Date | string, locale?: string) => string;
    $formatCurrency: (amount: number, currency?: string) => string;
  }
}

// Augment route meta for type-safe router.beforeEach
declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    roles?: ("admin" | "editor" | "viewer")[];
    title?: string;
    breadcrumb?: string;
  }
}

// Register global components for template type checking (Volar)
declare module "vue" {
  export interface GlobalComponents {
    BaseButton: typeof import("../components/BaseButton.vue")["default"];
    BaseInput: typeof import("../components/BaseInput.vue")["default"];
    BaseModal: typeof import("../components/BaseModal.vue")["default"];
    RouterLink: typeof import("vue-router")["RouterLink"];
    RouterView: typeof import("vue-router")["RouterView"];
  }
}

export {};
```

```ts
// plugins/globals.ts -- registering the augmented properties
import type { App } from "vue";
import axios from "axios";

export function registerGlobals(app: App) {
  const http = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 10_000,
  });

  app.config.globalProperties.$http = http;

  app.config.globalProperties.$formatDate = (
    date: Date | string,
    locale = "en-US"
  ) => {
    return new Intl.DateTimeFormat(locale, {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(date));
  };

  app.config.globalProperties.$formatCurrency = (
    amount: number,
    currency = "USD"
  ) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(amount);
  };
}
```
