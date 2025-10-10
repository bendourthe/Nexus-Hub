# JavaScript Technical Documentation

## Objective
Create comprehensive technical documentation that captures architecture decisions, system design, data flows, integration points, and development workflows for developers and technical stakeholders.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/technical_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/technical_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Architecture Documentation

- [ ] System architecture overview with diagrams

- [ ] Component responsibilities clearly defined

- [ ] Technology stack documented with rationale

- [ ] Architectural patterns explained

- [ ] Scalability and performance considerations

- [ ] Security architecture documented

### Design Decisions

- [ ] Key technical decisions documented with rationale

- [ ] Alternative approaches considered

- [ ] Trade-offs and constraints explained

- [ ] Decision timeline and context

- [ ] Impact assessment of decisions

### Module Organization

- [ ] Directory structure explained

- [ ] Module dependencies mapped

- [ ] Public vs private interfaces defined

- [ ] Import/export structure documented

- [ ] Code organization principles

### Data Flow

- [ ] Data flow diagrams created

- [ ] State management documented

- [ ] Event flows explained

- [ ] Data transformation pipelines

- [ ] Error propagation paths

### Integration Points

- [ ] External API integrations documented

- [ ] Database schemas and migrations

- [ ] Message queue/event systems

- [ ] Third-party service dependencies

- [ ] Authentication/authorization flows

### Development Workflow

- [ ] Development environment setup

- [ ] Build and deployment process

- [ ] Testing strategy

- [ ] CI/CD pipeline documentation

- [ ] Release process

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# JavaScript Technical Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/technical_docs"
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

Please create comprehensive technical documentation for this JavaScript/Node.js project following this protocol:

## Phase 1: Architecture Analysis

1. **System Architecture Overview**

   Document the high-level architecture:

   ```markdown
   # System Architecture

   ## Overview

   [Project Name] is built as a [monolith/microservice/library/framework] that [high-level purpose].

   ## Architecture Style

   - **Pattern**: [MVC/Layered/Event-Driven/Microservices/etc.]
   - **Runtime**: [Node.js/Browser/Universal/Edge]
   - **Deployment**: [Single instance/distributed/serverless/containerized]
   - **State Management**: [Redux/MobX/Context/Stateless/etc.]
   - **Communication**: [REST/GraphQL/WebSocket/gRPC]

   ## Key Architectural Decisions

   ### Decision 1: [Technology/Pattern Choice]
   - **Context**: [What problem needed solving]
   - **Decision**: [What was chosen]
   - **Rationale**: [Why this approach]
   - **Consequences**: [Benefits and trade-offs]
   - **Alternatives Considered**: [What else was evaluated]

   ### Decision 2: [Another Key Decision]
   [Same structure]

   ## Component Diagram

   ```
   ┌─────────────────────────────────────────────────────┐
   │                   Application                       │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │  ┌─────────────┐    ┌──────────────┐              │
   │  │   API Layer │◄───┤ Auth Service │              │
   │  └──────┬──────┘    └──────────────┘              │
   │         │                                           │
   │         ▼                                           │
   │  ┌─────────────┐                                   │
   │  │ Core Logic  │                                   │
   │  └──────┬──────┘                                   │
   │         │                                           │
   │         ▼                                           │
   │  ┌─────────────┐    ┌──────────────┐              │
   │  │ Data Layer  │◄───┤ Cache Service│              │
   │  └──────┬──────┘    └──────────────┘              │
   │         │                                           │
   └─────────┼───────────────────────────────────────────┘
             ▼
      ┌─────────────┐
      │  Database   │
      └─────────────┘
   ```

   ## Technology Stack

   | Layer | Technology | Version | Rationale |
   |-------|-----------|---------|-----------|
   | Runtime | Node.js | 20+ | LTS, modern features, performance |
   | Framework | Express/Fastify/NestJS | Latest | [Why chosen] |
   | Database | PostgreSQL/MongoDB | Latest | [Why chosen] |
   | Cache | Redis | 7+ | Fast in-memory storage |
   | Frontend | React/Vue/Angular | Latest | [Why chosen] |
   | Build Tool | Webpack/Vite/esbuild | Latest | [Why chosen] |
   | Testing | Jest/Vitest | Latest | Rich ecosystem |

   ## Scalability Considerations

   - **Horizontal Scaling**: [How the system scales horizontally]
   - **Vertical Scaling**: [Limits and considerations]
   - **Bottlenecks**: [Known bottlenecks and mitigation]
   - **Performance Targets**: [SLAs and performance goals]

   ## Security Architecture

   - **Authentication**: [Method and implementation]
   - **Authorization**: [RBAC/ABAC approach]
   - **Data Protection**: [Encryption, PII handling]
   - **Network Security**: [TLS, firewall rules, etc.]
   - **Secrets Management**: [How secrets are stored/accessed]
   ```

2. **Design Decisions Documentation**

   Create an Architecture Decision Record (ADR) for each major decision:

   ```markdown
   # Architecture Decision Records

   ## ADR-001: [Decision Title]

   **Status**: [Proposed/Accepted/Deprecated/Superseded]
   **Date**: [YYYY-MM-DD]
   **Deciders**: [Names/roles]
   **Technical Story**: [Issue/ticket number]

   ### Context

   [Describe the problem or situation requiring a decision.
   Include technical, business, and organizational context.]

   ### Decision

   [State the decision clearly and concisely]

   ### Rationale

   **Why this approach was chosen**:
   - [Reason 1]
   - [Reason 2]
   - [Reason 3]

   **Alternatives Considered**:

   #### Alternative 1: [Name]
   - **Pros**: [Benefits]
   - **Cons**: [Drawbacks]
   - **Why Rejected**: [Reason]

   #### Alternative 2: [Name]
   - **Pros**: [Benefits]
   - **Cons**: [Drawbacks]
   - **Why Rejected**: [Reason]

   ### Consequences

   **Positive**:
   - [Benefit 1]
   - [Benefit 2]

   **Negative**:
   - [Trade-off 1]
   - [Trade-off 2]

   **Risks**:
   - [Risk 1 and mitigation]
   - [Risk 2 and mitigation]

   ### Implementation Notes

   [Technical details about implementation]

   ### References

   - [Link to relevant documentation]
   - [Link to discussion thread]
   - [Related ADRs]

   ---

   ## ADR-002: [Next Decision]
   [Same structure]
   ```

## Phase 2: Module Organization

Document the codebase structure:

```markdown
# Module Organization

## Directory Structure

```
project/
├── src/
│   ├── index.js                # Application entry point
│   │
│   ├── api/                    # API layer (REST/GraphQL)
│   │   ├── routes/             # Route definitions
│   │   │   ├── index.js
│   │   │   ├── users.js
│   │   │   └── products.js
│   │   ├── middleware/         # Request/response middleware
│   │   │   ├── auth.js
│   │   │   ├── errorHandler.js
│   │   │   └── rateLimit.js
│   │   └── controllers/        # Request handlers
│   │       ├── userController.js
│   │       └── productController.js
│   │
│   ├── services/               # Business logic layer
│   │   ├── userService.js      # User-related business logic
│   │   ├── productService.js   # Product-related business logic
│   │   └── authService.js      # Authentication logic
│   │
│   ├── models/                 # Data models
│   │   ├── User.js             # User model/schema
│   │   ├── Product.js          # Product model/schema
│   │   └── index.js            # Model exports
│   │
│   ├── repositories/           # Data access layer
│   │   ├── userRepository.js   # User data access
│   │   ├── productRepository.js
│   │   └── baseRepository.js   # Base repository pattern
│   │
│   ├── infrastructure/         # External integrations
│   │   ├── database/
│   │   │   ├── connection.js   # Database connection
│   │   │   └── migrations/     # Database migrations
│   │   ├── cache/
│   │   │   └── redisClient.js  # Redis client
│   │   ├── queue/
│   │   │   └── jobQueue.js     # Message queue
│   │   └── external/
│   │       └── apiClients.js   # Third-party API clients
│   │
│   ├── utils/                  # Shared utilities
│   │   ├── logger.js           # Logging utility
│   │   ├── config.js           # Configuration management
│   │   ├── validators.js       # Input validators
│   │   └── helpers.js          # Helper functions
│   │
│   └── types/                  # TypeScript types (if using TS)
│       ├── index.d.ts
│       └── models.d.ts
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── fixtures/               # Test fixtures
│
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
├── config/                     # Configuration files
├── public/                     # Static assets (if web app)
└── dist/                       # Build output
```

## Layer Responsibilities

### API Layer (`src/api/`)

- **Purpose**: Handle HTTP requests/responses

- **Responsibilities**:
  - Route definition and request routing
  - Request validation and parsing
  - Response formatting
  - Authentication/authorization checks
  - Rate limiting and throttling

- **Dependencies**: Services layer only (no direct data access)

- **Key Files**:
  - `routes/`: Defines API endpoints
  - `middleware/`: Request/response processing
  - `controllers/`: Request handlers

### Services Layer (`src/services/`)

- **Purpose**: Business logic and domain operations

- **Responsibilities**:
  - Business rule enforcement
  - Data validation
  - Use case orchestration
  - Transaction coordination
  - Event emission

- **Dependencies**: Repositories for persistence, no API layer knowledge

- **Key Files**:
  - `userService.js`: User business logic
  - `productService.js`: Product business logic
  - `authService.js`: Authentication logic

### Repositories Layer (`src/repositories/`)

- **Purpose**: Data persistence and retrieval

- **Responsibilities**:
  - Database operations (CRUD)
  - Query building and optimization
  - Transaction management
  - Data mapping (DB ↔ Domain)

- **Dependencies**: Infrastructure layer for connections

- **Key Files**:
  - `userRepository.js`: User data access
  - `productRepository.js`: Product data access
  - `baseRepository.js`: Common repository logic

### Infrastructure Layer (`src/infrastructure/`)

- **Purpose**: External service integration

- **Responsibilities**:
  - Database connections
  - Cache operations
  - Message queue operations
  - File storage
  - Third-party API integration

- **Dependencies**: External services only

- **Key Files**:
  - `database/connection.js`: Database setup
  - `cache/redisClient.js`: Redis integration
  - `queue/jobQueue.js`: Queue integration

## Dependency Rules

1. **Dependencies flow inward**: API → Services → Repositories → Infrastructure
2. **Services layer is independent**: No dependencies on outer layers
3. **Use dependency injection**: Inject dependencies at boundaries
4. **Interfaces over implementations**: Use abstract classes or interfaces

## Module Dependencies

```
api/
├── depends on: services, utils
└── used by: index.js

services/
├── depends on: repositories, utils
└── used by: api

repositories/
├── depends on: infrastructure, utils
└── used by: services

infrastructure/
├── depends on: utils
└── used by: repositories

utils/
├── depends on: nothing (pure utilities)
└── used by: all layers
```

## Import Conventions

```javascript
// Node.js built-in modules
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');

// Third-party modules
const express = require('express');
const { body, validationResult } = require('express-validator');
const jwt = require('jsonwebtoken');

// Local application modules
const userService = require('./services/userService');
const logger = require('./utils/logger');
const { asyncHandler } = require('./utils/helpers');

// ES6 module syntax (if using ES modules)
import fs from 'fs';
import express from 'express';
import { userService } from './services/userService.js';
```

## Public vs Private APIs

### Public API (for external consumers)

- Defined in `src/api/routes/`

- Versioned endpoints (`/api/v1/...`)

- Fully documented with OpenAPI/Swagger

- Backward compatibility guaranteed

### Internal API (for internal modules)

- Exported functions/classes

- Documented with JSDoc comments

- May change between minor versions

### Private Implementation (internal only)

- Functions/classes not exported

- Prefixed with underscore (`_internalFunc`)

- No backward compatibility guarantee
```

## Phase 3: Data Flow Documentation

Document how data moves through the system:

```markdown
# Data Flow

## Request Flow

### Typical API Request Flow

```
1. Client Request
   │
   ▼
2. Load Balancer/API Gateway
   │
   ▼
3. Middleware (auth, logging, rate limit)
   │
   ▼
4. Route Handler (src/api/routes/)
   │
   ├─► Parse request body
   ├─► Validate request data
   └─► Extract authentication token
       │
       ▼
5. Controller (src/api/controllers/)
   │
   ├─► Map request to service call
   └─► Handle response formatting
       │
       ▼
6. Service (src/services/)
   │
   ├─► Apply business rules
   ├─► Orchestrate operations
   └─► Validate business constraints
       │
       ▼
7. Repository (src/repositories/)
   │
   ├─► Build query
   ├─► Execute database operation
   └─► Map DB models to domain models
       │
       ▼
8. Database
   │
   ▼
9. Response flows back up through layers
   │
   └─► Transform → Serialize → Return
```

### Example: User Creation Flow

```javascript
// 1. API Layer receives request
// src/api/routes/users.js
router.post('/users',
  body('email').isEmail(),
  body('password').isLength({ min: 8 }),
  asyncHandler(async (req, res) => {
    // Validate request
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // 2. Delegate to controller
    const user = await userController.createUser(req.body);
    res.status(201).json(user);
  })
);

// 3. Controller coordinates the operation
// src/api/controllers/userController.js
class UserController {
  async createUser(userData) {
    // Delegate to service layer
    const user = await userService.createUser(userData);
    return this.toDTO(user);
  }

  toDTO(user) {
    // Transform to API response format
    return {
      id: user.id,
      email: user.email,
      name: user.name,
      createdAt: user.createdAt
    };
  }
}

// 4. Service layer applies business logic
// src/services/userService.js
class UserService {
  constructor(userRepository, emailService) {
    this.userRepository = userRepository;
    this.emailService = emailService;
  }

  async createUser(userData) {
    // Validate business rules
    const exists = await this.userRepository.findByEmail(userData.email);
    if (exists) {
      throw new Error('User already exists');
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(userData.password, 10);

    // Create user
    const user = await this.userRepository.create({
      email: userData.email,
      name: userData.name,
      password: hashedPassword
    });

    // Trigger side effects (async)
    this.emailService.sendWelcomeEmail(user.email);

    return user;
  }
}

// 5. Repository persists data
// src/repositories/userRepository.js
class UserRepository {
  constructor(db) {
    this.db = db;
  }

  async create(userData) {
    // Insert into database
    const result = await this.db('users').insert(userData).returning('*');

    // Map to domain model
    return this.toDomain(result[0]);
  }

  async findByEmail(email) {
    const result = await this.db('users').where({ email }).first();
    return result ? this.toDomain(result) : null;
  }

  toDomain(dbRow) {
    // Map database row to domain model
    return {
      id: dbRow.id,
      email: dbRow.email,
      name: dbRow.name,
      createdAt: dbRow.created_at
    };
  }
}
```

## Event Flow

### Asynchronous Event Processing

```
1. Event Trigger
   │
   ▼
2. Event Published to Queue/Event Bus
   │
   ▼
3. Event Dispatcher Routes to Handlers
   │
   ├─► Handler 1: Send welcome email
   ├─► Handler 2: Update analytics
   └─► Handler 3: Trigger workflows
       │
       ▼
4. Each Handler Processes Independently
   │
   └─► Results logged/monitored
```

## State Management

### Server-Side State

- **Configuration**: Loaded at startup from environment

- **Database Connection Pool**: Managed by ORM/query builder

- **Cache**: Redis for session and application cache

- **Request State**: Stored in request object via middleware

### Client-Side State (if applicable)

- **Storage**: Redux/MobX/Context API

- **Persistence**: LocalStorage/SessionStorage

- **Synchronization**: WebSocket/Polling/SSE
```

## Phase 4: Integration Points

Document external integrations:

```markdown
# Integration Points

## External APIs

### Third-Party Service A

- **Purpose**: [What it's used for]

- **Documentation**: [URL to API docs]

- **Authentication**: [Method: API key, OAuth, etc.]

- **Rate Limits**: [Requests per second/minute]

- **Endpoints Used**:
  - `GET /api/v1/resource`: [Description]
  - `POST /api/v1/action`: [Description]

- **Error Handling**: [How failures are handled]

- **Retry Strategy**: [Exponential backoff, max retries, etc.]

- **Monitoring**: [Health checks, alerting]

**Example Integration**:
```javascript
const axios = require('axios');

class ExternalServiceClient {
  constructor(apiKey, baseUrl) {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });

    // Add retry logic
    this.client.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 429) {
          // Rate limited - implement backoff
          await this.sleep(5000);
          return this.client.request(error.config);
        }
        throw error;
      }
    );
  }

  async fetchResource(resourceId) {
    try {
      const response = await this.client.get(`/resource/${resourceId}`);
      return response.data;
    } catch (error) {
      logger.error('External API error:', error);
      throw new ExternalAPIError(`Failed to fetch resource: ${error.message}`);
    }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Database Schema

### Tables

#### `users` table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### `sessions` table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
```

### Migrations

- **Tool**: Knex.js / Sequelize / TypeORM

- **Location**: `src/infrastructure/database/migrations/`

- **Process**:
  ```bash
  # Create new migration
  npx knex migrate:make migration_name

  # Run migrations
  npx knex migrate:latest

  # Rollback
  npx knex migrate:rollback
  ```

## Message Queue

### Job Queue (Bull/BullMQ)

- **Broker**: Redis

- **Queues**:
  - `email-queue`: Email sending jobs
  - `import-queue`: Batch data imports
  - `report-queue`: Report generation

- **Workers**: Separate worker processes

**Example Job**:
```javascript
const Queue = require('bull');
const emailQueue = new Queue('email', 'redis://localhost:6379');

// Producer: Add job to queue
async function sendWelcomeEmail(userId) {
  await emailQueue.add('welcome', {
    userId,
    type: 'welcome'
  }, {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  });
}

// Consumer: Process jobs
emailQueue.process('welcome', async (job) => {
  const { userId } = job.data;
  const user = await userRepository.findById(userId);

  await emailService.send({
    to: user.email,
    template: 'welcome',
    data: { name: user.name }
  });
});
```

## Authentication & Authorization

### Authentication Flow
1. User submits credentials
2. Server validates against database
3. Server generates JWT with user claims
4. Token returned to client
5. Client includes token in subsequent requests
6. Server validates token on each request

### Authorization

- **Method**: Role-Based Access Control (RBAC)

- **Roles**: admin, user, guest

- **Permissions**: Defined per endpoint

- **Implementation**: Express middleware

```javascript
const jwt = require('jsonwebtoken');

// Authentication middleware
function authenticate(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// Authorization middleware
function authorize(...roles) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Not authenticated' });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
}

// Usage
router.get('/admin/users', authenticate, authorize('admin'), async (req, res) => {
  // Only accessible to admins
});
```
```

## Phase 5: Development Workflow

Document the development process:

```markdown
# Development Workflow

## Development Environment Setup

### Prerequisites

- Node.js 20+ (LTS)

- npm/yarn/pnpm

- PostgreSQL 15+ / MongoDB 6+

- Redis 7+

- Docker (optional)

### Local Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/org/project.git
   cd project
   ```

2. **Install Dependencies**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Setup Database**
   ```bash
   # Run migrations
   npm run migrate:latest

   # Seed data (optional)
   npm run seed
   ```

5. **Start Services**
   ```bash
   # Start Redis (if not using Docker)
   redis-server

   # Start application in development mode
   npm run dev

   # Or use Docker Compose
   docker-compose up -d
   ```

## Build Process

### Local Build
```bash
# Run linter
npm run lint

# Fix linting issues
npm run lint:fix

# Run tests
npm test

# Build for production
npm run build
```

### Docker Build
```bash
# Build image
docker build -t project:latest .

# Run container
docker run -p 3000:3000 project:latest
```

## Testing Strategy

### Test Pyramid

- **Unit Tests** (70%): Fast, isolated, test individual functions

- **Integration Tests** (20%): Test component integration

- **E2E Tests** (10%): Test complete user workflows

### Running Tests
```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Test Organization
```
tests/
├── unit/
│   ├── services/          # Service tests
│   ├── repositories/      # Repository tests
│   └── utils/             # Utility tests
├── integration/
│   ├── api/               # API integration tests
│   └── database/          # Database integration tests
└── e2e/
    └── scenarios/         # End-to-end scenarios
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      - run: npm run lint

      - run: npm test

      - run: npm run build

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: # Deployment commands
```

### Deployment Process

1. **Development**: Push to feature branch
2. **PR Review**: Create pull request, CI runs tests
3. **Merge**: Merge to main after approval
4. **Deploy to Staging**: Automatic deployment
5. **Manual Testing**: QA testing on staging
6. **Deploy to Production**: Manual trigger after approval

## Release Process

1. **Version Bump**: Update version in `package.json`
2. **Update Changelog**: Document changes in `CHANGELOG.md`
3. **Create Release Branch**: `release/vX.Y.Z`
4. **Final Testing**: Run full test suite
5. **Tag Release**: `git tag vX.Y.Z`
6. **Deploy**: Trigger production deployment
7. **Announce**: Notify users of new version

---
```

## Output Format

Please provide technical documentation in this format:

### Documentation Structure

```markdown
## ARCHITECTURE.md
[High-level architecture documentation]

---

## ADR/
[Architecture Decision Records for key decisions]

---

## DEVELOPMENT.md
[Development workflow and setup guide]

---

## INTEGRATIONS.md
[External integration documentation]

---
```

### Summary Report

```markdown
## Technical Documentation Summary

**Documents Created**:

- Architecture Overview: [Yes/No]

- Architecture Decision Records: [count]

- Module Organization: [Yes/No]

- Data Flow Documentation: [Yes/No]

- Integration Documentation: [Yes/No]

- Development Workflow: [Yes/No]

**Diagrams Created**:

- Architecture diagram: [Yes/No]

- Component diagram: [Yes/No]

- Data flow diagram: [Yes/No]

- Deployment diagram: [Yes/No]

**Technical Decisions Documented**: [count]
**External Integrations Documented**: [count]

**Quality Checks**:

- [ ] Architecture clearly explained

- [ ] Design decisions have rationale

- [ ] Module organization mapped

- [ ] Data flows illustrated

- [ ] Integration points documented

- [ ] Development workflow complete

- [ ] Diagrams accurate and up-to-date

**Target Audience**: Development team, technical stakeholders
```

---

## Best Practices

1. **Keep Documentation Close to Code**
   - Store ADRs in repo
   - Update docs with code changes
   - Link docs from code comments

2. **Use Diagrams**
   - Architecture diagrams
   - Sequence diagrams for flows
   - Entity-relationship diagrams

3. **Document Decisions**
   - Why, not just what
   - Alternatives considered
   - Trade-offs made

4. **Maintain Currency**
   - Review during PRs
   - Update with major changes
   - Mark obsolete docs

5. **Progressive Detail**
   - Start high-level
   - Drill down to specifics
   - Link between levels

---

## Output Format Specifications

The technical documentation should:

- Provide high-level architecture overview with diagrams

- Document design decisions with rationale and alternatives

- Map module organization and dependencies clearly

- Illustrate data flows through the system

- Document all external integrations comprehensively

- Explain development workflow and processes

- Be maintained alongside code changes

- Target technical audience (developers, architects)

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
