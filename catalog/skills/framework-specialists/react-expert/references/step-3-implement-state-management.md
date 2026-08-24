### Step 3: Implement State Management

**Context API (suitable for low-frequency updates)**:

```tsx
interface ThemeContextValue {
  theme: "light" | "dark";
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const toggle = useCallback(
    () => setTheme((t) => (t === "light" ? "dark" : "light")),
    []
  );
  // Memoize the context value to prevent unnecessary re-renders
  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
```

**Zustand (recommended for most applications)**:

```tsx
import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartStore {
  items: CartItem[];
  addItem: (item: Omit<CartItem, "quantity">) => void;
  removeItem: (id: string) => void;
  clearCart: () => void;
  total: () => number;
}

export const useCartStore = create<CartStore>()(
  devtools(
    persist(
      (set, get) => ({
        items: [],
        addItem: (item) =>
          set((state) => {
            const existing = state.items.find((i) => i.id === item.id);
            if (existing) {
              return {
                items: state.items.map((i) =>
                  i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i
                ),
              };
            }
            return { items: [...state.items, { ...item, quantity: 1 }] };
          }),
        removeItem: (id) =>
          set((state) => ({
            items: state.items.filter((i) => i.id !== id),
          })),
        clearCart: () => set({ items: [] }),
        total: () =>
          get().items.reduce((sum, i) => sum + i.price * i.quantity, 0),
      }),
      { name: "cart-storage" }
    )
  )
);
```
