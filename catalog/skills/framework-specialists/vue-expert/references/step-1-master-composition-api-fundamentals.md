### Step 1: Master Composition API Fundamentals

**ref and reactive for state management**:

```vue
<script setup lang="ts">
import { ref, reactive, computed, watch, watchEffect, onMounted } from "vue";

// ref for primitives and single values (unwraps in template automatically)
const count = ref(0);
const searchQuery = ref("");

// reactive for objects (deep reactivity by default)
interface UserProfile {
  name: string;
  email: string;
  preferences: {
    theme: "light" | "dark";
    locale: string;
  };
}

const profile = reactive<UserProfile>({
  name: "",
  email: "",
  preferences: {
    theme: "light",
    locale: "en-US",
  },
});

// computed for derived state (cached, recalculates only when dependencies change)
const displayName = computed(() => {
  return profile.name.trim() || "Anonymous User";
});

const filteredResults = computed(() => {
  const query = searchQuery.value.toLowerCase();
  if (!query) return allResults.value;
  return allResults.value.filter((item) =>
    item.title.toLowerCase().includes(query)
  );
});

// Writable computed for two-way derived state
const fullName = computed({
  get: () => `${profile.name}`.trim(),
  set: (value: string) => {
    const [first, ...rest] = value.split(" ");
    profile.name = first ?? "";
  },
});
</script>
```

**watch and watchEffect for side effects**:

```vue
<script setup lang="ts">
import { ref, watch, watchEffect, onMounted, onUnmounted } from "vue";

const userId = ref<string | null>(null);
const userData = ref<User | null>(null);
const loading = ref(false);
const error = ref<Error | null>(null);

// watch: explicit source, access to old and new values, lazy by default
watch(userId, async (newId, oldId) => {
  if (!newId) {
    userData.value = null;
    return;
  }
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch(`/api/users/${newId}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    userData.value = await response.json();
  } catch (err) {
    error.value = err instanceof Error ? err : new Error(String(err));
  } finally {
    loading.value = false;
  }
});

// watch with options: immediate runs on setup, deep watches nested changes
watch(
  () => profile.preferences,
  (newPrefs) => {
    localStorage.setItem("user-prefs", JSON.stringify(newPrefs));
  },
  { deep: true, immediate: true }
);

// watch multiple sources simultaneously
watch(
  [() => filters.category, () => filters.sortBy, currentPage],
  ([category, sortBy, page]) => {
    fetchProducts({ category, sortBy, page });
  }
);

// watchEffect: auto-tracks dependencies, runs immediately
const stopWatcher = watchEffect((onCleanup) => {
  const controller = new AbortController();

  if (searchQuery.value.length >= 3) {
    fetchSuggestions(searchQuery.value, controller.signal);
  }

  // Cleanup function runs before each re-execution and on unmount
  onCleanup(() => controller.abort());
});

// Lifecycle hooks in Composition API
onMounted(() => {
  document.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeyDown);
  stopWatcher();
});
</script>
```
