# JavaScript API Documentation

## Objective
Create complete, accurate API documentation that enables developers to quickly understand and successfully integrate with your JavaScript API, including authentication flows, request formats, response structures, and error handling for Express/Fastify applications.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/api_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/api_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Endpoint Documentation

- [ ] All endpoints documented with methods and paths

- [ ] Request parameters clearly specified (path, query, body)

- [ ] Response schemas documented with examples

- [ ] Status codes and their meanings explained

- [ ] Content types specified

### Authentication

- [ ] Authentication methods documented (JWT, OAuth, API Key)

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

- [ ] Multiple client libraries (axios, fetch, Node.js)

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

---

## Output Format Specifications

The API documentation should:

- Follow OpenAPI 3.0 specification standards

- Include complete request/response examples

- Provide working code examples for axios and fetch

- Document all error scenarios comprehensively

- Explain JWT authentication and refresh tokens

- Include rate limiting and best practices

- Be compatible with Swagger UI and Postman

- Keep examples up-to-date with API changes

~~~markdown
# JavaScript API Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/api_docs"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please create comprehensive API documentation for this JavaScript project following this protocol:

## Phase 1: API Inventory & Analysis

1. **Discover All Endpoints**
   - List all routes/endpoints in the Express/Fastify application
   - Identify HTTP methods for each endpoint
   - Group endpoints by resource/functionality
   - Note which endpoints require authentication

2. **Analyze Request/Response Patterns**
   - Document request body schemas
   - Document response body schemas
   - Identify common patterns across endpoints
   - Note error response formats

3. **Authentication & Authorization**
   - Document authentication methods used (JWT, OAuth2, API Key)
   - Identify authorization requirements per endpoint
   - Document token/session management

## Phase 2: OpenAPI/Swagger Specification

Generate OpenAPI 3.0 specification:

```yaml
openapi: 3.0.3
info:
  title: JavaScript API
  description: |
    RESTful API built with Express/Fastify for managing application resources.

    ## Base URLs
    - Production: https://api.example.com/v1
    - Staging: https://staging-api.example.com/v1
    - Development: http://localhost:3000/api/v1

    ## Authentication
    This API uses JWT Bearer token authentication.
    Include your token in the `Authorization` header:
    ```
    Authorization: Bearer YOUR_JWT_TOKEN
    ```

    ## Rate Limiting
    - Free tier: 1000 requests/hour
    - Pro tier: 10000 requests/hour
    - Enterprise: Custom limits

    Rate limit headers are included in all responses:
    - `X-RateLimit-Limit`: Request limit per window
    - `X-RateLimit-Remaining`: Remaining requests
    - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

    ## Versioning
    This API uses URL versioning (e.g., `/v1/`, `/v2/`).
    Current version: v1

  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
    url: https://example.com/support
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging-api.example.com/v1
    description: Staging server
  - url: http://localhost:3000/api/v1
    description: Development server

tags:
  - name: Authentication
    description: User authentication and token management
  - name: Users
    description: User account operations
  - name: Products
    description: Product catalog management

security:
  - BearerAuth: []

paths:
  /auth/register:
    post:
      summary: Register new user
      description: |
        Create a new user account with email and password.

        **No authentication required**

        **Rate Limit**: 10 requests per hour per IP
      tags:
        - Authentication
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
                - name
              properties:
                email:
                  type: string
                  format: email
                  description: User's email address (must be unique)
                  example: "user@example.com"
                password:
                  type: string
                  format: password
                  minLength: 8
                  description: Password (min 8 chars, must include uppercase, lowercase, number)
                  example: "SecurePass123!"
                name:
                  type: string
                  minLength: 2
                  maxLength: 100
                  description: User's full name
                  example: "John Doe"
      responses:
        '201':
          description: User registered successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: object
                    properties:
                      user:
                        $ref: '#/components/schemas/User'
                      token:
                        type: string
                        description: JWT access token
                        example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        '400':
          $ref: '#/components/responses/BadRequest'
        '409':
          description: Email already exists
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                success: false
                error:
                  code: "EMAIL_EXISTS"
                  message: "An account with this email already exists"

  /auth/login:
    post:
      summary: Login user
      description: |
        Authenticate with email and password to receive JWT token.

        **No authentication required**

        **Rate Limit**: 5 requests per minute per IP
      tags:
        - Authentication
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
                - password
              properties:
                email:
                  type: string
                  format: email
                  example: "user@example.com"
                password:
                  type: string
                  format: password
                  example: "SecurePass123!"
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    example: true
                  data:
                    type: object
                    properties:
                      token:
                        type: string
                        description: JWT access token
                        example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                      refreshToken:
                        type: string
                        description: Refresh token for obtaining new access token
                        example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                      expiresIn:
                        type: integer
                        description: Token expiration time in seconds
                        example: 3600
                      user:
                        $ref: '#/components/schemas/User'
        '401':
          description: Invalid credentials
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                success: false
                error:
                  code: "INVALID_CREDENTIALS"
                  message: "Invalid email or password"

  /auth/refresh:
    post:
      summary: Refresh access token
      description: |
        Obtain a new access token using a refresh token.

        **No authentication required** (uses refresh token)
      tags:
        - Authentication
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - refreshToken
              properties:
                refreshToken:
                  type: string
                  description: Valid refresh token
      responses:
        '200':
          description: Token refreshed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: object
                    properties:
                      token:
                        type: string
                      expiresIn:
                        type: integer
        '401':
          $ref: '#/components/responses/Unauthorized'

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
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          description: Number of items per page
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: sort
          in: query
          description: Sort field and direction (e.g., "createdAt:desc")
          schema:
            type: string
            enum: [createdAt:asc, createdAt:desc, name:asc, name:desc]
            default: createdAt:desc
        - name: search
          in: query
          description: Search in name and email fields
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
                  success:
                    type: boolean
                    example: true
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
              example:
                success: true
                data:
                  - id: "507f1f77bcf86cd799439011"
                    email: "user@example.com"
                    name: "John Doe"
                    role: "user"
                    isActive: true
                    createdAt: "2024-01-15T10:30:00.000Z"
                    updatedAt: "2024-01-15T10:30:00.000Z"
                pagination:
                  page: 1
                  limit: 20
                  totalItems: 42
                  totalPages: 3
                  hasNext: true
                  hasPrev: false
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimitExceeded'

    post:
      summary: Create user
      description: |
        Create a new user account (admin only).

        **Permissions Required**: `write:users`, `admin`

        **Rate Limit**: 10 requests per minute
      tags:
        - Users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
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
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '403':
          $ref: '#/components/responses/Forbidden'

  /users/{userId}:
    get:
      summary: Get user by ID
      description: Retrieve detailed information about a specific user
      tags:
        - Users
      parameters:
        - name: userId
          in: path
          required: true
          description: User ID (MongoDB ObjectId)
          schema:
            type: string
            pattern: '^[0-9a-fA-F]{24}$'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/User'
        '404':
          $ref: '#/components/responses/NotFound'

    patch:
      summary: Update user
      description: Update specific fields of a user
      tags:
        - Users
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
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
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      summary: Delete user
      description: |
        Permanently delete a user account.

        **Permissions Required**: `delete:users`, `admin`

        **Warning**: This action is irreversible.
      tags:
        - Users
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '204':
          description: User deleted successfully
        '404':
          $ref: '#/components/responses/NotFound'
        '403':
          $ref: '#/components/responses/Forbidden'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from `/auth/login` or `/auth/register`.
        Include in the `Authorization` header as: `Bearer YOUR_TOKEN`

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          description: Unique user identifier (MongoDB ObjectId)
          example: "507f1f77bcf86cd799439011"
        email:
          type: string
          format: email
          description: User's email address
          example: "user@example.com"
        name:
          type: string
          description: User's full name
          example: "John Doe"
        role:
          type: string
          enum: [user, admin, moderator]
          description: User's role
          example: "user"
        isActive:
          type: boolean
          description: Whether the account is active
          example: true
        createdAt:
          type: string
          format: date-time
          description: Account creation timestamp (ISO 8601)
          example: "2024-01-15T10:30:00.000Z"
        updatedAt:
          type: string
          format: date-time
          description: Last update timestamp (ISO 8601)
          example: "2024-01-15T10:30:00.000Z"
      required:
        - id
        - email
        - name
        - role
        - isActive
        - createdAt
        - updatedAt

    UserCreate:
      type: object
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 2
          maxLength: 100
        password:
          type: string
          format: password
          minLength: 8
        role:
          type: string
          enum: [user, admin, moderator]
          default: user
      required:
        - email
        - name
        - password

    UserUpdate:
      type: object
      properties:
        name:
          type: string
          minLength: 2
          maxLength: 100
        isActive:
          type: boolean
        role:
          type: string
          enum: [user, admin, moderator]
      description: All fields are optional. Only provided fields will be updated.

    Pagination:
      type: object
      properties:
        page:
          type: integer
          description: Current page number
          example: 1
        limit:
          type: integer
          description: Items per page
          example: 20
        totalItems:
          type: integer
          description: Total number of items
          example: 42
        totalPages:
          type: integer
          description: Total number of pages
          example: 3
        hasNext:
          type: boolean
          description: Whether there is a next page
          example: true
        hasPrev:
          type: boolean
          description: Whether there is a previous page
          example: false

    Error:
      type: object
      properties:
        success:
          type: boolean
          example: false
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
            success: false
            error:
              code: "VALIDATION_ERROR"
              message: "Validation failed"
              details:
                email: "Must be a valid email address"
                password: "Must be at least 8 characters"

    Unauthorized:
      description: Unauthorized - missing or invalid authentication
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            success: false
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
            success: false
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
            success: false
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
        X-RateLimit-Remaining:
          description: Remaining requests in current window
          schema:
            type: integer
        X-RateLimit-Reset:
          description: Time when rate limit resets (Unix timestamp)
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            success: false
            error:
              code: "RATE_LIMIT_EXCEEDED"
              message: "Too many requests. Please try again later."
              details:
                retryAfter: 3600
```

## Phase 3: Authentication Documentation

Document authentication in detail:

```markdown
# Authentication

## Overview

This API uses JWT (JSON Web Token) bearer authentication. Tokens are obtained through the `/auth/login` or `/auth/register` endpoints and must be included in the `Authorization` header for protected routes.

## Obtaining a Token

### Registration (New Users)

**Request:**
```http
POST /auth/register HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123!",
  "name": "New User"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "507f1f77bcf86cd799439011",
      "email": "newuser@example.com",
      "name": "New User",
      "role": "user",
      "isActive": true,
      "createdAt": "2024-01-16T14:30:00.000Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Login (Existing Users)

**Request:**
```http
POST /auth/login HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600,
    "user": {
      "id": "507f1f77bcf86cd799439011",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user"
    }
  }
}
```

## Using the Token

Include the token in the `Authorization` header with the `Bearer` scheme:

```http
GET /users/me HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Token Refresh

Access tokens expire after 1 hour. Use the refresh token to obtain a new access token without re-authenticating:

**Request:**
```http
POST /auth/refresh HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 3600
  }
}
```

## Token Revocation (Logout)

Revoke a token to invalidate it:

```http
POST /auth/logout HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Roles and Permissions

| Role | Permissions |
|------|-------------|
| **admin** | Full access to all resources |
| **moderator** | Read all, write own, moderate content |
| **user** | Read all, write/delete own resources only |
```

## Phase 4: Code Examples

Provide working code examples in JavaScript:

```javascript
const axios = require('axios');

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = null;
    this.client = axios.create({
      baseURL: baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add request interceptor to include token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response?.status === 401) {
          console.error('Authentication failed');
        }
        return Promise.reject(error);
      }
    );
  }

  async login(email, password) {
    const response = await this.client.post('/auth/login', {
      email,
      password
    });
    this.token = response.data.token;
    return response.data;
  }

  async register(email, password, name) {
    const response = await this.client.post('/auth/register', {
      email,
      password,
      name
    });
    this.token = response.data.token;
    return response.data;
  }

  async listUsers(options = {}) {
    const { page = 1, limit = 20, sort, search } = options;
    const params = { page, limit };
    if (sort) params.sort = sort;
    if (search) params.search = search;

    return await this.client.get('/users', { params });
  }

  async getUser(userId) {
    return await this.client.get(`/users/${userId}`);
  }

  async createUser(userData) {
    return await this.client.post('/users', userData);
  }

  async updateUser(userId, updates) {
    return await this.client.patch(`/users/${userId}`, updates);
  }

  async deleteUser(userId) {
    return await this.client.delete(`/users/${userId}`);
  }
}

// Usage
(async () => {
  const api = new APIClient('https://api.example.com/v1');

  try {
    // Login
    const loginResult = await api.login('user@example.com', 'SecurePass123!');
    console.log('Logged in:', loginResult.user.name);

    // List users
    const users = await api.listUsers({ page: 1, limit: 10 });
    console.log(`Found ${users.pagination.totalItems} users`);

    // Get specific user
    const user = await api.getUser(users.data[0].id);
    console.log('User details:', user.data);

    // Update user
    const updated = await api.updateUser(user.data.id, { name: 'Updated Name' });
    console.log('Updated user:', updated.data);
  } catch (error) {
    console.error('API Error:', error.response?.data || error.message);
  }
})();
```

## Phase 5: Error Handling & Best Practices

```markdown
# Error Handling

## Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Specific error information"
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

- `EMAIL_EXISTS`: Email already in use

### Resource Errors

- `NOT_FOUND`: Requested resource doesn't exist

- `ALREADY_EXISTS`: Resource with identifier already exists

- `CONFLICT`: Operation conflicts with current state

### Rate Limiting

- `RATE_LIMIT_EXCEEDED`: Too many requests

## Handling Errors in JavaScript

```javascript
async function makeAPICall() {
  try {
    const response = await api.getUser('invalid-id');
    return response.data;
  } catch (error) {
    if (error.response) {
      const { status, data } = error.response;
      const errorCode = data.error?.code;

      switch (status) {
        case 401:
          console.log('Authentication required - redirecting to login');
          // Refresh token or redirect to login
          break;
        case 404:
          console.log('User not found');
          break;
        case 429:
          const retryAfter = data.error?.details?.retryAfter;
          console.log(`Rate limited - retry after ${retryAfter} seconds`);
          break;
        default:
          console.error(`Error ${errorCode}:`, data.error?.message);
      }
    } else {
      console.error('Network error:', error.message);
    }
    throw error;
  }
}
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

```javascript
async function makeRequestWithRetry(requestFn) {
  while (true) {
    try {
      return await requestFn();
    } catch (error) {
      if (error.response?.status === 429) {
        const resetTime = parseInt(error.response.headers['x-ratelimit-reset']);
        const waitTime = Math.max((resetTime - Date.now() / 1000), 60) * 1000;

        console.log(`Rate limited - waiting ${waitTime / 1000} seconds`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
      throw error;
    }
  }
}
```

## Pagination

Always use pagination for list endpoints:

```javascript
async function getAllUsers(api) {
  const allUsers = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const response = await api.listUsers({ page, limit: 100 });
    allUsers.push(...response.data);

    hasMore = response.pagination.hasNext;
    page++;
  }

  return allUsers;
}
```

## Request Retry Logic

```javascript
async function retryRequest(requestFn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      if (attempt === maxRetries) throw error;

      // Only retry on network errors or 5xx server errors
      const shouldRetry = !error.response ||
                         error.response.status >= 500;

      if (!shouldRetry) throw error;

      const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
      console.log(`Retry ${attempt}/${maxRetries} after ${delay}ms`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Environment Configuration

```javascript
// config.js
module.exports = {
  development: {
    apiBaseURL: 'http://localhost:3000/api/v1',
    timeout: 10000
  },
  staging: {
    apiBaseURL: 'https://staging-api.example.com/v1',
    timeout: 10000
  },
  production: {
    apiBaseURL: 'https://api.example.com/v1',
    timeout: 5000
  }
};

// Usage
const config = require('./config')[process.env.NODE_ENV || 'development'];
const api = new APIClient(config.apiBaseURL);
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

- Working examples in JavaScript (Node.js, browser)

- Complete client implementations

- Error handling demonstrations

### Summary Report

```markdown
## API Documentation Summary

**API Version**: [version]
**Total Endpoints**: [count]
**Authentication Method**: JWT Bearer Token

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

- [ ] JavaScript code examples (axios, fetch)

- [ ] Node.js examples

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

~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
