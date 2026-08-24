## Common Patterns

### Pattern 1: Relay Cursor Pagination Implementation

```javascript
function buildConnection(rows, hasMore, getCursor) {
  const edges = rows.map((row) => ({
    node: row,
    cursor: getCursor(row),
  }));

  return {
    edges,
    pageInfo: {
      hasNextPage: hasMore,
      hasPreviousPage: false, // Simplified; track if "before" was used
      startCursor: edges[0]?.cursor || null,
      endCursor: edges[edges.length - 1]?.cursor || null,
    },
    totalCount: null, // Compute separately if needed (can be expensive)
  };
}
```

### Pattern 2: Error Union Pattern

```graphql
union CreateOrderResult = Order | ValidationError | InsufficientStockError

type ValidationError {
  field: String!
  message: String!
}

type InsufficientStockError {
  productId: ID!
  requested: Int!
  available: Int!
}

type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderResult!
}
```

### Pattern 3: Viewer Pattern for Auth Context

```graphql
type Query {
  # Viewer is the authenticated user; null if not logged in
  viewer: User
}

type User {
  # Private fields only accessible to the viewer
  email: EmailAddress!
  orders: OrderConnection!
  # Sensitive operations as mutations on the User type
  cart: Cart!
}
```
