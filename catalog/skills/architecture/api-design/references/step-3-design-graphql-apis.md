### Step 3: Design GraphQL APIs

**Schema Design Example**:

```graphql
# schema.graphql

type Query {
  """Fetch a single order by ID."""
  order(id: ID!): Order

  """List orders with filtering and pagination."""
  orders(
    filter: OrderFilter
    first: Int = 20
    after: String
  ): OrderConnection!

  """Search products by text query."""
  searchProducts(query: String!, first: Int = 10): ProductConnection!
}

type Mutation {
  """Create a new order from cart items."""
  createOrder(input: CreateOrderInput!): CreateOrderPayload!

  """Cancel an existing order with a reason."""
  cancelOrder(input: CancelOrderInput!): CancelOrderPayload!

  """Add a line item to a draft order."""
  addOrderLine(input: AddOrderLineInput!): AddOrderLinePayload!
}

type Subscription {
  """Stream order status updates in real time."""
  orderStatusChanged(orderId: ID!): OrderStatusEvent!
}

# --- Types ---

type Order implements Node {
  id: ID!
  customer: Customer!
  status: OrderStatus!
  lines: [OrderLine!]!
  total: Money!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type OrderLine {
  product: Product!
  unitPrice: Money!
  quantity: Int!
  lineTotal: Money!
}

type Money {
  amount: Int!
  currency: Currency!
  formatted: String!
}

enum OrderStatus {
  DRAFT
  PLACED
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

enum Currency {
  USD
  EUR
  GBP
}

# --- Connections (Relay-style pagination) ---

type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# --- Inputs ---

input CreateOrderInput {
  customerId: ID!
  lines: [OrderLineInput!]!
}

input OrderLineInput {
  productId: ID!
  quantity: Int!
}

input CancelOrderInput {
  orderId: ID!
  reason: String!
}

input AddOrderLineInput {
  orderId: ID!
  productId: ID!
  quantity: Int!
}

input OrderFilter {
  status: OrderStatus
  customerId: ID
  createdAfter: DateTime
  createdBefore: DateTime
}

# --- Payloads (union for errors) ---

type CreateOrderPayload {
  order: Order
  errors: [UserError!]!
}

type CancelOrderPayload {
  order: Order
  errors: [UserError!]!
}

type AddOrderLinePayload {
  order: Order
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: ErrorCode!
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  CONFLICT
  UNAUTHORIZED
}

# --- Events ---

type OrderStatusEvent {
  orderId: ID!
  previousStatus: OrderStatus!
  newStatus: OrderStatus!
  occurredAt: DateTime!
}

interface Node {
  id: ID!
}

scalar DateTime
```

**Preventing N+1 Queries with DataLoader**:

```python
# graphql/dataloaders.py
from aiodataloader import DataLoader

class ProductLoader(DataLoader):
    """Batches individual product lookups into a single query."""

    def __init__(self, product_repo):
        super().__init__()
        self._repo = product_repo

    async def batch_load_fn(self, product_ids: list[str]):
        products = await self._repo.find_by_ids(product_ids)
        product_map = {p.id: p for p in products}
        return [product_map.get(pid) for pid in product_ids]

# graphql/resolvers.py
async def resolve_order_line_product(line, info):
    return await info.context["product_loader"].load(line.product_id)
```
