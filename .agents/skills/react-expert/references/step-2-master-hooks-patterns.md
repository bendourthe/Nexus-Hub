### Step 2: Master Hooks Patterns

**useState with complex state**:

```tsx
interface FormState {
  name: string;
  email: string;
  errors: Record<string, string>;
}

function useForm(initial: FormState) {
  const [state, setState] = useState<FormState>(initial);

  const setField = useCallback(
    <K extends keyof FormState>(field: K, value: FormState[K]) => {
      setState((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const reset = useCallback(() => setState(initial), [initial]);

  return { state, setField, reset };
}
```

**useEffect: correct dependency management**:

```tsx
// Fetch data with cleanup and race condition protection
function useUser(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;           // Guard against stale responses
    const controller = new AbortController();

    async function fetchUser() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: User = await res.json();
        if (!cancelled) setUser(data);
      } catch (err) {
        if (!cancelled && err instanceof Error && err.name !== "AbortError") {
          setError(err);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchUser();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [userId]);

  return { user, error, loading };
}
```

**Custom hook: debounced value**:

```tsx
function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

// Usage in search
function SearchInput() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      searchAPI(debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={(e) => setQuery(e.target.value)} />;
}
```

**useRef for imperative handles and stable references**:

```tsx
function VideoPlayer({ src }: { src: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const previousSrc = useRef(src);

  useEffect(() => {
    if (previousSrc.current !== src) {
      videoRef.current?.load();
      previousSrc.current = src;
    }
  }, [src]);

  return (
    <div>
      <video ref={videoRef} src={src} />
      <button onClick={() => videoRef.current?.play()}>Play</button>
      <button onClick={() => videoRef.current?.pause()}>Pause</button>
    </div>
  );
}
```
