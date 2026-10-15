### Step 5: Configure Vue Router Patterns

**Route configuration with lazy loading and typed meta**:

```ts
// router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

// Extend RouteMeta for type-safe meta fields
declare module "vue-router" {
  interface RouteMeta {
    requiresAuth?: boolean;
    roles?: string[];
    title?: string;
    transition?: "slide-left" | "slide-right" | "fade";
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("../layouts/DefaultLayout.vue"),
    children: [
      {
        path: "",
        name: "home",
        component: () => import("../pages/HomePage.vue"),
        meta: { title: "Home" },
      },
      {
        path: "products",
        name: "products",
        component: () => import("../pages/ProductsPage.vue"),
        meta: { title: "Products" },
      },
      {
        path: "products/:id",
        name: "product-detail",
        component: () => import("../pages/ProductDetailPage.vue"),
        props: true,
        meta: { title: "Product Detail" },
      },
    ],
  },
  {
    path: "/dashboard",
    component: () => import("../layouts/DashboardLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "dashboard",
        component: () => import("../pages/DashboardPage.vue"),
        meta: { title: "Dashboard", roles: ["user", "admin"] },
      },
      {
        path: "settings",
        name: "settings",
        component: () => import("../pages/SettingsPage.vue"),
        meta: { title: "Settings", roles: ["user", "admin"] },
      },
      {
        path: "admin",
        name: "admin",
        component: () => import("../pages/AdminPage.vue"),
        meta: { title: "Admin Panel", roles: ["admin"] },
      },
    ],
  },
  {
    path: "/login",
    name: "login",
    component: () => import("../pages/LoginPage.vue"),
    meta: { title: "Sign In" },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../pages/NotFoundPage.vue"),
    meta: { title: "Page Not Found" },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, behavior: "smooth" };
    return { top: 0 };
  },
});

export default router;
```

**Navigation guards for auth and role checking**:

```ts
// router/guards.ts
import type { Router } from "vue-router";
import { useAuthStore } from "../stores/useAuthStore";

export function registerGuards(router: Router) {
  // Global before guard: authentication and authorization
  router.beforeEach(async (to, _from) => {
    const authStore = useAuthStore();

    // Update document title
    document.title = to.meta.title
      ? `${to.meta.title} | MyApp`
      : "MyApp";

    // Check if route requires authentication
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      return {
        name: "login",
        query: { redirect: to.fullPath },
      };
    }

    // Check role-based access
    if (to.meta.roles && to.meta.roles.length > 0) {
      const hasRole = to.meta.roles.some((role) =>
        authStore.user?.roles.includes(role)
      );
      if (!hasRole) {
        return { name: "dashboard" };
      }
    }

    return true;
  });

  // Global after hook: analytics tracking
  router.afterEach((to, from) => {
    if (to.path !== from.path) {
      trackPageView(to.fullPath, to.meta.title);
    }
  });

  // Per-route error handling
  router.onError((error, to) => {
    // Handle lazy-loaded chunk failures (common after deployments)
    if (
      error.message.includes("Failed to fetch dynamically imported module") ||
      error.message.includes("Loading chunk")
    ) {
      window.location.href = to.fullPath;
    }
  });
}

function trackPageView(path: string, title?: string) {
  // Analytics integration point
  console.debug("[Analytics]", { path, title });
}
```

**Programmatic navigation and route composable**:

```vue
<script setup lang="ts">
import { useRouter, useRoute } from "vue-router";
import { computed, watch } from "vue";

const router = useRouter();
const route = useRoute();

// Reactive route params
const productId = computed(() => route.params.id as string);
const searchQuery = computed(() => (route.query.q as string) ?? "");
const currentPage = computed(() => Number(route.query.page) || 1);

// Update query params without full navigation
function updateSearch(query: string) {
  router.replace({
    query: {
      ...route.query,
      q: query || undefined,
      page: undefined, // Reset page when search changes
    },
  });
}

function goToPage(page: number) {
  router.push({
    query: { ...route.query, page: page > 1 ? String(page) : undefined },
  });
}

// Navigate after an action
async function handleDelete(id: string) {
  await deleteProduct(id);
  await router.push({ name: "products" });
}

// Watch route changes for data fetching
watch(
  () => route.params.id,
  (newId) => {
    if (newId) fetchProductDetail(newId as string);
  },
  { immediate: true }
);
</script>
```
