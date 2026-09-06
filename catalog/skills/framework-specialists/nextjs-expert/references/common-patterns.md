## Common Patterns

### Pattern 1: Optimistic Mutation with Server Action

```tsx
"use client";

import { useOptimistic, useRef } from "react";
import { addComment } from "./actions";

export function CommentForm({ comments }: { comments: Comment[] }) {
  const formRef = useRef<HTMLFormElement>(null);
  const [optimisticComments, addOptimistic] = useOptimistic(
    comments,
    (current, newComment: string) => [
      ...current,
      { id: "temp", text: newComment, pending: true },
    ]
  );

  async function handleSubmit(formData: FormData) {
    const text = formData.get("text") as string;
    addOptimistic(text);
    formRef.current?.reset();
    await addComment(formData);
  }

  return (
    <>
      <ul>
        {optimisticComments.map((c) => (
          <li key={c.id} style={{ opacity: c.pending ? 0.5 : 1 }}>
            {c.text}
          </li>
        ))}
      </ul>
      <form ref={formRef} action={handleSubmit}>
        <input name="text" required />
        <button type="submit">Add Comment</button>
      </form>
    </>
  );
}
```

### Pattern 2: Streaming with Suspense Boundaries

```tsx
// app/products/page.tsx
import { Suspense } from "react";

export default function ProductsPage() {
  return (
    <div>
      <h1>Products</h1>
      {/* Featured loads fast */}
      <Suspense fallback={<FeaturedSkeleton />}>
        <FeaturedProducts />
      </Suspense>
      {/* Reviews are slower, streamed in later */}
      <Suspense fallback={<ReviewsSkeleton />}>
        <RecentReviews />
      </Suspense>
    </div>
  );
}

async function FeaturedProducts() {
  const products = await fetch("https://api.example.com/featured", {
    next: { revalidate: 300 },
  }).then((r) => r.json());

  return (
    <ul>
      {products.map((p: Product) => (
        <li key={p.id}>{p.name}</li>
      ))}
    </ul>
  );
}

async function RecentReviews() {
  // This fetch is slow, but the page renders immediately
  // and streams this section when ready
  const reviews = await fetch("https://api.example.com/reviews", {
    cache: "no-store",
  }).then((r) => r.json());

  return (
    <ul>
      {reviews.map((r: Review) => (
        <li key={r.id}>{r.text} - {r.rating}/5</li>
      ))}
    </ul>
  );
}
```
