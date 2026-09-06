### Step 7: Test with Vitest and Vue Test Utils

**Component testing fundamentals**:

```ts
// components/__tests__/LoginForm.test.ts
import { describe, it, expect, vi } from "vitest";
import { mount } from "@vue/test-utils";
import LoginForm from "../LoginForm.vue";

describe("LoginForm", () => {
  it("submits credentials when form is valid", async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find('input[name="email"]').setValue("user@example.com");
    await wrapper.find('input[name="password"]').setValue("s3cret!");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toBeTruthy();
    expect(wrapper.emitted("submit")![0]).toEqual([
      { email: "user@example.com", password: "s3cret!" },
    ]);
  });

  it("shows validation errors for empty fields", async () => {
    const wrapper = mount(LoginForm);

    await wrapper.find("form").trigger("submit");

    expect(wrapper.text()).toContain("Email is required");
    expect(wrapper.text()).toContain("Password is required");
    expect(wrapper.emitted("submit")).toBeFalsy();
  });

  it("disables submit button while loading", async () => {
    const wrapper = mount(LoginForm, {
      props: { loading: true },
    });

    const button = wrapper.find('button[type="submit"]');
    expect(button.attributes("disabled")).toBeDefined();
    expect(button.text()).toBe("Signing in...");
  });

  it("renders slot content in the footer", () => {
    const wrapper = mount(LoginForm, {
      slots: {
        footer: '<a href="/forgot">Forgot password?</a>',
      },
    });

    expect(wrapper.find("a").text()).toBe("Forgot password?");
    expect(wrapper.find("a").attributes("href")).toBe("/forgot");
  });
});
```

**Testing composables**:

```ts
// composables/__tests__/useFetch.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { ref, nextTick } from "vue";
import { useFetch } from "../useFetch";

describe("useFetch", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches data on mount when immediate is true", async () => {
    const mockData = { id: 1, name: "Product" };
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    const { data, loading, error } = useFetch<typeof mockData>("/api/products/1");

    expect(loading.value).toBe(true);
    await vi.waitFor(() => expect(loading.value).toBe(false));

    expect(data.value).toEqual(mockData);
    expect(error.value).toBeNull();
  });

  it("sets error on network failure", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"));

    const { data, error, loading } = useFetch("/api/products/1");

    await vi.waitFor(() => expect(loading.value).toBe(false));

    expect(data.value).toBeNull();
    expect(error.value?.message).toBe("Network error");
  });

  it("refetches when URL changes", async () => {
    const url = ref("/api/products/1");
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 1 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 2 }),
      } as Response);

    const { data } = useFetch<{ id: number }>(url);
    await vi.waitFor(() => expect(data.value?.id).toBe(1));

    url.value = "/api/products/2";
    await vi.waitFor(() => expect(data.value?.id).toBe(2));

    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it("does not fetch when immediate is false", () => {
    const { loading } = useFetch("/api/products", { immediate: false });

    expect(fetch).not.toHaveBeenCalled();
    expect(loading.value).toBe(false);
  });
});
```

**Testing with router and Pinia stores**:

```ts
// pages/__tests__/ProductDetailPage.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createTestingPinia } from "@pinia/testing";
import { createRouter, createMemoryHistory } from "vue-router";
import ProductDetailPage from "../ProductDetailPage.vue";
import { useProductStore } from "../../stores/useProductStore";

function createTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/products/:id", name: "product-detail", component: ProductDetailPage },
      { path: "/products", name: "products", component: { template: "<div />" } },
    ],
  });
}

describe("ProductDetailPage", () => {
  let router: ReturnType<typeof createTestRouter>;

  beforeEach(async () => {
    router = createTestRouter();
    await router.push("/products/abc-123");
    await router.isReady();
  });

  it("displays product details from the store", () => {
    const wrapper = mount(ProductDetailPage, {
      global: {
        plugins: [
          router,
          createTestingPinia({
            initialState: {
              products: {
                products: [
                  { id: "abc-123", name: "Widget", price: 29.99, category: "tools", inStock: true },
                ],
              },
            },
          }),
        ],
      },
    });

    expect(wrapper.text()).toContain("Widget");
    expect(wrapper.text()).toContain("29.99");
  });

  it("calls fetchProducts on mount if store is empty", () => {
    const wrapper = mount(ProductDetailPage, {
      global: {
        plugins: [router, createTestingPinia({ stubActions: false })],
      },
    });

    const store = useProductStore();
    expect(store.fetchProducts).toHaveBeenCalled();
  });

  it("navigates back to product list on delete", async () => {
    const wrapper = mount(ProductDetailPage, {
      global: {
        plugins: [
          router,
          createTestingPinia({
            initialState: {
              products: {
                products: [
                  { id: "abc-123", name: "Widget", price: 29.99, category: "tools", inStock: true },
                ],
              },
            },
          }),
        ],
      },
    });

    await wrapper.find('[data-testid="delete-button"]').trigger("click");
    await wrapper.find('[data-testid="confirm-delete"]').trigger("click");

    expect(router.currentRoute.value.name).toBe("products");
  });
});
```
