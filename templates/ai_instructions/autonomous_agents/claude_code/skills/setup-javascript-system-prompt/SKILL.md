---
name: setup-javascript-system-prompt
description: Configure comprehensive JavaScript/TypeScript development standards for Claude Code with best practices, testing frameworks, and modern workflows
version: 1.0.0
author: Benjamin Dourthe
language: JavaScript, TypeScript
category: Configuration
tags: [configuration, javascript, typescript, system-prompt, standards, node, react, jest, eslint]
priority: HIGH
template_source: agent_prompts/autonomous_agents/claude_code/javascript/
---

# Setup JavaScript/TypeScript System Prompt

Configure Claude Code with comprehensive JavaScript/TypeScript development standards, best practices, and workflows optimized for production-quality code generation across Node.js, React, and full-stack applications.

## When to Use This Skill

Use this skill when you need to:
- Set up a new JavaScript/TypeScript project with Claude Code
- Configure Claude Code for modern JavaScript development
- Apply comprehensive JavaScript/TypeScript development standards
- Establish consistent coding practices across JavaScript projects
- Optimize Claude Code for Node.js, React, or full-stack workflows
- Configure testing frameworks (Jest, Vitest, Mocha)
- Set up build tools (Webpack, Vite, esbuild)

## What This Skill Does

This skill helps you configure Claude Code with:

### 1. JavaScript/TypeScript Development Standards
- **Modern ES6+ syntax** and patterns
- **Import organization** (Node built-ins → third-party → local)
- **Type safety** with TypeScript strict mode
- **Function design** and naming conventions (camelCase, PascalCase)
- **100-character line length** (Prettier standard)
- **Comment guidelines** (no meta-commentary or change tracking)

### 2. Project Architecture Guidelines
- **Node.js backend structure** (src/, controllers/, services/, models/)
- **React frontend structure** (components/, hooks/, context/, pages/)
- **Full-stack application** organization
- **Configuration files** (package.json, tsconfig.json, .eslintrc.js)
- **Documentation structure** (README, CHANGELOG, DEVLOG)

### 3. Testing Frameworks
- **Jest configuration** for unit and integration tests
- **React Testing Library** for component tests
- **Test structure** (unit/, integration/, e2e/)
- **Coverage thresholds** (80% minimum)
- **Mock patterns** and test utilities

### 4. Code Quality Tools
- **ESLint** configuration with TypeScript support
- **Prettier** formatting standards
- **TypeScript** strict mode configuration
- **Pre-commit hooks** with Husky
- **Code review** checklists

### 5. Development Workflow
- **Task breakdown** methodology for complex features
- **Iterative testing protocol** (temp tests → iterate → cleanup)
- **Quality gates** and verification steps
- **Version control** best practices
- **NPM script** organization

### 6. Framework-Specific Guidance
- **Express.js** API development patterns
- **React** component architecture and hooks
- **Next.js** application structure
- **NestJS** modular backend architecture
- **GraphQL** schema and resolver patterns

## Prerequisites

- Claude Code installed and configured
- Node.js 18+ (LTS recommended) installed
- npm 9+ or yarn 1.22+ installed
- Basic understanding of JavaScript/TypeScript development
- Project directory created (or ready to create new project)

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**
- **Best for**: Complex projects, enterprise development, full-stack applications
- **Features**: Complete architectural guidance, extensive best practices, detailed error handling
- **Token count**: ~40,000 tokens
- **File**: `agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_comprehensive_40k.md`
- **Includes**: All frameworks, testing strategies, performance optimization

**Condensed Version (~20k tokens)**
- **Best for**: Quick development, prototyping, smaller projects, single-purpose apps
- **Features**: Essential guidelines, core best practices, streamlined workflow
- **Token count**: ~20,000 tokens
- **File**: `agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_condensed_20k.md`
- **Includes**: Core standards, basic testing, essential patterns

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the JavaScript system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

This method ensures all team members and Claude Code sessions use consistent standards.

1. **Navigate to your project root directory**
   ```bash
   cd /path/to/your/project
   ```

2. **Copy the chosen system prompt file to CLAUDE.md**:
   ```bash
   # For comprehensive version (recommended for production projects)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version (recommended for quick prototypes)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/javascript/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```

3. **Claude Code will automatically detect and load this file**
   - When you start Claude Code in this directory, it reads CLAUDE.md
   - All responses will follow the configured standards

#### Method B: Session-Based Configuration

This method applies standards only to the current Claude Code session.

```bash
# For comprehensive version
claude --system-prompt ./path/to/CLAUDE_comprehensive_40k.md

# For condensed version
claude --system-prompt ./path/to/CLAUDE_condensed_20k.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to perform standard tasks:

#### Test 1: Function Creation with TypeScript
```
"Create a function that fetches user data from an API with error handling"
```

**Expected behavior**:
- TypeScript type annotations included
- JSDoc comments present
- async/await pattern used
- Proper error handling with try-catch
- No inline comments unless necessary
- Import statements properly organized

#### Test 2: Project Structure Recommendation
```
"Show me the recommended project structure for a Node.js REST API with TypeScript"
```

**Expected behavior**:
- Includes src/, tests/, dist/ directories
- Shows package.json, tsconfig.json, .eslintrc.js
- Includes CHANGELOG.md, README.md, DEVLOG.md
- Recommends controllers/, services/, models/ organization
- Suggests testing structure (unit/, integration/)

#### Test 3: React Component Generation
```
"Create a React component for a user profile card with TypeScript"
```

**Expected behavior**:
- Functional component with TypeScript interface for props
- Proper JSDoc documentation
- Event handlers typed correctly
- Loading and error states included
- Follows React best practices (hooks, effects)

#### Test 4: Testing Framework Knowledge
```
"How should I structure my tests for this Express.js API?"
```

**Expected behavior**:
- Mentions Jest configuration
- Describes test structure (unit/, integration/, e2e/)
- Explains coverage thresholds
- Suggests mocking strategies
- Recommends test utilities

### Step 4: Initialize Project with Standards

If starting a new project, ask Claude Code to initialize it following the system prompt:

```
"Initialize a new TypeScript Node.js project with Express.js following the standards in CLAUDE.md"
```

Claude Code will:
1. Create proper directory structure
2. Initialize package.json with correct scripts
3. Configure tsconfig.json with strict mode
4. Set up ESLint and Prettier
5. Create Jest configuration
6. Add .gitignore with appropriate exclusions
7. Create README, CHANGELOG, and DEVLOG templates

### Step 5: Customize for Your Organization (Optional)

Add organization-specific standards without modifying the core prompt:

1. **Open the CLAUDE.md file** in your project
2. **Add a new section at the end**:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - **API Standards**: All APIs must follow RESTful conventions with versioning (v1/, v2/)
   - **Authentication**: Use JWT with refresh tokens, stored in httpOnly cookies
   - **Database**: PostgreSQL with TypeORM, migrations required for schema changes
   - **Logging**: Use Winston logger with structured JSON output
   - **Error Handling**: Custom error classes extending base Error, logged to Sentry
   - **Environment**: Use dotenv for configuration, never commit .env files
   - **Code Review**: Minimum 2 approvals required, 90% test coverage

   ## Internal Tools
   - **CI/CD**: GitHub Actions for automated testing and deployment
   - **Deployment**: Docker containers on AWS ECS
   - **Monitoring**: DataDog APM and New Relic for performance tracking

   ## Compliance Requirements
   - **Security**: OWASP Top 10 checks required
   - **Data Privacy**: GDPR compliance, data encryption at rest and in transit
   - **Accessibility**: WCAG 2.1 Level AA for all frontend components
   ```

3. **Save and restart Claude Code session** to apply changes

### Step 6: Configure ESLint and Prettier

Ensure your project has consistent code formatting:

#### .eslintrc.js Configuration
```javascript
module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    project: './tsconfig.json',
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'prettier',
  ],
  plugins: ['@typescript-eslint'],
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
};
```

#### .prettierrc Configuration
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always"
}
```

### Step 7: Set Up Testing Framework

Initialize Jest for testing:

```bash
npm install -D jest @types/jest ts-jest @testing-library/react @testing-library/jest-dom
```

#### jest.config.js
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

### Step 8: Commit to Version Control

Add the CLAUDE.md and configuration files to your repository:

```bash
git add CLAUDE.md .eslintrc.js .prettierrc jest.config.js tsconfig.json
git commit -m "Add Claude Code JavaScript/TypeScript system prompt configuration"
git push
```

## Key Features of the JavaScript/TypeScript System Prompt

### 1. Import Organization
Automatically organizes imports in the correct order:

1. **Node.js built-in modules** (fs, path, util) - alphabetically sorted
2. **Third-party libraries** (express, mongoose, lodash) - grouped by function with headers
3. **Local application imports** (@/core, @/utils) - alphabetically sorted
4. **Type imports** (type { User, Config }) - separate from value imports

**Example**:
```typescript
// Node.js built-ins
import * as fs from 'fs';
import * as path from 'path';

// Web framework
import express from 'express';
import cors from 'cors';

// Database
import mongoose from 'mongoose';

// Local imports
import { DatabaseManager } from '@/core/database';
import { formatResponse } from '@/utils/format';

// Type imports
import type { User, Config } from '@/types';
```

### 2. TypeScript Standards
- **Strict mode enabled**: No implicit any, proper null checks
- **Type annotations**: All public functions have return types
- **Interface over type**: Use interfaces for object shapes
- **Generics**: Type-safe reusable components
- **Utility types**: Leverage Pick, Omit, Partial, Record
- **Type guards**: Runtime type checking functions

### 3. Code Standards
- **Line length**: 100 characters (Prettier standard)
- **Functions**: One blank line between functions
- **Classes**: Two blank lines between classes
- **Comments**: Above code, explain "why" not "what"
- **No change-tracking comments**: Prevents "changed value to 12" style comments
- **JSDoc for public APIs**: Document parameters, returns, examples

### 4. Testing Framework
- **Jest** as primary testing framework
- **React Testing Library** for component tests
- **Coverage thresholds**: 80% minimum for branches, functions, lines
- **Test organization**: unit/, integration/, e2e/ directories
- **Mocking strategies**: Mock external dependencies
- **Test utilities**: Shared helpers in tests/utils/

### 5. React Best Practices
- **Functional components**: Use hooks instead of class components
- **Custom hooks**: Extract reusable stateful logic
- **Context API**: Avoid prop drilling
- **Memoization**: React.memo, useMemo, useCallback for performance
- **Error boundaries**: Catch rendering errors
- **Suspense**: Handle async loading states

### 6. Node.js API Patterns
- **Express middleware**: Request validation, error handling
- **Async route handlers**: Always use async/await
- **Error middleware**: Centralized error handling
- **Dependency injection**: Testable service architecture
- **Environment configuration**: dotenv for secrets
- **Database connection pooling**: Efficient resource management

### 7. Documentation Standards
- **JSDoc for complex functions**: Parameters, returns, throws, examples
- **Simple functions**: One-line description sufficient
- **README.md structure**: Installation, usage, development, scripts
- **CHANGELOG.md**: Follow Keep a Changelog format
- **DEVLOG.md**: Single source of truth for development history

### 8. Development Workflow
- **Task breakdown** for projects >30 minutes
- **Iterative testing protocol**: Create temp tests, iterate until pass, cleanup
- **Quality gates** before delivery: tests pass, linting clean, types valid
- **Version control** best practices: semantic versioning, meaningful commits

## Framework-Specific Configurations

### Express.js Backend

**Typical Structure**:
```
src/
├── index.ts              # Server entry point
├── app.ts                # Express app configuration
├── controllers/          # Request handlers
├── services/             # Business logic
├── models/               # Database models
├── middleware/           # Custom middleware
├── routes/               # Route definitions
├── utils/                # Helper functions
└── types/                # TypeScript types
```

**Key Patterns**:
- Async error handling wrapper
- Validation middleware (Joi, Zod)
- Authentication middleware (JWT)
- Request logging (Morgan, Winston)
- Rate limiting (express-rate-limit)

### React Frontend

**Typical Structure**:
```
src/
├── index.tsx             # App entry point
├── App.tsx               # Root component
├── components/           # Reusable components
│   ├── common/           # Buttons, inputs, cards
│   └── [feature]/        # Feature-specific components
├── pages/                # Page-level components
├── hooks/                # Custom React hooks
├── context/              # React context providers
├── services/             # API service functions
├── utils/                # Helper functions
├── types/                # TypeScript interfaces
└── styles/               # Global styles
```

**Key Patterns**:
- Component composition over inheritance
- Custom hooks for shared logic
- Context for global state
- Service layer for API calls
- React Query for server state

### Next.js Full-Stack

**Typical Structure**:
```
app/                      # App Router (Next.js 13+)
├── (auth)/               # Route groups
├── api/                  # API routes
├── [slug]/               # Dynamic routes
├── layout.tsx            # Root layout
└── page.tsx              # Home page

src/
├── components/           # Shared components
├── lib/                  # Utilities and config
└── types/                # TypeScript types

public/                   # Static assets
```

**Key Patterns**:
- Server Components by default
- Client Components with 'use client'
- API routes for backend logic
- Server Actions for mutations
- Metadata API for SEO

### NestJS Backend

**Typical Structure**:
```
src/
├── main.ts               # Application entry
├── app.module.ts         # Root module
├── [feature]/            # Feature modules
│   ├── [feature].module.ts
│   ├── [feature].controller.ts
│   ├── [feature].service.ts
│   ├── [feature].entity.ts
│   └── dto/              # Data Transfer Objects
├── common/               # Shared code
│   ├── guards/
│   ├── interceptors/
│   ├── decorators/
│   └── filters/
└── config/               # Configuration
```

**Key Patterns**:
- Dependency injection
- Module-based architecture
- Guards for authentication
- Interceptors for transformation
- Pipes for validation

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session.

**Check**:
```bash
ls -la CLAUDE.md
# Should show file exists in project root
```

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version.

**Action**:
```bash
cp path/to/CLAUDE_condensed_20k.md ./CLAUDE.md
```

### Issue: Standards Not Being Followed
**Solution**: Explicitly reference the standard in your request:
```
"Following the import organization standard in CLAUDE.md, organize the imports in this file"
```

### Issue: ESLint Conflicts with Prettier
**Solution**: Install and configure eslint-config-prettier:
```bash
npm install -D eslint-config-prettier
```

Add to .eslintrc.js extends:
```javascript
extends: [
  'eslint:recommended',
  'plugin:@typescript-eslint/recommended',
  'prettier', // Must be last
],
```

### Issue: TypeScript Compilation Errors
**Solution**: Check tsconfig.json includes and excludes:
```json
{
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

### Issue: Jest Not Finding TypeScript Files
**Solution**: Ensure ts-jest preset is configured:
```javascript
module.exports = {
  preset: 'ts-jest',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

### Issue: Need Different Standards for Subproject
**Solution**: Create a project-specific CLAUDE.md in the subproject directory with overrides.

## Testing Strategies

### Unit Tests
Test individual functions and methods in isolation:

```typescript
describe('formatUserData', () => {
  it('should format user name correctly', () => {
    const input = { firstName: 'john', lastName: 'doe' };
    const result = formatUserData(input);
    expect(result.fullName).toBe('John Doe');
  });

  it('should handle missing fields gracefully', () => {
    const input = { firstName: 'john' };
    const result = formatUserData(input);
    expect(result.fullName).toBe('John');
  });
});
```

### Integration Tests
Test how components work together:

```typescript
describe('UserService', () => {
  let service: UserService;
  let mockDatabase: jest.Mocked<Database>;

  beforeEach(() => {
    mockDatabase = createMockDatabase();
    service = new UserService(mockDatabase);
  });

  it('should create user and send welcome email', async () => {
    const userData = { email: 'test@example.com', name: 'Test' };
    await service.createUser(userData);

    expect(mockDatabase.insert).toHaveBeenCalledWith('users', userData);
    expect(emailService.send).toHaveBeenCalledWith('welcome', userData.email);
  });
});
```

### E2E Tests
Test complete user workflows:

```typescript
describe('User Registration Flow', () => {
  it('should register new user and redirect to dashboard', async () => {
    const response = await request(app)
      .post('/api/users/register')
      .send({ email: 'test@example.com', password: 'secure123' })
      .expect(201);

    expect(response.body).toHaveProperty('userId');
    expect(response.body).toHaveProperty('token');

    const dashboardResponse = await request(app)
      .get('/api/dashboard')
      .set('Authorization', `Bearer ${response.body.token}`)
      .expect(200);

    expect(dashboardResponse.body).toHaveProperty('userName');
  });
});
```

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with JavaScript/TypeScript system prompt (CLAUDE.md in project root)
- [ ] Verified configuration by testing function generation with TypeScript
- [ ] Confirmed project structure knowledge for Node.js/React
- [ ] Validated testing framework understanding (Jest configuration)
- [ ] ESLint and Prettier configured and working
- [ ] TypeScript compiler (tsconfig.json) configured with strict mode
- [ ] Jest testing framework set up with coverage thresholds
- [ ] NPM scripts configured for build, test, lint, format
- [ ] Documentation files created (README, CHANGELOG, DEVLOG)
- [ ] .gitignore configured with appropriate exclusions
- [ ] Optionally customized for organization-specific needs
- [ ] Committed CLAUDE.md to version control for team consistency

## NPM Scripts Reference

Standard scripts to include in package.json:

```json
{
  "scripts": {
    "dev": "ts-node-dev --respawn src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.{ts,tsx}",
    "lint:fix": "eslint src/**/*.{ts,tsx} --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json}\"",
    "type-check": "tsc --noEmit",
    "clean": "rm -rf dist",
    "prebuild": "npm run clean",
    "pretest": "npm run lint",
    "prepare": "husky install"
  }
}
```

## Related Skills

- `generate-jsdoc-comments`: Use after setup to document existing JavaScript/TypeScript code
- `setup-test-infrastructure`: Establish Jest testing framework following system prompt standards
- `code-review-quality`: Review JavaScript/TypeScript code quality against configured standards
- `cleanup-javascript`: Clean up JavaScript/TypeScript code following configured standards
- `refactor-to-typescript`: Convert JavaScript projects to TypeScript with proper types
- `optimize-react-performance`: Apply React performance best practices from system prompt

## Additional Resources

### Official Documentation
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [ESLint Configuration](https://eslint.org/docs/latest/use/configure/)
- [Prettier Options](https://prettier.io/docs/en/options.html)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

### Style Guides
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)

### Testing Resources
- [Jest Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)
- [Testing React Applications](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [E2E Testing with Playwright](https://playwright.dev/)

### Framework-Specific
- [Express Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)
- [React Documentation](https://react.dev/)
- [Next.js Documentation](https://nextjs.org/docs)
- [NestJS Documentation](https://docs.nestjs.com/)

### Performance and Security
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Web Security Checklist](https://github.com/virajkulkarni14/WebDeveloperSecurityChecklist)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**Template Source**: agent_prompts/autonomous_agents/claude_code/javascript/
