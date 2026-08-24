### Step 9: React 19 Features

**Actions and useActionState**:

```tsx
import { useActionState } from "react";

async function submitForm(
  _prevState: { message: string } | null,
  formData: FormData
) {
  const name = formData.get("name") as string;
  const res = await fetch("/api/contact", {
    method: "POST",
    body: JSON.stringify({ name }),
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) return { message: "Failed to submit" };
  return { message: `Thank you, ${name}!` };
}

function ContactForm() {
  const [state, formAction, isPending] = useActionState(submitForm, null);

  return (
    <form action={formAction}>
      <input name="name" required disabled={isPending} />
      <button type="submit" disabled={isPending}>
        {isPending ? "Submitting..." : "Submit"}
      </button>
      {state?.message && <p>{state.message}</p>}
    </form>
  );
}
```

**useOptimistic for instant UI feedback**:

```tsx
import { useOptimistic } from "react";

function TodoList({ todos, onToggle }: {
  todos: Todo[];
  onToggle: (id: string) => Promise<void>;
}) {
  const [optimisticTodos, addOptimistic] = useOptimistic(
    todos,
    (currentTodos, toggledId: string) =>
      currentTodos.map((t) =>
        t.id === toggledId ? { ...t, done: !t.done } : t
      )
  );

  async function handleToggle(id: string) {
    addOptimistic(id);       // Immediate UI update
    await onToggle(id);      // Actual server call
  }

  return (
    <ul>
      {optimisticTodos.map((todo) => (
        <li key={todo.id}>
          <label>
            <input
              type="checkbox"
              checked={todo.done}
              onChange={() => handleToggle(todo.id)}
            />
            {todo.title}
          </label>
        </li>
      ))}
    </ul>
  );
}
```
