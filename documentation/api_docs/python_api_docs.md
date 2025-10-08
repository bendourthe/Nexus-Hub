# Python API Documentation

## Objective
Create complete, accurate API documentation that enables developers to quickly understand and successfully integrate with your API, including authentication flows, request formats, response structures, and error handling.

## Implementation Checklist

### Endpoint Documentation
- [ ] All endpoints documented with methods and paths
- [ ] Request parameters clearly specified (path, query, body)
- [ ] Response schemas documented with examples
- [ ] Status codes and their meanings explained
- [ ] Content types specified

### Authentication
- [ ] Authentication methods documented
- [ ] Token/key acquisition process explained
- [ ] Authentication headers specified
- [ ] Token refresh mechanism documented
- [ ] Permission levels explained

### Request/Response
- [ ] Request body schemas with examples
- [ ] Required vs optional fields marked
- [ ] Data types and formats specified
- [ ] Response body schemas with examples
- [ ] Nested objects properly documented

### Error Handling
- [ ] All error codes documented
- [ ] Error response format specified
- [ ] Error messages and meanings explained
- [ ] Troubleshooting guidance provided
- [ ] Common error scenarios covered

### Examples
- [ ] Working code examples provided
- [ ] Multiple programming languages (if applicable)
- [ ] Complete request/response cycles shown
- [ ] Authentication examples included
- [ ] Edge cases demonstrated

### Best Practices
- [ ] Rate limits documented
- [ ] Pagination explained
- [ ] Filtering and sorting documented
- [ ] Versioning strategy explained
- [ ] Deprecation policy stated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python API Documentation Request

Please create comprehensive API documentation for this Python project following this protocol:

## Phase 1: API Inventory & Analysis

1. **Discover All Endpoints**
   - List all routes/endpoints in the application
   - Identify HTTP methods for each endpoint
   - Group endpoints by resource/functionality
   - Note which endpoints require authentication

2. **Analyze Request/Response Patterns**
   - Document request body schemas
   - Document response body schemas
   - Identify common patterns across endpoints
   - Note error response formats

3. **Authentication & Authorization**
   - Document authentication methods used
   - Identify authorization requirements per endpoint
   - Document token/session management

## Phase 2: OpenAPI/Swagger Specification

Generate OpenAPI 3.0 specification:

```yaml
openapi: 3.0.3
info:
  title: [Project Name] API
  description: |
    [Comprehensive description of what the API does]

    ## Base URLs
    - Production: https://api.example.com/v1
    - Staging: https://staging-api.example.com/v1
    - Development: http://localhost:8000/api/v1

    ## Authentication
    This API uses [Bearer token/API Key/OAuth 2.0] authentication.
    Include your token in the `Authorization` header:
    ```
    Authorization: Bearer YOUR_TOKEN_HERE
    ```

    ## Rate Limiting
    - Free tier: 1000 requests/hour
    - Pro tier: 10000 requests/hour
    - Enterprise: Unlimited

    ## Versioning
    This API uses URL versioning (e.g., `/v1/`, `/v2/`).
    Current version: v1

  version: 1.0.0
  contact:
    name: API Support
    email: api@example.com
    url: https://example.com/support
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server

tags:
  - name: Users
    description: User management operations
  - name: Authentication
    description: Authentication and authorization

security:
  - BearerAuth: []

paths:
  /users:
    get:
      summary: List users
      description: |
        Retrieve a paginated list of users.

        **Permissions Required**: `read:users`

        **Rate Limit**: 100 requests per minute
      tags:
        - Users
      parameters:
        - name: page
          in: query
          description: Page number (1-indexed)
          required: false
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: page_size
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: sort
          in: query
          description: Sort field and direction (e.g., "created_at:desc")
          required: false
          schema:
            type: string
            enum: [created_at:asc, created_at:desc, name:asc, name:desc]
            default: created_at:desc
        - name: filter[email]
          in: query
          description: Filter by email (partial match)
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  meta:
                    $ref: '#/components/schemas/PaginationMeta'
                  links:
                    $ref: '#/components/schemas/PaginationLinks'
              examples:
                success:
                  summary: Successful user list response
                  value:
                    data:
                      - id: "123e4567-e89b-12d3-a456-426614174000"
                        email: "user@example.com"
                        name: "John Doe"
                        is_active: true
                        created_at: "2024-01-15T10:30:00Z"
                      - id: "123e4567-e89b-12d3-a456-426614174001"
                        email: "jane@example.com"
                        name: "Jane Smith"
                        is_active: true
                        created_at: "2024-01-14T09:20:00Z"
                    meta:
                      page: 1
                      page_size: 20
                      total_items: 42
                      total_pages: 3
                    links:
                      first: "/users?page=1"
                      last: "/users?page=3"
                      next: "/users?page=2"
                      prev: null
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimitExceeded'
        '500':
          $ref: '#/components/responses/InternalServerError'

    post:
      summary: Create user
      description: |
        Create a new user account.

        **Permissions Required**: `write:users`

        **Rate Limit**: 10 requests per minute
      tags:
        - Users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
            examples:
              basic:
                summary: Basic user creation
                value:
                  email: "newuser@example.com"
                  name: "New User"
                  password: "securePassword123!"
              with_metadata:
                summary: User with optional metadata
                value:
                  email: "newuser@example.com"
                  name: "New User"
                  password: "securePassword123!"
                  metadata:
                    department: "Engineering"
                    role: "Developer"
      responses:
        '201':
          description: User created successfully
          headers:
            Location:
              description: URL of the created user
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
              example:
                id: "123e4567-e89b-12d3-a456-426614174002"
                email: "newuser@example.com"
                name: "New User"
                is_active: true
                created_at: "2024-01-16T14:30:00Z"
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: User already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                error:
                  code: "USER_EXISTS"
                  message: "A user with this email already exists"
                  details:
                    email: "newuser@example.com"

  /users/{user_id}:
    get:
      summary: Get user by ID
      description: Retrieve detailed information about a specific user
      tags:
        - Users
      parameters:
        - name: user_id
          in: path
          description: User ID (UUID)
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      summary: Update user
      description: Update specific fields of a user
      tags:
        - Users
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserUpdate'
      responses:
        '200':
          description: User updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      summary: Delete user
      description: |
        Delete a user account. This action is irreversible.

        **Permissions Required**: `delete:users`
      tags:
        - Users
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: User deleted successfully
        '404':
          $ref: '#/components/responses/NotFound'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from the `/auth/token` endpoint.
        Include in the `Authorization` header as: `Bearer YOUR_TOKEN`

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
          description: Unique user identifier
          example: "123e4567-e89b-12d3-a456-426614174000"
        email:
          type: string
          format: email
          description: User's email address
          example: "user@example.com"
        name:
          type: string
          description: User's full name
          minLength: 1
          maxLength: 100
          example: "John Doe"
        is_active:
          type: boolean
          description: Whether the user account is active
          example: true
        created_at:
          type: string
          format: date-time
          description: Account creation timestamp (ISO 8601)
          example: "2024-01-15T10:30:00Z"
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp (ISO 8601)
          example: "2024-01-15T10:30:00Z"
      required:
        - id
        - email
        - name
        - is_active
        - created_at

    UserCreate:
      type: object
      properties:
        email:
          type: string
          format: email
          description: User's email address (must be unique)
          example: "newuser@example.com"
        name:
          type: string
          description: User's full name
          minLength: 1
          maxLength: 100
          example: "New User"
        password:
          type: string
          format: password
          description: User's password (min 8 chars, must include uppercase, lowercase, number)
          minLength: 8
          example: "SecurePass123!"
        metadata:
          type: object
          description: Optional metadata about the user
          additionalProperties: true
      required:
        - email
        - name
        - password

    UserUpdate:
      type: object
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        is_active:
          type: boolean
      description: All fields are optional. Only provided fields will be updated.

    PaginationMeta:
      type: object
      properties:
        page:
          type: integer
          description: Current page number
          example: 1
        page_size:
          type: integer
          description: Number of items per page
          example: 20
        total_items:
          type: integer
          description: Total number of items
          example: 42
        total_pages:
          type: integer
          description: Total number of pages
          example: 3
      required:
        - page
        - page_size
        - total_items
        - total_pages

    PaginationLinks:
      type: object
      properties:
        first:
          type: string
          format: uri
          description: Link to first page
          example: "/users?page=1"
        last:
          type: string
          format: uri
          description: Link to last page
          example: "/users?page=3"
        next:
          type: string
          format: uri
          nullable: true
          description: Link to next page (null if on last page)
          example: "/users?page=2"
        prev:
          type: string
          format: uri
          nullable: true
          description: Link to previous page (null if on first page)
          example: null
      required:
        - first
        - last
        - next
        - prev

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              description: Machine-readable error code
              example: "VALIDATION_ERROR"
            message:
              type: string
              description: Human-readable error message
              example: "Invalid request data"
            details:
              type: object
              description: Additional error details
              additionalProperties: true
              example:
                email: ["Must be a valid email address"]
          required:
            - code
            - message

  responses:
    BadRequest:
      description: Bad request - invalid input
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "VALIDATION_ERROR"
              message: "Invalid request data"
              details:
                email: ["Must be a valid email address"]
                name: ["Required field"]

    Unauthorized:
      description: Unauthorized - missing or invalid authentication
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "UNAUTHORIZED"
              message: "Authentication required"

    Forbidden:
      description: Forbidden - insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "FORBIDDEN"
              message: "You don't have permission to perform this action"

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "NOT_FOUND"
              message: "The requested resource was not found"

    RateLimitExceeded:
      description: Rate limit exceeded
      headers:
        X-RateLimit-Limit:
          description: Request limit per time window
          schema:
            type: integer
            example: 1000
        X-RateLimit-Remaining:
          description: Remaining requests in current window
          schema:
            type: integer
            example: 0
        X-RateLimit-Reset:
          description: Time when rate limit resets (Unix timestamp)
          schema:
            type: integer
            example: 1705410000
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "RATE_LIMIT_EXCEEDED"
              message: "Too many requests. Please try again later."
              details:
                retry_after: 3600

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: "INTERNAL_ERROR"
              message: "An unexpected error occurred. Please try again later."
```

## Phase 3: Authentication Documentation

Document authentication in detail:

```markdown
# Authentication

## Overview

This API uses JWT (JSON Web Token) bearer authentication. Include your token in the `Authorization` header for all protected endpoints.

## Obtaining a Token

### Request
```http
POST /auth/token HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Using the Token

Include the token in the `Authorization` header:

```http
GET /users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Python Example
```python
import requests

# Obtain token
auth_response = requests.post(
    "https://api.example.com/auth/token",
    json={"email": "user@example.com", "password": "your_password"}
)
token = auth_response.json()["access_token"]

# Use token in requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://api.example.com/users/me", headers=headers)
```

## Token Refresh

Tokens expire after 1 hour. Use the refresh token to obtain a new access token:

```http
POST /auth/refresh HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Token Revocation

Revoke a token (logout):

```http
POST /auth/revoke HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Permissions

Each endpoint requires specific permissions. User roles determine available permissions:

| Role | Permissions |
|------|-------------|
| Admin | `read:*`, `write:*`, `delete:*` (all permissions) |
| User | `read:users`, `write:own_profile`, `read:public_data` |
| Guest | `read:public_data` |
```

## Phase 4: Code Examples

Provide working code examples:

```markdown
# Code Examples

## Python (requests)

```python
import requests
from typing import Dict, List, Optional

class APIClient:
    """Client for the Example API."""

    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url
        self.token = None
        self._authenticate(email, password)

    def _authenticate(self, email: str, password: str):
        """Obtain authentication token."""
        response = requests.post(
            f"{self.base_url}/auth/token",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def _headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        sort: Optional[str] = None,
        email_filter: Optional[str] = None
    ) -> Dict:
        """List users with pagination and filtering."""
        params = {
            "page": page,
            "page_size": page_size
        }
        if sort:
            params["sort"] = sort
        if email_filter:
            params["filter[email]"] = email_filter

        response = requests.get(
            f"{self.base_url}/users",
            headers=self._headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()

    def create_user(self, email: str, name: str, password: str) -> Dict:
        """Create a new user."""
        response = requests.post(
            f"{self.base_url}/users",
            headers=self._headers(),
            json={
                "email": email,
                "name": name,
                "password": password
            }
        )
        response.raise_for_status()
        return response.json()

    def get_user(self, user_id: str) -> Dict:
        """Get user by ID."""
        response = requests.get(
            f"{self.base_url}/users/{user_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient(
    base_url="https://api.example.com/v1",
    email="admin@example.com",
    password="admin_password"
)

# List users
users = client.list_users(page=1, page_size=10)
for user in users["data"]:
    print(f"{user['name']} <{user['email']}>")

# Create user
new_user = client.create_user(
    email="newuser@example.com",
    name="New User",
    password="SecurePass123!"
)
print(f"Created user: {new_user['id']}")
```

## Python (httpx async)

```python
import httpx
import asyncio
from typing import Dict, List, Optional

class AsyncAPIClient:
    """Async client for the Example API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self, email: str, password: str):
        """Obtain authentication token."""
        response = await self.client.post(
            f"{self.base_url}/auth/token",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def _headers(self) -> Dict[str, str]:
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    async def list_users(self, page: int = 1) -> Dict:
        """List users."""
        response = await self.client.get(
            f"{self.base_url}/users",
            headers=self._headers(),
            params={"page": page}
        )
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Close the client."""
        await self.client.aclose()

# Usage
async def main():
    client = AsyncAPIClient("https://api.example.com/v1")
    try:
        await client.authenticate("admin@example.com", "password")
        users = await client.list_users()
        print(f"Found {len(users['data'])} users")
    finally:
        await client.close()

asyncio.run(main())
```

## cURL Examples

```bash
# Obtain token
curl -X POST https://api.example.com/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"your_password"}'

# Save token
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# List users
curl -X GET "https://api.example.com/v1/users?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"

# Create user
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "name": "New User",
    "password": "SecurePass123!"
  }'

# Get specific user
curl -X GET https://api.example.com/v1/users/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer $TOKEN"

# Update user
curl -X PATCH https://api.example.com/v1/users/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'

# Delete user
curl -X DELETE https://api.example.com/v1/users/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer $TOKEN"
```
```

## Phase 5: Error Handling & Best Practices

```markdown
# Error Handling

## Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": ["Specific error about field"]
    }
  }
}
```

## HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful GET, PATCH request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

## Common Error Codes

### Authentication Errors
- `UNAUTHORIZED`: Missing or invalid token
- `TOKEN_EXPIRED`: Token has expired, refresh needed
- `INVALID_CREDENTIALS`: Wrong email/password

### Validation Errors
- `VALIDATION_ERROR`: Request data failed validation
- `REQUIRED_FIELD`: Required field missing
- `INVALID_FORMAT`: Field has invalid format

### Resource Errors
- `NOT_FOUND`: Requested resource doesn't exist
- `ALREADY_EXISTS`: Resource with identifier already exists
- `CONFLICT`: Operation conflicts with current state

### Rate Limiting
- `RATE_LIMIT_EXCEEDED`: Too many requests

## Handling Errors in Code

```python
import requests
from requests.exceptions import HTTPError

def safe_api_call():
    """Example of proper error handling."""
    try:
        response = requests.get(
            "https://api.example.com/v1/users/invalid-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()

    except HTTPError as e:
        status_code = e.response.status_code
        error_data = e.response.json()
        error_code = error_data.get("error", {}).get("code")

        if status_code == 401:
            print("Authentication failed - refresh token")
        elif status_code == 404:
            print("Resource not found")
        elif status_code == 429:
            retry_after = error_data.get("error", {}).get("details", {}).get("retry_after")
            print(f"Rate limited - retry after {retry_after} seconds")
        else:
            print(f"Error {error_code}: {error_data}")

        raise
```

# Best Practices

## Rate Limiting

- **Free tier**: 1000 requests/hour
- **Pro tier**: 10000 requests/hour
- **Enterprise**: Custom limits

Check rate limit headers in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1705410000
```

### Handling Rate Limits

```python
import time

def make_request_with_retry(url, headers):
    """Make request with automatic retry on rate limit."""
    while True:
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            retry_after = int(response.headers.get("X-RateLimit-Reset", 0))
            current_time = int(time.time())
            wait_time = max(retry_after - current_time, 60)
            print(f"Rate limited - waiting {wait_time} seconds")
            time.sleep(wait_time)
            continue

        response.raise_for_status()
        return response.json()
```

## Pagination

Always use pagination for list endpoints:

```python
def get_all_users(client):
    """Fetch all users using pagination."""
    all_users = []
    page = 1

    while True:
        response = client.list_users(page=page, page_size=100)
        all_users.extend(response["data"])

        # Check if there are more pages
        if not response["links"]["next"]:
            break

        page += 1

    return all_users
```

## Filtering and Sorting

Use query parameters for filtering:

```python
# Filter by email
users = client.list_users(email_filter="@example.com")

# Sort by creation date
users = client.list_users(sort="created_at:desc")

# Combine filters
users = client.list_users(
    email_filter="@example.com",
    sort="created_at:desc",
    page_size=50
)
```

## Idempotency

Use idempotency keys for safe retries:

```python
import uuid

idempotency_key = str(uuid.uuid4())

response = requests.post(
    "https://api.example.com/v1/users",
    headers={
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key
    },
    json=user_data
)
```
```

---

## Output Format

Please provide API documentation in these formats:

### 1. OpenAPI/Swagger Specification
- Complete openapi.yaml file
- All endpoints, schemas, and examples
- Can be imported into Swagger UI, Postman, etc.

### 2. Human-Readable Documentation
- Markdown files organized by resource
- Clear examples and explanations
- Suitable for publishing to docs site

### 3. Code Examples
- Working examples in Python (and other languages if applicable)
- Complete client implementations
- Error handling demonstrations

### Summary Report

```markdown
## API Documentation Summary

**API Version**: [version]
**Total Endpoints**: [count]
**Authentication Method**: [Bearer/OAuth/API Key]

**Endpoints Documented**:
- GET endpoints: [count]
- POST endpoints: [count]
- PATCH/PUT endpoints: [count]
- DELETE endpoints: [count]

**Schemas Documented**: [count]
**Error Codes Documented**: [count]
**Code Examples**: [count]

**Documentation Formats**:
- [ ] OpenAPI 3.0 specification
- [ ] Markdown documentation
- [ ] Python code examples
- [ ] cURL examples
- [ ] Interactive API explorer (Swagger UI)

**Quality Checks**:
- [ ] All endpoints documented
- [ ] Request/response schemas complete
- [ ] Authentication fully explained
- [ ] Error handling comprehensive
- [ ] Code examples tested and working
- [ ] Rate limits documented
- [ ] Best practices included
```

---

## Tools for API Documentation

### Generate from Code (FastAPI Example)

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API description",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Access at /docs (Swagger UI) or /redoc (ReDoc)
```

### Documentation Hosting Options

- **Swagger UI**: Interactive API explorer
- **ReDoc**: Beautiful API documentation
- **ReadTheDocs**: Comprehensive documentation hosting
- **GitHub Pages**: Free hosting for static docs
- **MkDocs**: Static site generator for docs

---
~~~

## Output Format Specifications

The API documentation should:
- Follow OpenAPI 3.0 specification standards
- Include complete request/response examples
- Provide working code examples in multiple languages
- Document all error scenarios comprehensively
- Explain authentication and authorization clearly
- Include rate limiting and best practices
- Be interactive (Swagger UI) or easily testable
- Keep examples up-to-date with API changes
