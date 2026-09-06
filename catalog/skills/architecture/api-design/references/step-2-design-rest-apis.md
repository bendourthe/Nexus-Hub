### Step 2: Design REST APIs

**Resource Naming Conventions**:

```
# Use nouns (not verbs) for resources
GET    /users                  # List users
POST   /users                  # Create user
GET    /users/{id}             # Get single user
PUT    /users/{id}             # Replace user
PATCH  /users/{id}             # Partial update
DELETE /users/{id}             # Delete user

# Use plural nouns
GET    /orders                 # Not /order
GET    /order-items            # Hyphenated, not camelCase or snake_case

# Nest for clear ownership (max 2 levels deep)
GET    /users/{id}/orders      # Orders belonging to user
POST   /users/{id}/orders      # Create order for user

# Use query parameters for filtering, sorting, searching
GET    /orders?status=pending&sort=-created_at&limit=20
GET    /products?category=electronics&min_price=100&q=laptop
```

**HTTP Methods and Status Codes**:

```
Method    Idempotent  Safe   Common Status Codes
------    ----------  ----   --------------------
GET       Yes         Yes    200 OK, 304 Not Modified
POST      No          No     201 Created, 202 Accepted, 400 Bad Request
PUT       Yes         No     200 OK, 204 No Content, 409 Conflict
PATCH     No          No     200 OK, 422 Unprocessable Entity
DELETE    Yes         No     204 No Content, 404 Not Found

Status Code Ranges:
  2xx  Success (200 OK, 201 Created, 202 Accepted, 204 No Content)
  3xx  Redirection (301 Moved, 304 Not Modified)
  4xx  Client error (400 Bad Request, 401 Unauthorized, 403 Forbidden,
       404 Not Found, 409 Conflict, 422 Unprocessable Entity, 429 Too Many)
  5xx  Server error (500 Internal, 502 Bad Gateway, 503 Unavailable)
```

**OpenAPI 3.1 Example**:

```yaml
openapi: 3.1.0
info:
  title: Order Management API
  version: 1.2.0
  description: API for managing customer orders
  contact:
    name: Platform Team
    email: platform@example.com

servers:
  - url: https://api.example.com/v1
    description: Production
  - url: https://api.staging.example.com/v1
    description: Staging

paths:
  /orders:
    get:
      operationId: listOrders
      summary: List orders with filtering and pagination
      tags: [Orders]
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [draft, placed, confirmed, shipped, delivered, cancelled]
        - name: cursor
          in: query
          description: Pagination cursor from previous response
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          description: Paginated list of orders
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: "#/components/schemas/Order"
                  pagination:
                    $ref: "#/components/schemas/CursorPagination"
          headers:
            X-RateLimit-Remaining:
              schema:
                type: integer

    post:
      operationId: createOrder
      summary: Create a new order
      tags: [Orders]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateOrderRequest"
      responses:
        "201":
          description: Order created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
          headers:
            Location:
              schema:
                type: string
                format: uri
        "422":
          description: Validation error
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/ProblemDetail"

components:
  schemas:
    Order:
      type: object
      required: [id, customerId, status, lines, total, createdAt]
      properties:
        id:
          type: string
          format: uuid
        customerId:
          type: string
          format: uuid
        status:
          type: string
          enum: [draft, placed, confirmed, shipped, delivered, cancelled]
        lines:
          type: array
          items:
            $ref: "#/components/schemas/OrderLine"
        total:
          $ref: "#/components/schemas/Money"
        createdAt:
          type: string
          format: date-time
        _links:
          type: object
          properties:
            self:
              type: object
              properties:
                href:
                  type: string
                  format: uri

    OrderLine:
      type: object
      properties:
        productId:
          type: string
          format: uuid
        productName:
          type: string
        unitPrice:
          $ref: "#/components/schemas/Money"
        quantity:
          type: integer
          minimum: 1

    Money:
      type: object
      properties:
        amount:
          type: integer
          description: Amount in smallest currency unit (cents)
        currency:
          type: string
          pattern: "^[A-Z]{3}$"

    CreateOrderRequest:
      type: object
      required: [customerId, lines]
      properties:
        customerId:
          type: string
          format: uuid
        lines:
          type: array
          minItems: 1
          items:
            type: object
            required: [productId, quantity]
            properties:
              productId:
                type: string
                format: uuid
              quantity:
                type: integer
                minimum: 1

    CursorPagination:
      type: object
      properties:
        nextCursor:
          type: string
          nullable: true
        hasMore:
          type: boolean

    ProblemDetail:
      type: object
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
          format: uri
        errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - bearerAuth: []
```
