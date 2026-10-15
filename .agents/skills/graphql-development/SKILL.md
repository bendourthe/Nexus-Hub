---
name: graphql-development
description: GraphQL API development including schema design, resolvers, N+1 prevention, subscriptions, and federation. Use when building GraphQL APIs, optimizing query performance, or implementing real-time features.
summary_l0: "Build GraphQL APIs with schema design, DataLoader, subscriptions, and federation"
overview_l1: "This skill provides comprehensive guidance on building production-quality GraphQL APIs, covering schema design, resolver implementation, the N+1 problem with DataLoader, subscriptions, Apollo Federation, caching, security, and client-side patterns. Use it when designing GraphQL schemas (types, interfaces, unions, enums), implementing resolvers with batching and caching, preventing N+1 query problems, adding real-time features with subscriptions, implementing pagination (Relay cursor, offset-based), securing GraphQL APIs (authentication, authorization, query complexity), setting up Apollo Federation for microservices, or optimizing client-side data fetching. Key capabilities include schema-first design, resolver architecture, DataLoader batching, subscription implementation, Relay-compliant pagination, query complexity analysis, federation gateway setup, and client cache management. The expected output is a production-ready GraphQL API with optimized resolvers, proper security controls, and client integration patterns. Trigger phrases: GraphQL, schema, resolver, DataLoader, subscription, mutation, query complexity, N+1, federation, Apollo, SDL, GraphQL API."
---

# GraphQL Development

Comprehensive guidance on building production-quality GraphQL APIs, covering schema design, resolver implementation, the N+1 problem with DataLoader, subscriptions, Apollo Federation, caching strategies, security, and client-side patterns.

## When to Use This Skill

Use this skill for:

- Designing GraphQL schemas (types, interfaces, unions, enums)
- Implementing resolvers with batching and caching
- Preventing N+1 query problems with DataLoader
- Adding real-time features with subscriptions
- Implementing pagination (Relay cursor, offset-based)
- Securing GraphQL APIs (authentication, authorization, query complexity)
- Setting up Apollo Federation for microservices
- Optimizing client-side data fetching (Apollo Client, urql)

**Trigger phrases**: "GraphQL", "schema", "resolver", "DataLoader", "subscription", "mutation", "query complexity", "N+1", "federation", "Apollo", "SDL", "GraphQL API"

## What This Skill Does

Provides production-ready GraphQL patterns including:

- **Schema Design**: Types, interfaces, unions, enums, input types, custom scalars
- **Resolvers**: Field-level resolution, context injection, error handling
- **Performance**: DataLoader for batching, query complexity analysis, persisted queries
- **Real-Time**: Subscriptions via WebSocket, pub/sub patterns
- **Federation**: Apollo Federation gateway, subgraph design, entity resolution
- **Security**: Authentication, field-level authorization, depth limiting, rate limiting
- **Clients**: Apollo Client, urql, cache normalization

## Instructions

### Step 1: Design the Schema

**Schema Design Principles**:

```
1. Design for the client's needs, not the database schema
2. Use nullable fields by default; make non-null only when guaranteed
3. Prefer specific types over generic ones
4. Use interfaces for shared fields, unions for polymorphic returns
5. Suffix input types with "Input", payloads with "Payload"
6. Always return the modified object in mutation payloads
```

**Complete Schema Example (SDL)**:

```graphql
# ============================================
# Custom Scalars
# ============================================
scalar DateTime
scalar EmailAddress
scalar URL

# ============================================
# Enums
# ============================================
enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

enum SortDirection {
  ASC
  DESC
}

# ============================================
# Interfaces
# ============================================
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

# ============================================
# Types
# ============================================
type User implements Node & Timestamped {
  id: ID!
  email: EmailAddress!
  name: String!
  avatar: URL
  orders(first: Int, after: String, status: OrderStatus): OrderConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Product implements Node & Timestamped {
  id: ID!
  name: String!
  description: String
  price: Float!
  category: Category!
  images: [URL!]!
  inStock: Boolean!
  reviews(first: Int, after: String): ReviewConnection!
  averageRating: Float
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Order implements Node & Timestamped {
  id: ID!
  user: User!
  items: [OrderItem!]!
  status: OrderStatus!
  total: Float!
  shippingAddress: Address!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type OrderItem {
  product: Product!
  quantity: Int!
  unitPrice: Float!
  lineTotal: Float!
}

type Address {
  street: String!
  city: String!
  state: String
  postalCode: String!
  country: String!
}

type Category implements Node {
  id: ID!
  name: String!
  slug: String!
  products(first: Int, after: String): ProductConnection!
}

type Review implements Node & Timestamped {
  id: ID!
  author: User!
  product: Product!
  rating: Int!
  comment: String
  createdAt: DateTime!
  updatedAt: DateTime!
}

# ============================================
# Relay-Style Pagination
# ============================================
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type ProductConnection {
  edges: [ProductEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ProductEdge {
  node: Product!
  cursor: String!
}

type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type ReviewConnection {
  edges: [ReviewEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type ReviewEdge {
  node: Review!
  cursor: String!
}

# ============================================
# Inputs
# ============================================
input CreateOrderInput {
  items: [OrderItemInput!]!
  shippingAddress: AddressInput!
}

input OrderItemInput {
  productId: ID!
  quantity: Int!
}

input AddressInput {
  street: String!
  city: String!
  state: String
  postalCode: String!
  country: String!
}

input ProductFilterInput {
  categoryId: ID
  minPrice: Float
  maxPrice: Float
  inStock: Boolean
  search: String
}

input ProductSortInput {
  field: ProductSortField!
  direction: SortDirection!
}

enum ProductSortField {
  NAME
  PRICE
  CREATED_AT
  RATING
}

# ============================================
# Mutation Payloads (always return the object)
# ============================================
type CreateOrderPayload {
  order: Order
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: String!
}

# ============================================
# Queries, Mutations, Subscriptions
# ============================================
type Query {
  # Single resource (nullable for 404)
  user(id: ID!): User
  product(id: ID!): Product
  order(id: ID!): Order

  # Collections with filtering, sorting, pagination
  products(
    filter: ProductFilterInput
    sort: ProductSortInput
    first: Int
    after: String
  ): ProductConnection!

  # Viewer pattern (current authenticated user)
  viewer: User
}

type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
  cancelOrder(id: ID!): CreateOrderPayload!
  addReview(productId: ID!, rating: Int!, comment: String): Review!
}

type Subscription {
  orderStatusChanged(orderId: ID!): Order!
  newReview(productId: ID!): Review!
}
```

### Step 2: Implement Resolvers (Node.js)

**Resolver Structure with Context**:

```javascript
// resolvers/index.js
const { GraphQLDateTime } = require("graphql-scalars");

const resolvers = {
  DateTime: GraphQLDateTime,

  Query: {
    viewer: (_parent, _args, context) => {
      // context.user is set by auth middleware
      if (!context.user) return null;
      return context.dataSources.users.getById(context.user.id);
    },

    product: (_parent, { id }, context) => {
      return context.dataSources.products.getById(id);
    },

    products: (_parent, { filter, sort, first = 20, after }, context) => {
      return context.dataSources.products.getConnection({
        filter,
        sort,
        first: Math.min(first, 100), // Cap page size
        after,
      });
    },
  },

  Mutation: {
    createOrder: async (_parent, { input }, context) => {
      if (!context.user) {
        return {
          order: null,
          errors: [{ message: "Authentication required", code: "UNAUTHENTICATED" }],
        };
      }

      try {
        const order = await context.dataSources.orders.create(context.user.id, input);
        // Publish event for subscriptions
        context.pubsub.publish(`ORDER_STATUS_${order.id}`, { orderStatusChanged: order });
        return { order, errors: [] };
      } catch (error) {
        return {
          order: null,
          errors: [{ message: error.message, code: "VALIDATION_ERROR", field: error.field }],
        };
      }
    },
  },

  // Field-level resolvers
  User: {
    orders: (user, { first = 10, after, status }, context) => {
      return context.dataSources.orders.getByUser(user.id, { first, after, status });
    },
  },

  Product: {
    category: (product, _args, context) => {
      // Uses DataLoader for batching (prevents N+1)
      return context.dataSources.categories.getById(product.categoryId);
    },
    reviews: (product, { first = 10, after }, context) => {
      return context.dataSources.reviews.getByProduct(product.id, { first, after });
    },
    averageRating: (product, _args, context) => {
      return context.dataSources.reviews.getAverageRating(product.id);
    },
  },

  Order: {
    user: (order, _args, context) => {
      return context.dataSources.users.getById(order.userId);
    },
    items: (order, _args, context) => {
      return context.dataSources.orderItems.getByOrder(order.id);
    },
  },

  OrderItem: {
    product: (item, _args, context) => {
      return context.dataSources.products.getById(item.productId);
    },
  },

  Subscription: {
    orderStatusChanged: {
      subscribe: (_parent, { orderId }, context) => {
        if (!context.user) throw new Error("Authentication required");
        return context.pubsub.asyncIterator(`ORDER_STATUS_${orderId}`);
      },
    },
    newReview: {
      subscribe: (_parent, { productId }, context) => {
        return context.pubsub.asyncIterator(`NEW_REVIEW_${productId}`);
      },
    },
  },
};
```

### Step 3: Solve the N+1 Problem with DataLoader

**DataLoader Setup**:

```javascript
// dataloaders.js
const DataLoader = require("dataloader");

function createLoaders(db) {
  return {
    // Batch: given [id1, id2, id3], run ONE query instead of three
    userById: new DataLoader(async (ids) => {
      const users = await db.query(
        "SELECT * FROM users WHERE id = ANY($1)",
        [ids]
      );
      // IMPORTANT: return results in the same order as the input IDs
      const userMap = new Map(users.map((u) => [u.id, u]));
      return ids.map((id) => userMap.get(id) || null);
    }),

    productById: new DataLoader(async (ids) => {
      const products = await db.query(
        "SELECT * FROM products WHERE id = ANY($1)",
        [ids]
      );
      const map = new Map(products.map((p) => [p.id, p]));
      return ids.map((id) => map.get(id) || null);
    }),

    categoryById: new DataLoader(async (ids) => {
      const categories = await db.query(
        "SELECT * FROM categories WHERE id = ANY($1)",
        [ids]
      );
      const map = new Map(categories.map((c) => [c.id, c]));
      return ids.map((id) => map.get(id) || null);
    }),

    // One-to-many DataLoader (orders by user)
    ordersByUserId: new DataLoader(async (userIds) => {
      const orders = await db.query(
        "SELECT * FROM orders WHERE user_id = ANY($1) ORDER BY created_at DESC",
        [userIds]
      );
      const grouped = new Map();
      for (const order of orders) {
        const list = grouped.get(order.user_id) || [];
        list.push(order);
        grouped.set(order.user_id, list);
      }
      return userIds.map((id) => grouped.get(id) || []);
    }),
  };
}

// Create loaders per-request (they cache within a single request)
// In Apollo Server:
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => ({
    user: req.user,
    dataSources: createLoaders(db), // Fresh loaders per request
  }),
});
```

**Python DataLoader (Strawberry + aiodataloader)**:

```python
from aiodataloader import DataLoader
from typing import list, Optional

class UserLoader(DataLoader):
    async def batch_load_fn(self, user_ids: list[str]) -> list[Optional[dict]]:
        """Load multiple users in a single query."""
        users = await db.fetch_all(
            "SELECT * FROM users WHERE id = ANY(:ids)",
            {"ids": user_ids},
        )
        user_map = {u["id"]: u for u in users}
        return [user_map.get(uid) for uid in user_ids]

class ProductLoader(DataLoader):
    async def batch_load_fn(self, product_ids: list[str]) -> list[Optional[dict]]:
        products = await db.fetch_all(
            "SELECT * FROM products WHERE id = ANY(:ids)",
            {"ids": product_ids},
        )
        product_map = {p["id"]: p for p in products}
        return [product_map.get(pid) for pid in product_ids]

# Usage in resolvers
async def resolve_user(order, info):
    return await info.context["loaders"].user.load(order.user_id)
```

### Step 4: Implement Subscriptions

**WebSocket Subscription Server (Node.js)**:

```javascript
const { createServer } = require("http");
const { WebSocketServer } = require("ws");
const { useServer } = require("graphql-ws/lib/use/ws");
const { ApolloServer } = require("@apollo/server");
const { expressMiddleware } = require("@apollo/server/express4");
const { makeExecutableSchema } = require("@graphql-tools/schema");
const { PubSub } = require("graphql-subscriptions");
const express = require("express");

const pubsub = new PubSub();
const schema = makeExecutableSchema({ typeDefs, resolvers });

const app = express();
const httpServer = createServer(app);

// WebSocket server for subscriptions
const wsServer = new WebSocketServer({
  server: httpServer,
  path: "/graphql",
});

const serverCleanup = useServer(
  {
    schema,
    context: async (ctx) => {
      // Authenticate WebSocket connections
      const token = ctx.connectionParams?.authToken;
      const user = token ? await verifyToken(token) : null;
      return { user, pubsub };
    },
    onConnect: async (ctx) => {
      console.log("Client connected for subscriptions");
    },
    onDisconnect: () => {
      console.log("Client disconnected");
    },
  },
  wsServer
);

const server = new ApolloServer({
  schema,
  plugins: [
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          },
        };
      },
    },
  ],
});

await server.start();
app.use("/graphql", expressMiddleware(server));
httpServer.listen(4000);
```

### Step 5: Secure the API

**Authentication and Authorization**:

```javascript
// Auth directive implementation
const { mapSchema, getDirective, MapperKind } = require("@graphql-tools/utils");
const { defaultFieldResolver } = require("graphql");

function authDirectiveTransformer(schema) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, "auth")?.[0];
      if (!authDirective) return fieldConfig;

      const { requires: role } = authDirective;
      const originalResolve = fieldConfig.resolve || defaultFieldResolver;

      fieldConfig.resolve = async function (source, args, context, info) {
        if (!context.user) {
          throw new Error("Authentication required");
        }
        if (role && !context.user.roles.includes(role)) {
          throw new Error(`Role '${role}' required`);
        }
        return originalResolve(source, args, context, info);
      };

      return fieldConfig;
    },
  });
}

// Schema directive usage:
// directive @auth(requires: Role = USER) on FIELD_DEFINITION
// type Query {
//   viewer: User @auth
//   adminStats: Stats @auth(requires: ADMIN)
// }
```

**Query Complexity and Depth Limiting**:

```javascript
const { createComplexityLimitRule } = require("graphql-validation-complexity");
const depthLimit = require("graphql-depth-limit");

const server = new ApolloServer({
  schema,
  validationRules: [
    depthLimit(10), // Max query depth of 10
    createComplexityLimitRule(1000, {
      // Max complexity score of 1000
      scalarCost: 1,
      objectCost: 2,
      listFactor: 10,
      formatErrorMessage: (cost) =>
        `Query complexity ${cost} exceeds maximum of 1000`,
    }),
  ],
});
```

**Persisted Queries (Automatic)**:

```javascript
const { ApolloServer } = require("@apollo/server");
const {
  ApolloServerPluginPersistedQueries,
} = require("@apollo/server/plugin/persistedQueries");
const { KeyvAdapter } = require("@apollo/utils.keyvadapter");
const Keyv = require("keyv");

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginPersistedQueries({
      cache: new KeyvAdapter(new Keyv("redis://localhost:6379")),
      ttl: 86400, // 24 hours
    }),
  ],
});
```

### Step 6: Set Up Apollo Federation

**Subgraph Definition (Products Service)**:

```graphql
# products/schema.graphql
extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key", "@shareable"])

type Product @key(fields: "id") {
  id: ID!
  name: String!
  price: Float!
  category: Category!
  inStock: Boolean!
}

type Category @key(fields: "id") {
  id: ID!
  name: String!
  products(first: Int, after: String): ProductConnection!
}

type Query {
  product(id: ID!): Product
  products(filter: ProductFilterInput, first: Int, after: String): ProductConnection!
}
```

**Subgraph Definition (Orders Service)**:

```graphql
# orders/schema.graphql
extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key", "@external"])

type Order @key(fields: "id") {
  id: ID!
  user: User!
  items: [OrderItem!]!
  status: OrderStatus!
  total: Float!
}

# Reference to User type defined in users subgraph
type User @key(fields: "id") {
  id: ID! @external
  orders(first: Int, after: String): OrderConnection!
}

type OrderItem {
  product: Product!
  quantity: Int!
  unitPrice: Float!
}

# Reference to Product type defined in products subgraph
type Product @key(fields: "id") {
  id: ID! @external
}
```

**Apollo Router Configuration**:

```yaml
# router.yaml (Apollo Router - the federation gateway)
supergraph:
  listen: 0.0.0.0:4000

subgraphs:
  products:
    routing_url: http://products-service:4001/graphql
  orders:
    routing_url: http://orders-service:4002/graphql
  users:
    routing_url: http://users-service:4003/graphql

traffic_shaping:
  all:
    timeout: 30s
  subgraphs:
    products:
      timeout: 10s

telemetry:
  instrumentation:
    spans:
      mode: spec_compliant
  exporters:
    tracing:
      otlp:
        endpoint: http://otel-collector:4317
```

## Best Practices

- **Design schemas for clients**, not for the database; think in terms of UI components
- **Use DataLoader for every relationship resolver** to prevent N+1 queries
- **Return mutation payloads** (not bare types) so errors can be communicated in-band
- **Implement cursor-based pagination** (Relay spec) for stable, efficient paging
- **Set query depth and complexity limits** to prevent abuse and denial-of-service
- **Use persisted queries** in production to reduce payload size and prevent arbitrary query injection
- **Create fresh DataLoader instances per request**; their cache is request-scoped
- **Keep resolvers thin**; delegate business logic to service/data layers
- **Use subscriptions only for data the client is actively viewing**; not for background sync
- **Version schemas additively**; deprecate fields with `@deprecated` instead of removing them

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The resolver works, I'll add DataLoader later" | A relationship resolver without DataLoader is an N+1 query that issues one DB call per row; "later" arrives as a production latency spike when the list grows from 10 to 10,000 rows. |
| "We don't need a depth limit, our clients are trusted" | GraphQL exposes a recursive query surface; without a depth and complexity limit a single deeply-nested query (or a malicious one) can fan out into a denial-of-service against the database. |
| "Mutations can just throw, the client will handle it" | Throwing for expected user errors collapses them into transport-level failures; payload types with an errors field let the client distinguish validation failure from a 500, which a thrown exception erases. |
| "Auth at the route is enough for GraphQL" | A single endpoint serves every field; route-level auth cannot protect a sensitive field reachable through an alternate query path, so authorization must be applied at the field/resolver layer. |

## Verification

- [ ] No N+1 queries: every relationship field resolves through DataLoader (verified by query logging)
- [ ] Query depth and complexity limits are configured and reject an over-limit query
- [ ] Mutations return payload types with an `errors` field distinguishing user errors from system errors
- [ ] Authorization is enforced at the field/resolver level for sensitive data, not only at the endpoint
- [ ] Pagination uses the Relay cursor specification and the schema validates against the SDL

## Related Skills

- [[api-documentation]] -- documents the GraphQL schema with descriptions and examples
- [[performance-testing]] -- load-tests GraphQL endpoints to catch N+1 and complexity regressions
- [[async-patterns]] -- the subscription and real-time concurrency patterns GraphQL subscriptions rely on
- [[security-review]] -- assesses GraphQL-specific attack surface (depth abuse, introspection, field-level auth)

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
