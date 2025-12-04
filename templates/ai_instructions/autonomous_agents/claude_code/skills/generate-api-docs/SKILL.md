---
name: generate-api-docs
description: Generate comprehensive API reference documentation with examples for all public interfaces across multiple languages
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language (Python, JavaScript, Java, C#, Go, C, C++)
category: Documentation
tags: [documentation, api, reference, multi-language, openapi, swagger]
template_sources:
  - documentation/api_docs/python_api_docs.md
  - documentation/api_docs/javascript_api_docs.md
  - documentation/api_docs/java_api_docs.md
  - documentation/api_docs/csharp_api_docs.md
  - documentation/api_docs/go_api_docs.md
  - documentation/api_docs/c_api_docs.md
  - documentation/api_docs/cpp_api_docs.md
---

# Generate API Documentation

Create comprehensive, production-ready API reference documentation with examples, schemas, and integration guides for all public interfaces in your codebase.

## When to Use This Skill

Use this skill when you need to:
- Document REST APIs, GraphQL APIs, or gRPC services
- Create reference documentation for public libraries/SDKs
- Generate OpenAPI/Swagger specifications
- Document CLI commands and options
- Create API integration guides with examples
- Maintain up-to-date API documentation
- Prepare for API publication or external consumption

## What This Skill Does

This skill generates language-appropriate API documentation:

### For All Languages
1. **Public Interface Documentation**
   - Classes, methods, functions with parameters and returns
   - Type signatures and schemas
   - Error conditions and exceptions
   - Usage examples for each endpoint/function

2. **API Organization**
   - Logical grouping of related endpoints
   - Versioning information
   - Authentication and authorization
   - Rate limiting and quotas

3. **Integration Examples**
   - Code samples in multiple languages
   - Common use cases and patterns
   - Error handling examples
   - SDK usage guides

4. **Reference Material**
   - Data models and schemas
   - Enumeration values
   - Constants and configuration
   - Changelog and migration guides

### Language-Specific Features

#### Python
- **Sphinx/ReadTheDocs**: reStructuredText or Markdown
- **Type Hints**: Leverages Python type annotations
- **Docstrings**: NumPy/Google/Sphinx style
- **Tools**: Sphinx, MkDocs, pdoc

#### JavaScript/TypeScript
- **JSDoc**: Comprehensive JSDoc comments
- **TypeScript**: Full type definitions
- **OpenAPI**: Swagger/OpenAPI 3.0 specs
- **Tools**: JSDoc, TypeDoc, Swagger UI

#### Java
- **JavaDoc**: Standard JavaDoc format
- **Annotations**: JAX-RS, Spring annotations
- **OpenAPI**: Springdoc-openapi integration
- **Tools**: JavaDoc, Swagger, Asciidoctor

#### C#
- **XML Comments**: Triple-slash documentation
- **Swagger/OpenAPI**: NSwag, Swashbuckle
- **API Controllers**: ASP.NET Core documentation
- **Tools**: DocFX, Sandcastle, Swagger

#### Go
- **Godoc**: Standard godoc format
- **Comments**: Package and function comments
- **OpenAPI**: go-swagger, oapi-codegen
- **Tools**: godoc, pkgsite, swaggo

#### C
- **Doxygen**: Comprehensive C documentation
- **Header Files**: Interface documentation
- **Function Declarations**: Parameter descriptions
- **Tools**: Doxygen, GTK-Doc

#### C++
- **Doxygen**: Modern C++ documentation
- **Concepts**: C++20 concepts documentation
- **Templates**: Template parameter documentation
- **Tools**: Doxygen, Breathe, Sphinx

## Prerequisites

- Codebase with public API or library interfaces
- Version control for tracking documentation updates
- Output directory for generated documentation
- Optional: API testing framework for validation

## Instructions

### Step 1: Prepare Your Environment

1. **Identify API Scope**:
   - List all public endpoints/functions
   - Group by module/resource
   - Identify versioning scheme

2. **Create Output Directory**:
   ```bash
   mkdir -p api_docs/{templates,assets,exports}
   ```

3. **Check Existing Documentation**:
   ```bash
   find . -name "*.md" -o -name "openapi.yaml" -o -name "swagger.json"
   ```

### Step 2: Invoke the API Documentation Skill

For **Python** APIs:
```
"Use the generate-api-docs skill to create comprehensive Python API documentation.

Language: Python
API Type: REST API / Library SDK / CLI
Documentation Format: Sphinx / MkDocs / ReadTheDocs
Include: OpenAPI specs, usage examples, authentication guide
Output: api_docs/ directory"
```

For **JavaScript/TypeScript** APIs:
```
"Use the generate-api-docs skill for JavaScript/TypeScript API.

Language: JavaScript/TypeScript
API Type: REST API / Node.js library / Express routes
Documentation Format: JSDoc / TypeDoc / Swagger UI
Include: OpenAPI 3.0 spec, TypeScript types, integration examples
Output: api_docs/ directory"
```

For **Other Languages**:
Adapt the prompt with appropriate language-specific details.

### Step 3: Review Generated Documentation Structure

The skill generates organized API documentation:

```
api_docs/
├── templates/
│   ├── endpoint_template.md      # Reusable endpoint documentation template
│   ├── schema_template.md        # Data model template
│   └── example_requests.md       # Request/response examples
├── assets/
│   ├── architecture_diagram.png  # API architecture visualization
│   ├── auth_flow.png            # Authentication flow diagram
│   └── data_model.png           # Entity relationship diagram
└── exports/
    ├── api_reference.md         # Complete API reference
    ├── openapi.yaml            # OpenAPI/Swagger specification
    ├── getting_started.md      # Quick start guide
    ├── authentication.md       # Auth documentation
    ├── rate_limiting.md       # Rate limit documentation
    ├── error_codes.md         # Error reference
    ├── changelog.md           # API version history
    └── examples/              # Code examples directory
        ├── python/
        ├── javascript/
        └── curl/
```

### Step 4: Customize and Enhance

1. **Add Custom Examples**:
   - Real-world use cases
   - Language-specific SDK examples
   - Integration scenarios

2. **Include Authentication Details**:
   - API keys, OAuth, JWT
   - Token management
   - Security best practices

3. **Add Versioning Information**:
   - Current version
   - Deprecated endpoints
   - Migration guides

4. **Performance Guidelines**:
   - Rate limiting
   - Pagination
   - Caching strategies

### Step 5: Generate Interactive Documentation

#### For OpenAPI/Swagger:

**Python (FastAPI/Flask)**:
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Your routes here

# Generate OpenAPI spec
with open("api_docs/exports/openapi.json", "w") as f:
    json.dump(get_openapi(
        title="My API",
        version="1.0.0",
        routes=app.routes
    ), f)
```

**JavaScript (Express + swagger-jsdoc)**:
```javascript
const swaggerJsdoc = require('swagger-jsdoc');
const swaggerUi = require('swagger-ui-express');

const options = {
  definition: {
    openapi: '3.0.0',
    info: { title: 'My API', version: '1.0.0' }
  },
  apis: ['./routes/*.js']
};

const specs = swaggerJsdoc(options);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs));
```

**Java (Spring Boot + Springdoc)**:
```java
@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("My API")
                .version("1.0.0"));
    }
}
```

### Step 6: Publish Documentation

1. **Static Site Hosting**:
   ```bash
   # For MkDocs
   mkdocs build
   mkdocs serve

   # For Sphinx
   sphinx-build -b html docs/source docs/build

   # For Docusaurus
   npm run build
   npm run serve
   ```

2. **Documentation Platforms**:
   - ReadTheDocs.org (Python)
   - GitHub Pages (all languages)
   - GitLab Pages (all languages)
   - Netlify / Vercel (all languages)
   - SwaggerHub (OpenAPI)

3. **Internal Hosting**:
   - Corporate wiki
   - Internal documentation server
   - Confluence integration

## Documentation Examples by Language

### Python FastAPI Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="User Management API",
    description="Comprehensive user management service",
    version="1.0.0"
)

class User(BaseModel):
    """
    User data model.

    Attributes:
        id: Unique user identifier
        name: User's full name
        email: User's email address
        active: Account status
    """
    id: int
    name: str
    email: str
    active: bool = True

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Retrieve user by ID.

    Args:
        user_id: The unique identifier for the user

    Returns:
        User: The user object if found

    Raises:
        HTTPException: 404 if user not found

    Example:
        ```python
        response = requests.get("http://api.example.com/users/123")
        user = response.json()
        print(f"User: {user['name']}")
        ```
    """
    # Implementation
    pass
```

### JavaScript Express Example

```javascript
/**
 * @swagger
 * /users/{id}:
 *   get:
 *     summary: Retrieve user by ID
 *     description: Get detailed information about a specific user
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: integer
 *         description: Unique user identifier
 *     responses:
 *       200:
 *         description: User object
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/User'
 *       404:
 *         description: User not found
 *     tags:
 *       - Users
 */
router.get('/users/:id', async (req, res) => {
    // Implementation
});
```

### Java Spring Boot Example

```java
/**
 * User management controller.
 *
 * <p>Provides endpoints for user CRUD operations.</p>
 *
 * @author Benjamin Dourthe
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "User management endpoints")
public class UserController {

    /**
     * Retrieve user by ID.
     *
     * @param id the unique user identifier
     * @return the user object if found
     * @throws UserNotFoundException if user doesn't exist
     */
    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID",
               description = "Retrieve detailed user information")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "User found"),
        @ApiResponse(responseCode = "404", description = "User not found")
    })
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        // Implementation
    }
}
```

## Quality Checklist

Before finalizing API documentation, verify:

- [ ] All public endpoints/functions documented
- [ ] Request/response schemas defined
- [ ] Authentication methods explained
- [ ] Error codes and messages documented
- [ ] Rate limiting details provided
- [ ] Code examples included (at least 2 languages)
- [ ] Common use cases demonstrated
- [ ] Versioning information clear
- [ ] Changelog maintained
- [ ] Migration guides for breaking changes
- [ ] Interactive documentation generated (OpenAPI UI)
- [ ] Documentation tested with real API calls
- [ ] Links and references validated
- [ ] Search functionality working (if applicable)
- [ ] Documentation published and accessible

## Common Issues and Solutions

### Issue: Documentation Out of Sync with Code
**Solution**:
- Integrate documentation generation into CI/CD
- Use doc-testing to validate examples
- Automate OpenAPI spec generation from code

### Issue: Incomplete Type Information
**Solution**:
- Add comprehensive type hints (Python)
- Use TypeScript instead of JavaScript
- Enable strict mode in type checkers

### Issue: Missing Examples
**Solution**:
- Create example gallery template
- Include curl commands for all endpoints
- Provide SDK examples for common languages

### Issue: Poor Organization
**Solution**:
- Group by resource/domain
- Use clear hierarchical structure
- Provide search and navigation

## Success Criteria

After using this skill, you should have:

- [ ] Complete API reference documentation
- [ ] OpenAPI/Swagger specification (for REST APIs)
- [ ] Authentication and authorization guide
- [ ] Code examples in multiple languages
- [ ] Error reference with all codes
- [ ] Getting started / quick start guide
- [ ] Interactive documentation (Swagger UI / equivalent)
- [ ] Changelog with version history
- [ ] Migration guides for major versions
- [ ] Documentation published and accessible

## Related Skills

- `generate-docstrings`: Create inline code documentation first
- `create-user-documentation`: Build user-facing guides
- `create-technical-docs`: Document architecture
- `setup-test-infrastructure`: Test API endpoints

## Tools by Language

### Python
- Sphinx, MkDocs, pdoc, FastAPI auto-docs
- sphinx-autodoc, sphinx-apidoc
- ReadTheDocs hosting

### JavaScript/TypeScript
- JSDoc, TypeDoc, API Extractor
- swagger-jsdoc, tsoa
- Docusaurus, VuePress

### Java
- JavaDoc, Asciidoctor, Springdoc
- swagger-core, swagger-annotations
- GitHub Pages, Maven sites

### C#
- DocFX, Sandcastle, Swagger/NSwag
- XML documentation comments
- Azure Static Web Apps

### Go
- godoc, pkgsite, swaggo
- go-swagger, oapi-codegen
- GitHub Pages

### C/C++
- Doxygen, Sphinx + Breathe
- GTK-Doc, Natural Docs
- Static site generation

## Additional Resources

- [OpenAPI Specification](https://swagger.io/specification/)
- [API Documentation Best Practices](https://swagger.io/blog/api-documentation/api-documentation-best-practices/)
- [Stripe API Documentation](https://stripe.com/docs/api) (excellent example)
- [Twilio API Docs](https://www.twilio.com/docs/usage/api) (great structure)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - documentation/api_docs/
