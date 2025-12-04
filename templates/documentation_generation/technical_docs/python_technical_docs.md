---
template_id: python_technical_docs
template_name: Technical Docs - Python
version: 1.0.0
last_updated: 2025-12-03
language: Python
category: documentation
phase: technical_docs
difficulty: beginner
estimated_time_hours: 4-6
prerequisites: []
tools:
  - pytest (8.3.4+)
  - black (24.12.0)
  - mypy (1.13.0)
  - ruff
tags:
  - documentation
  - documentation
  - python
---
# Python Technical Documentation

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

- [ ] Import structure documented

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
# Python Technical Documentation Request

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

Please create comprehensive technical documentation for this Python project following this protocol:

## Phase 1: Architecture Analysis

1. **System Architecture Overview**

   Document the high-level architecture:

   ```markdown
   # System Architecture

   ## Overview

   [Project Name] is built as a [monolith/microservice/library/framework] that [high-level purpose].

   ## Architecture Style

   - **Pattern**: [MVC/Layered/Hexagonal/Event-Driven/etc.]
   - **Deployment**: [Single instance/distributed/serverless/etc.]
   - **State Management**: [Stateless/stateful/hybrid]
   - **Communication**: [Synchronous/asynchronous/hybrid]

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
   | Runtime | Python | 3.11+ | Modern features, performance |
   | Web Framework | FastAPI | 0.100+ | Async support, type hints |
   | Database | PostgreSQL | 15+ | ACID, JSON support |
   | Cache | Redis | 7+ | Fast in-memory storage |
   | Task Queue | Celery | 5+ | Distributed task processing |
   | Testing | pytest | 7+ | Rich plugin ecosystem |

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
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   │
│   ├── api/                    # API layer (REST/GraphQL)
│   │   ├── __init__.py
│   │   ├── routes.py           # Route definitions
│   │   ├── middleware.py       # Request/response middleware
│   │   └── dependencies.py     # Dependency injection
│   │
│   ├── core/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── models.py           # Domain models
│   │   ├── services.py         # Business logic services
│   │   ├── validators.py       # Input validation
│   │   └── exceptions.py       # Custom exceptions
│   │
│   ├── data/                   # Data access layer
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection
│   │   ├── repositories.py     # Data access patterns
│   │   ├── models.py           # ORM models
│   │   └── migrations/         # Database migrations
│   │
│   ├── infrastructure/         # External integrations
│   │   ├── __init__.py
│   │   ├── cache.py            # Cache service
│   │   ├── queue.py            # Message queue
│   │   ├── storage.py          # File storage
│   │   └── external_apis.py    # Third-party API clients
│   │
│   └── utils/                  # Shared utilities
│       ├── __init__.py
│       ├── logging.py          # Logging configuration
│       ├── config.py           # Configuration management
│       └── helpers.py          # Helper functions
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # End-to-end tests
│   └── fixtures/               # Test fixtures
│
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── config/                     # Configuration files
```

## Layer Responsibilities

### API Layer (`src/api/`)

- **Purpose**: Handle HTTP requests/responses

- **Responsibilities**:
  - Route definition and request routing
  - Request validation and serialization
  - Response formatting
  - Authentication/authorization checks
  - Rate limiting and throttling

- **Dependencies**: Core layer only (no direct data access)

- **Key Files**:
  - `routes.py`: Defines API endpoints
  - `middleware.py`: Request/response processing
  - `dependencies.py`: Dependency injection for routes

### Core Layer (`src/core/`)

- **Purpose**: Business logic and domain models

- **Responsibilities**:
  - Domain model definitions
  - Business rule enforcement
  - Data validation
  - Use case orchestration
  - Domain events

- **Dependencies**: Data layer for persistence, no API layer knowledge

- **Key Files**:
  - `models.py`: Domain entities and value objects
  - `services.py`: Business logic services
  - `validators.py`: Business rule validation

### Data Layer (`src/data/`)

- **Purpose**: Data persistence and retrieval

- **Responsibilities**:
  - Database connection management
  - CRUD operations
  - Query optimization
  - Transaction management
  - Migration management

- **Dependencies**: Infrastructure layer for connections

- **Key Files**:
  - `repositories.py`: Repository pattern implementation
  - `models.py`: ORM models (SQLAlchemy/etc.)
  - `database.py`: Database session management

### Infrastructure Layer (`src/infrastructure/`)

- **Purpose**: External service integration

- **Responsibilities**:
  - Cache operations
  - Message queue operations
  - File storage
  - Third-party API integration
  - Email/SMS services

- **Dependencies**: External services only

- **Key Files**:
  - `cache.py`: Redis/Memcached integration
  - `queue.py`: Celery/RabbitMQ integration
  - `external_apis.py`: Third-party API clients

## Dependency Rules

1. **Dependencies flow inward**: API → Core → Data → Infrastructure
2. **Core layer is independent**: No dependencies on outer layers
3. **Use dependency injection**: Inject dependencies at boundaries
4. **Interfaces over implementations**: Define protocols/abstract bases

## Module Dependencies

```
api/
├── depends on: core, utils
└── used by: main.py

core/
├── depends on: data, utils
└── used by: api, tests

data/
├── depends on: infrastructure, utils
└── used by: core

infrastructure/
├── depends on: utils
└── used by: data

utils/
├── depends on: nothing (pure utilities)
└── used by: all layers
```

## Import Conventions

```python
# Standard library imports
import os
import sys
from typing import List, Optional

# Third-party imports
import numpy as np
from fastapi import FastAPI, HTTPException
from sqlalchemy import Column, Integer, String

# Local application imports
from src.core.models import User
from src.core.services import UserService
from src.data.repositories import UserRepository
from src.utils.logging import get_logger
```

## Public vs Private APIs

### Public API (for external consumers)

- Defined in `src/api/routes.py`

- Versioned endpoints (`/api/v1/...`)

- Fully documented with OpenAPI/Swagger

- Backward compatibility guaranteed

### Internal API (for internal modules)

- Public functions/classes (no underscore prefix)

- Documented with docstrings

- May change between minor versions

### Private Implementation (internal only)

- Functions/classes with underscore prefix (`_internal_func`)

- No backward compatibility guarantee

- May change without notice
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
2. API Gateway/Load Balancer
   │
   ▼
3. Middleware (auth, logging, rate limit)
   │
   ▼
4. Route Handler (src/api/routes.py)
   │
   ├─► Validate request data
   └─► Extract authentication token
       │
       ▼
5. Business Service (src/core/services.py)
   │
   ├─► Apply business rules
   ├─► Orchestrate operations
   └─► Validate business constraints
       │
       ▼
6. Repository (src/data/repositories.py)
   │
   ├─► Build query
   ├─► Execute database operation
   └─► Map ORM models to domain models
       │
       ▼
7. Database
   │
   ▼
8. Response flows back up through layers
   │
   └─► Transform → Serialize → Return
```

### Example: User Creation Flow

```python
# 1. API Layer receives request
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    # 2. Delegate to service layer
    user = await user_service.create_user(user_data)
    return UserResponse.from_domain(user)

# 3. Service layer applies business logic
class UserService:
    async def create_user(self, user_data: UserCreate) -> User:
        # Validate business rules
        if await self.repository.email_exists(user_data.email):
            raise EmailAlreadyExistsError()

        # Create domain model
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )

        # Persist via repository
        saved_user = await self.repository.save(user)

        # Trigger side effects (async)
        await self.event_bus.publish(UserCreatedEvent(saved_user))

        return saved_user

# 4. Repository persists data
class UserRepository:
    async def save(self, user: User) -> User:
        # Map domain model to ORM model
        db_user = UserModel(
            email=user.email,
            hashed_password=user.hashed_password
        )

        # Persist to database
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)

        # Map back to domain model
        return User.from_orm(db_user)
```

## Event Flow

### Asynchronous Event Processing

```
1. Event Trigger
   │
   ▼
2. Event Published to Queue
   │
   ▼
3. Event Bus Routes to Handlers
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

### Application State

- **Configuration**: Loaded at startup, immutable

- **Database Connection Pool**: Managed by SQLAlchemy

- **Cache**: Redis for session and application cache

- **Request State**: Stored in request context (FastAPI Depends)

### User Session State

- **Storage**: Redis with 24-hour TTL

- **Format**: JSON Web Token (JWT)

- **Synchronization**: Single source of truth in Redis
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
```python
class ExternalServiceClient:
    """Client for Third-Party Service A."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5)
        )

    async def fetch_resource(self, resource_id: str) -> Dict:
        """Fetch resource from external service."""
        try:
            response = await self.session.get(
                f"{self.base_url}/api/v1/resource/{resource_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited - implement backoff
                raise RateLimitError()
            raise ExternalAPIError(f"API error: {e}")
```

## Database Schema

### Tables

#### `users` table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
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

- **Tool**: Alembic

- **Location**: `src/data/migrations/`

- **Process**:
  ```bash
  # Create new migration
  alembic revision --autogenerate -m "description"

  # Apply migrations
  alembic upgrade head

  # Rollback
  alembic downgrade -1
  ```

## Message Queue

### Celery Tasks

- **Broker**: Redis

- **Backend**: Redis

- **Tasks**:
  - `send_welcome_email`: Triggered on user registration
  - `process_batch_import`: Handles bulk data imports
  - `generate_daily_report`: Scheduled daily at midnight

**Example Task**:
```python
@celery_app.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id: str):
    """Send welcome email to new user."""
    try:
        user = UserRepository().get_by_id(user_id)
        email_service.send_template(
            to=user.email,
            template="welcome",
            context={"name": user.name}
        )
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
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

- **Implementation**: FastAPI dependency injection

```python
def require_role(required_role: str):
    """Dependency to check user role."""
    async def role_checker(token: str = Depends(oauth2_scheme)):
        user = await get_current_user(token)
        if user.role != required_role:
            raise PermissionDenied()
        return user
    return role_checker

# Usage
@router.get("/admin/users")
async def list_users(admin: User = Depends(require_role("admin"))):
    # Only accessible to admins
    pass
```
```

## Phase 5: Development Workflow

Document the development process:

```markdown
# Development Workflow

## Development Environment Setup

### Prerequisites

- Python 3.11+

- PostgreSQL 15+

- Redis 7+

- Docker (optional)

### Local Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/org/project.git
   cd project
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Setup Database**
   ```bash
   # Create database
   createdb project_dev

   # Run migrations
   alembic upgrade head

   # Seed data (optional)
   python scripts/seed_database.py
   ```

6. **Start Services**
   ```bash
   # Start Redis (if not using Docker)
   redis-server

   # Start application
   uvicorn src.main:app --reload

   # Start Celery worker (separate terminal)
   celery -A src.worker worker --loglevel=info
   ```

## Build Process

### Local Build
```bash
# Run linters
black src/ tests/
flake8 src/ tests/
mypy src/

# Run tests
pytest tests/ -v --cov=src

# Build package
python -m build
```

### Docker Build
```bash
# Build image
docker build -t project:latest .

# Run container
docker run -p 8000:8000 project:latest
```

## Testing Strategy

### Test Pyramid

- **Unit Tests** (70%): Fast, isolated, test individual functions

- **Integration Tests** (20%): Test component integration

- **E2E Tests** (10%): Test complete user workflows

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html

# Specific test
pytest tests/unit/test_users.py::test_create_user
```

### Test Organization
```
tests/
├── unit/
│   ├── test_services.py    # Business logic tests
│   ├── test_models.py      # Model tests
│   └── test_validators.py  # Validation tests
├── integration/
│   ├── test_api.py         # API integration tests
│   └── test_database.py    # Database integration tests
└── e2e/
    └── test_user_flow.py   # End-to-end scenarios
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest --cov=src
      - run: black --check src/
      - run: flake8 src/
      - run: mypy src/

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

1. **Version Bump**: Update version in `pyproject.toml`
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
