### Step 3: Build Composables for Reusable Logic

**useAsync composable for async operations**:

```ts
// composables/useAsync.ts
import { ref, type Ref } from "vue";

interface UseAsyncReturn<T> {
  data: Ref<T | null>;
  error: Ref<Error | null>;
  loading: Ref<boolean>;
  execute: (...args: unknown[]) => Promise<T | null>;
  reset: () => void;
}

export function useAsync<T>(
  asyncFn: (...args: unknown[]) => Promise<T>
): UseAsyncReturn<T> {
  const data = ref<T | null>(null) as Ref<T | null>;
  const error = ref<Error | null>(null);
  const loading = ref(false);

  async function execute(...args: unknown[]): Promise<T | null> {
    loading.value = true;
    error.value = null;
    try {
      const result = await asyncFn(...args);
      data.value = result;
      return result;
    } catch (err) {
      error.value = err instanceof Error ? err : new Error(String(err));
      return null;
    } finally {
      loading.value = false;
    }
  }

  function reset() {
    data.value = null;
    error.value = null;
    loading.value = false;
  }

  return { data, error, loading, execute, reset };
}
```

**useFetch composable with abort and caching**:

```ts
// composables/useFetch.ts
import { ref, watch, toValue, type MaybeRefOrGetter, type Ref } from "vue";

interface UseFetchOptions {
  immediate?: boolean;
  refetch?: boolean;
}

interface UseFetchReturn<T> {
  data: Ref<T | null>;
  error: Ref<Error | null>;
  loading: Ref<boolean>;
  execute: () => Promise<void>;
  abort: () => void;
}

const cache = new Map<string, { data: unknown; timestamp: number }>();
const STALE_TIME = 5 * 60 * 1000;

export function useFetch<T>(
  url: MaybeRefOrGetter<string>,
  options: UseFetchOptions = {}
): UseFetchReturn<T> {
  const { immediate = true, refetch = true } = options;

  const data = ref<T | null>(null) as Ref<T | null>;
  const error = ref<Error | null>(null);
  const loading = ref(false);
  let controller: AbortController | null = null;

  async function execute(): Promise<void> {
    const resolvedUrl = toValue(url);

    // Check cache first
    const cached = cache.get(resolvedUrl);
    if (cached && Date.now() - cached.timestamp < STALE_TIME) {
      data.value = cached.data as T;
      return;
    }

    abort();
    controller = new AbortController();
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(resolvedUrl, {
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const json: T = await response.json();
      data.value = json;
      cache.set(resolvedUrl, { data: json, timestamp: Date.now() });
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        error.value = err;
      }
    } finally {
      loading.value = false;
    }
  }

  function abort() {
    controller?.abort();
    controller = null;
  }

  if (refetch) {
    watch(() => toValue(url), execute);
  }

  if (immediate) {
    execute();
  }

  return { data, error, loading, execute, abort };
}
```

**useForm composable with validation**:

```ts
// composables/useForm.ts
import { reactive, computed, type UnwrapNestedRefs } from "vue";

type ValidationRule<T> = (value: T) => string | true;
type FieldRules<T> = { [K in keyof T]?: ValidationRule<T[K]>[] };

interface UseFormReturn<T extends Record<string, unknown>> {
  fields: UnwrapNestedRefs<T>;
  errors: Record<keyof T, string[]>;
  isValid: boolean;
  isDirty: boolean;
  validate: () => boolean;
  validateField: (field: keyof T) => void;
  reset: () => void;
  handleSubmit: (onSubmit: (values: T) => void | Promise<void>) => (e: Event) => void;
}

export function useForm<T extends Record<string, unknown>>(
  initialValues: T,
  rules: FieldRules<T> = {}
): UseFormReturn<T> {
  const fields = reactive({ ...initialValues }) as UnwrapNestedRefs<T>;
  const errors = reactive<Record<keyof T, string[]>>(
    Object.keys(initialValues).reduce(
      (acc, key) => ({ ...acc, [key]: [] }),
      {} as Record<keyof T, string[]>
    )
  );
  const touched = reactive<Record<keyof T, boolean>>(
    Object.keys(initialValues).reduce(
      (acc, key) => ({ ...acc, [key]: false }),
      {} as Record<keyof T, boolean>
    )
  );

  const isValid = computed(() =>
    Object.values(errors).every(
      (fieldErrors) => (fieldErrors as string[]).length === 0
    )
  );

  const isDirty = computed(() =>
    Object.keys(initialValues).some(
      (key) => fields[key as keyof T] !== initialValues[key as keyof T]
    )
  );

  function validateField(field: keyof T) {
    const fieldRules = rules[field] ?? [];
    const value = fields[field];
    const fieldErrors: string[] = [];
    for (const rule of fieldRules) {
      const result = rule(value as T[keyof T]);
      if (result !== true) fieldErrors.push(result);
    }
    errors[field] = fieldErrors as never;
  }

  function validate(): boolean {
    for (const field of Object.keys(rules) as (keyof T)[]) {
      validateField(field);
    }
    return isValid.value;
  }

  function reset() {
    Object.assign(fields, initialValues);
    for (const key of Object.keys(errors)) {
      errors[key as keyof T] = [] as never;
    }
  }

  function handleSubmit(onSubmit: (values: T) => void | Promise<void>) {
    return async (e: Event) => {
      e.preventDefault();
      if (validate()) {
        await onSubmit({ ...fields } as T);
      }
    };
  }

  return { fields, errors, isValid, isDirty, validate, validateField, reset, handleSubmit };
}
```
