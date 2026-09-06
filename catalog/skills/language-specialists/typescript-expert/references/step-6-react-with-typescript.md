### Step 6: React with TypeScript

**Component Typing**:

Type React components using function declarations with explicit prop types. Avoid `React.FC` because it implicitly includes `children` in the props and obscures the return type.

```typescript
// Basic component with typed props
interface ButtonProps {
  label: string;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  onClick: () => void;
}

function Button({ label, variant = "primary", disabled = false, onClick }: ButtonProps): React.ReactElement {
  return (
    <button className={`btn btn-${variant}`} disabled={disabled} onClick={onClick}>
      {label}
    </button>
  );
}

// Children prop - be explicit about what children you accept
interface CardProps {
  title: string;
  children: React.ReactNode; // Accepts anything renderable
}

function Card({ title, children }: CardProps): React.ReactElement {
  return (
    <div className="card">
      <h2>{title}</h2>
      <div className="card-body">{children}</div>
    </div>
  );
}

// Render prop pattern
interface DataFetcherProps<T> {
  url: string;
  render: (data: T, loading: boolean) => React.ReactNode;
}

function DataFetcher<T>({ url, render }: DataFetcherProps<T>): React.ReactElement {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(url)
      .then((res) => res.json())
      .then((json: T) => { setData(json); setLoading(false); });
  }, [url]);

  return <>{data !== null ? render(data, loading) : null}</>;
}
```

**Hooks Typing**:

When TypeScript cannot infer the type of a hook's state (for example, when the initial value is `null` or an empty array), provide an explicit generic argument. For `useRef`, distinguish between refs to DOM elements and refs to mutable values.

```typescript
// useState with explicit type
const [user, setUser] = React.useState<User | null>(null);
const [items, setItems] = React.useState<Item[]>([]);

// useReducer with typed state and actions
interface CounterState {
  count: number;
}

type CounterAction =
  | { type: "INCREMENT"; amount: number }
  | { type: "DECREMENT"; amount: number }
  | { type: "RESET" };

function counterReducer(state: CounterState, action: CounterAction): CounterState {
  switch (action.type) {
    case "INCREMENT":
      return { count: state.count + action.amount };
    case "DECREMENT":
      return { count: state.count - action.amount };
    case "RESET":
      return { count: 0 };
  }
}

function Counter(): React.ReactElement {
  const [state, dispatch] = React.useReducer(counterReducer, { count: 0 });

  return (
    <div>
      <span>{state.count}</span>
      <button onClick={() => dispatch({ type: "INCREMENT", amount: 1 })}>+</button>
    </div>
  );
}

// useRef for DOM elements vs mutable values
function TextInput(): React.ReactElement {
  // DOM ref - pass null, TypeScript knows it may be null until attached
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Mutable ref - for storing values that do not trigger re-renders
  const renderCount = React.useRef<number>(0);

  React.useEffect(() => {
    renderCount.current += 1;
  });

  function focusInput(): void {
    inputRef.current?.focus();
  }

  return <input ref={inputRef} />;
}

// Custom hook with typed return and an explicit runtime parser
function useLocalStorage<T>(
  key: string,
  initialValue: T,
  parse: (value: unknown) => T | undefined,
): [T, (value: T) => void] {
  const [stored, setStored] = React.useState<T>(() => {
    const item = window.localStorage.getItem(key);
    if (item === null) return initialValue;
    const decoded: unknown = JSON.parse(item);
    return parse(decoded) ?? initialValue;
  });

  function setValue(value: T): void {
    setStored(value);
    window.localStorage.setItem(key, JSON.stringify(value));
  }

  return [stored, setValue];
}
```

**Context Typing and Event Handlers**:

Create typed context with a factory pattern that avoids the need for a default value while keeping the API ergonomic. For event handlers, use React's built-in event types rather than the DOM ones directly.

```typescript
// Typed context - factory pattern (no awkward default value)
interface AuthContext {
  user: User | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContext | null>(null);

function useAuth(): AuthContext {
  const context = React.useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

function AuthProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  const [user, setUser] = React.useState<User | null>(null);

  const login = async (credentials: Credentials): Promise<void> => {
    const user = await api.login(credentials);
    setUser(user);
  };

  const logout = (): void => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Event handler typing
function Form(): React.ReactElement {
  function handleSubmit(event: React.FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    // Process form...
  }

  function handleChange(event: React.ChangeEvent<HTMLInputElement>): void {
    console.log(event.target.value);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>): void {
    if (event.key === "Enter") {
      // Submit...
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input onChange={handleChange} onKeyDown={handleKeyDown} />
    </form>
  );
}
```

**Polymorphic Components**:

A polymorphic component accepts an `as` prop that controls which HTML element (or React component) it renders. This pattern is common in design system libraries and requires careful typing to ensure that the resulting props match the chosen element.

```typescript
// Polymorphic component - renders as any HTML element
type PolymorphicProps<E extends React.ElementType, P = object> = P &
  Omit<React.ComponentPropsWithoutRef<E>, keyof P | "as"> & {
    as?: E;
  };

type TextProps<E extends React.ElementType = "span"> = PolymorphicProps<E, {
  size?: "sm" | "md" | "lg";
  weight?: "normal" | "bold";
}>;

function Text<E extends React.ElementType = "span">({
  as,
  size = "md",
  weight = "normal",
  children,
  ...rest
}: TextProps<E> & { children?: React.ReactNode }): React.ReactElement {
  const Component = as ?? "span";
  return (
    <Component className={`text-${size} font-${weight}`} {...rest}>
      {children}
    </Component>
  );
}

// Usage - props are validated against the chosen element
<Text>Default span</Text>
<Text as="h1" size="lg">Heading</Text>
<Text as="a" href="/about" size="sm">Link</Text>
// <Text as="a" disabled>Error</Text>  // Error: 'disabled' does not exist on anchor
```
