### Step 8: Test with Vitest and Playwright

**Component testing with @testing-library/svelte**:

```ts
// src/lib/components/Counter.test.ts
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import Counter from "./Counter.svelte";

describe("Counter", () => {
  it("renders initial count", () => {
    render(Counter, { props: { initial: 5 } });
    expect(screen.getByText("Count: 5")).toBeInTheDocument();
  });

  it("increments count on button click", async () => {
    const user = userEvent.setup();
    render(Counter, { props: { initial: 0 } });

    const button = screen.getByRole("button", { name: /increment/i });
    await user.click(button);

    expect(screen.getByText("Count: 1")).toBeInTheDocument();
  });

  it("decrements count but not below zero", async () => {
    const user = userEvent.setup();
    render(Counter, { props: { initial: 0 } });

    const button = screen.getByRole("button", { name: /decrement/i });
    await user.click(button);

    expect(screen.getByText("Count: 0")).toBeInTheDocument();
  });

  it("calls onChange callback when count changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(Counter, { props: { initial: 0, onChange } });

    await user.click(screen.getByRole("button", { name: /increment/i }));

    expect(onChange).toHaveBeenCalledWith(1);
  });
});
```

**Testing components with context and stores**:

```ts
// src/lib/components/CartSummary.test.ts
import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach } from "vitest";
import CartSummary from "./CartSummary.svelte";
import { cart } from "$lib/stores/cart.svelte";

describe("CartSummary", () => {
  beforeEach(() => {
    cart.clear();
  });

  it("shows empty cart message when no items", () => {
    render(CartSummary);
    expect(screen.getByText(/cart is empty/i)).toBeInTheDocument();
  });

  it("displays item count and total after adding items", async () => {
    cart.addItem({ id: "1", name: "Widget", price: 9.99 });
    cart.addItem({ id: "2", name: "Gadget", price: 24.99 });

    render(CartSummary);

    expect(screen.getByText(/2 items/i)).toBeInTheDocument();
    expect(screen.getByText(/\$34\.98/)).toBeInTheDocument();
  });

  it("removes item when remove button is clicked", async () => {
    const user = userEvent.setup();
    cart.addItem({ id: "1", name: "Widget", price: 9.99 });

    render(CartSummary);
    await user.click(screen.getByRole("button", { name: /remove widget/i }));

    expect(screen.getByText(/cart is empty/i)).toBeInTheDocument();
  });
});
```

**Testing load functions in isolation**:

```ts
// src/routes/blog/[slug]/+page.server.test.ts
import { describe, it, expect, vi } from "vitest";
import { load } from "./+page.server";

vi.mock("$lib/server/db", () => ({
  db: {
    post: {
      findUnique: vi.fn(),
    },
  },
}));

import { db } from "$lib/server/db";

describe("blog post load function", () => {
  it("returns post data for a valid slug", async () => {
    const mockPost = {
      slug: "hello-world",
      title: "Hello World",
      htmlContent: "<p>Content</p>",
      publishedAt: "2026-01-15",
      excerpt: "A hello world post",
    };

    vi.mocked(db.post.findUnique).mockResolvedValue(mockPost);

    const result = await load({
      params: { slug: "hello-world" },
    } as any);

    expect(result.post).toEqual(mockPost);
    expect(db.post.findUnique).toHaveBeenCalledWith({
      where: { slug: "hello-world" },
    });
  });

  it("throws 404 error for a missing slug", async () => {
    vi.mocked(db.post.findUnique).mockResolvedValue(null);

    await expect(
      load({ params: { slug: "nonexistent" } } as any)
    ).rejects.toMatchObject({
      status: 404,
    });
  });
});
```

**End-to-end testing with Playwright**:

```ts
// tests/e2e/blog.test.ts
import { test, expect } from "@playwright/test";

test.describe("Blog", () => {
  test("displays list of blog posts", async ({ page }) => {
    await page.goto("/blog");

    await expect(page.getByRole("heading", { name: /blog/i })).toBeVisible();
    await expect(page.getByRole("article").first()).toBeVisible();
  });

  test("navigates to individual post and back", async ({ page }) => {
    await page.goto("/blog");

    const firstPost = page.getByRole("article").first();
    const postTitle = await firstPost.getByRole("heading").textContent();
    await firstPost.getByRole("link").click();

    await expect(page.getByRole("heading", { name: postTitle! })).toBeVisible();

    await page.goBack();
    await expect(page.getByRole("heading", { name: /blog/i })).toBeVisible();
  });

  test("creates a new blog post via form", async ({ page }) => {
    // Log in first
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@example.com");
    await page.getByLabel(/password/i).fill("testpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.goto("/blog/new");
    await page.getByLabel(/title/i).fill("E2E Test Post");
    await page.getByLabel(/content/i).fill("This post was created by an E2E test to verify form submission.");
    await page.getByRole("button", { name: /create post/i }).click();

    // Should redirect to the new post
    await expect(page.getByRole("heading", { name: "E2E Test Post" })).toBeVisible();
  });

  test("shows validation errors for empty form", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@example.com");
    await page.getByLabel(/password/i).fill("testpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.goto("/blog/new");
    await page.getByRole("button", { name: /create post/i }).click();

    await expect(page.getByText(/title is required/i)).toBeVisible();
  });
});

test.describe("Dashboard", () => {
  test("redirects unauthenticated users to login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("displays dashboard stats for authenticated users", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email/i).fill("admin@example.com");
    await page.getByLabel(/password/i).fill("testpassword");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.goto("/dashboard");
    await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
    await expect(page.getByText(/total posts/i)).toBeVisible();
  });
});
```

**Vitest configuration for SvelteKit**:

```ts
// vite.config.ts
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"],
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      include: ["src/lib/**/*.{ts,svelte}", "src/routes/**/*.{ts,svelte}"],
      thresholds: {
        lines: 80,
        branches: 70,
      },
    },
  },
});
```

```ts
// src/tests/setup.ts
import "@testing-library/jest-dom/vitest";
```

**Playwright configuration**:

```ts
// playwright.config.ts
import type { PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = {
  webServer: {
    command: "npm run build && npm run preview",
    port: 4173,
    reuseExistingServer: !process.env.CI,
  },
  testDir: "tests/e2e",
  testMatch: /(.+\.)?(test|spec)\.[jt]s/,
  use: {
    baseURL: "http://localhost:4173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
};

export default config;
```
