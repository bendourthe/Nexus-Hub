### Step 4: Optimize Performance

**React.memo for expensive components**:

```tsx
interface DataTableProps {
  rows: DataRow[];
  columns: Column[];
  onSort: (column: string) => void;
}

const DataTable = React.memo(function DataTable({
  rows,
  columns,
  onSort,
}: DataTableProps) {
  return (
    <table>
      <thead>
        <tr>
          {columns.map((col) => (
            <th key={col.key} onClick={() => onSort(col.key)}>
              {col.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.id}>
            {columns.map((col) => (
              <td key={col.key}>{row[col.key]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
});
```

**Lazy loading with Suspense and code splitting**:

```tsx
import { lazy, Suspense } from "react";

// Split code at the route level
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const UserSettings = lazy(() => import("./pages/UserSettings"));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/settings" element={<UserSettings />} />
      </Routes>
    </Suspense>
  );
}
```

**Performance profiling steps**:

1. Open React DevTools Profiler tab
2. Click "Record" and perform the interaction
3. Review the flame graph: look for components that render unnecessarily
4. For each unnecessary render, determine whether it is caused by:
   - Unstable props (new object/array/function on every render)
   - Context value changing (split contexts or use selectors)
   - Parent re-rendering (wrap child in React.memo)
5. Apply the narrowest fix: useMemo/useCallback for prop stability, React.memo for the component, or context splitting
