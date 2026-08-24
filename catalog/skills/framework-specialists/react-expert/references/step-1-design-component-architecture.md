### Step 1: Design Component Architecture

**Composition Pattern** (preferred for most cases):

```tsx
// Compose small, focused components instead of monolithic ones
interface CardProps {
  children: React.ReactNode;
  className?: string;
}

function Card({ children, className }: CardProps) {
  return <div className={`card ${className ?? ""}`}>{children}</div>;
}

function CardHeader({ children }: { children: React.ReactNode }) {
  return <div className="card-header">{children}</div>;
}

function CardBody({ children }: { children: React.ReactNode }) {
  return <div className="card-body">{children}</div>;
}

// Usage: composable, flexible
function UserProfile({ user }: { user: User }) {
  return (
    <Card>
      <CardHeader>
        <h2>{user.name}</h2>
      </CardHeader>
      <CardBody>
        <p>{user.bio}</p>
      </CardBody>
    </Card>
  );
}
```

**Compound Component Pattern** (for tightly coupled component families):

```tsx
import { createContext, useContext, useState, type ReactNode } from "react";

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabs() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("Tab components must be used within <Tabs>");
  return ctx;
}

function Tabs({ defaultTab, children }: { defaultTab: string; children: ReactNode }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div role="tablist">{children}</div>
    </TabsContext.Provider>
  );
}

function TabTrigger({ value, children }: { value: string; children: ReactNode }) {
  const { activeTab, setActiveTab } = useTabs();
  return (
    <button
      role="tab"
      aria-selected={activeTab === value}
      onClick={() => setActiveTab(value)}
    >
      {children}
    </button>
  );
}

function TabContent({ value, children }: { value: string; children: ReactNode }) {
  const { activeTab } = useTabs();
  if (activeTab !== value) return null;
  return <div role="tabpanel">{children}</div>;
}

// Attach sub-components for clean API
Tabs.Trigger = TabTrigger;
Tabs.Content = TabContent;

// Usage
function SettingsPage() {
  return (
    <Tabs defaultTab="general">
      <Tabs.Trigger value="general">General</Tabs.Trigger>
      <Tabs.Trigger value="security">Security</Tabs.Trigger>
      <Tabs.Content value="general"><GeneralSettings /></Tabs.Content>
      <Tabs.Content value="security"><SecuritySettings /></Tabs.Content>
    </Tabs>
  );
}
```

**Render Props** (for sharing stateful logic with flexible rendering):

```tsx
interface MousePosition {
  x: number;
  y: number;
}

function MouseTracker({
  render,
}: {
  render: (pos: MousePosition) => ReactNode;
}) {
  const [position, setPosition] = useState<MousePosition>({ x: 0, y: 0 });

  return (
    <div onMouseMove={(e) => setPosition({ x: e.clientX, y: e.clientY })}>
      {render(position)}
    </div>
  );
}

// Usage
<MouseTracker render={({ x, y }) => <Cursor x={x} y={y} />} />;
```
