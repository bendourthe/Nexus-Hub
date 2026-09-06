## Common Patterns

### Pattern 1: Data Fetching Hook with Caching

```tsx
const cache = new Map<string, { data: unknown; timestamp: number }>();
const STALE_TIME = 5 * 60 * 1000; // 5 minutes

function useFetch<T>(url: string) {
  const [data, setData] = useState<T | null>(() => {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.timestamp < STALE_TIME) {
      return cached.data as T;
    }
    return null;
  });
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(!data);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function load() {
      try {
        const res = await fetch(url, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!cancelled) {
          cache.set(url, { data: json, timestamp: Date.now() });
          setData(json);
        }
      } catch (err) {
        if (!cancelled && err instanceof Error && err.name !== "AbortError") {
          setError(err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; controller.abort(); };
  }, [url]);

  return { data, error, loading };
}
```

### Pattern 2: Controlled Form with Validation

```tsx
function useFormValidation<T extends Record<string, string>>(
  initialValues: T,
  validate: (values: T) => Partial<Record<keyof T, string>>
) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});

  const handleChange = (field: keyof T) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setValues((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleBlur = (field: keyof T) => () => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    setErrors(validate(values));
  };

  const handleSubmit = (onSubmit: (values: T) => void) => (
    e: React.FormEvent
  ) => {
    e.preventDefault();
    const validationErrors = validate(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length === 0) {
      onSubmit(values);
    }
  };

  return { values, errors, touched, handleChange, handleBlur, handleSubmit };
}
```
