# React Performance Patterns Reference

Quick-lookup guide for React rendering optimization patterns. Use alongside the main react-expert skill when performance tuning is the primary focus.

## Memoization Decision Matrix

| Scenario | Tool | When to Use | When to Skip |
|----------|------|-------------|-------------|
| Expensive child re-renders | `React.memo` | Parent re-renders frequently with same props | Props change on every render (objects, callbacks) |
| Expensive computation | `useMemo` | Computation is O(n) or worse, runs on every render | Simple lookups, primitive comparisons |
| Callback identity stability | `useCallback` | Passed to memoized children or used in effect deps | Inline handlers on native elements |
| Ref-stable value | `useRef` | Value needed across renders without triggering re-render | Values that should trigger re-render |

## React.memo with Custom Comparison

```tsx
interface DataTableProps {
  rows: readonly Row[];
  sortColumn: string;
  onRowClick: (id: string) => void;
}

const DataTable = React.memo(
  function DataTable({ rows, sortColumn, onRowClick }: DataTableProps) {
    return (
      <table>
        <thead>
          <tr><th>{sortColumn}</th></tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} onClick={() => onRowClick(row.id)}>
              <td>{row[sortColumn]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  },
  (prev, next) =>
    prev.sortColumn === next.sortColumn &&
    prev.rows.length === next.rows.length &&
    prev.rows.every((row, i) => row.id === next.rows[i].id),
);
```

## Code Splitting Patterns

```tsx
// Route-level splitting (most common)
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Settings = lazy(() => import("./pages/Settings"));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}

// Component-level splitting (heavy components)
const HeavyChart = lazy(() => import("./components/HeavyChart"));

function AnalyticsPanel({ showChart }: { showChart: boolean }) {
  return (
    <div>
      <Summary />
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

## Virtual Scrolling with @tanstack/react-virtual

```tsx
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 5,
  });

  return (
    <div ref={parentRef} style={{ height: "600px", overflow: "auto" }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <ItemRow item={items[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Common Performance Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Object literal in JSX props | Creates new object every render, breaks memo | Extract to useMemo or module-level constant |
| Inline arrow in JSX | Creates new function every render | useCallback for memoized children, or inline for native elements |
| Context with object value | All consumers re-render when any field changes | Split into multiple contexts or use selector pattern |
| Mapping inside render without key | Forces reconciler to re-create DOM nodes | Always provide stable keys (not array index for dynamic lists) |
| useEffect without cleanup | Memory leaks from subscriptions, timers | Return cleanup function in useEffect |
