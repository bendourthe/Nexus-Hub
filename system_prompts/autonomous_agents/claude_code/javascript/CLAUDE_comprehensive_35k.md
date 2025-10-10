# CLAUDE.md - JavaScript/TypeScript Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for JavaScript/TypeScript development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9
- **New Feature**: Sections 1-5, 7
- **Refactoring**: Sections 3, 6, 9
- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a function**: Focus sections 3, 9
- **New project**: Use sections 2, 4, 5
- **Code review**: Apply sections 3, 10

## Context-Aware Behavior
- **For small scripts**: Minimal structure
- **For libraries**: Full architecture
- **For debugging**: Focus on problem-solving

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation
- Minimal testing setup
- Focus on core functionality

### Full Mode (for new projects)
- Complete architecture
- Comprehensive testing
- Full documentation

## Claude Code Terminal Commands
- **Run tests**: `claude run npm test`
- **Format code**: `claude format src/`
- **Check style**: `claude lint src/`
- **New project**: `claude init [project-name]`
- **Install deps**: `claude install`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and coding concepts
- Enable learning through understanding, not copy-paste
- Reference documentation for non-obvious concepts

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently
- Compare alternatives and recommend best solution
- Clearly explain reasoning and trade-offs

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete functions
- **Refactoring**: Consolidate duplicate logic

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance
- If already optimal, confirm briefly with reasoning


# 2. Project Architecture
---

## Standard Node.js Application Structure

```
project_name/
├── node_modules/                  # Dependencies
├── src/                           # Main application source
│   ├── index.ts                   # Entry point
│   ├── app.ts                     # Application setup
│   ├── core/                      # Core logic
│   │   ├── controllers/           # Route controllers
│   │   ├── services/              # Business logic
│   │   ├── models/                # Data models
│   │   ├── middleware/            # Express middleware
│   │   └── utils/                 # Utilities
│   └── types/                     # TypeScript type definitions
├── tests/                         # Testing suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── e2e/                       # End-to-end tests
│   └── setup.ts                   # Test configuration
├── dist/                          # Compiled output
├── docs/                          # Documentation
├── scripts/                       # Build/deploy scripts
├── CHANGELOG.md                   # Version history
├── README.md                      # Project documentation
├── DEVLOG.md                      # Development log
├── package.json                   # Dependencies and scripts
├── tsconfig.json                  # TypeScript config
├── .eslintrc.js                   # ESLint config
├── .prettierrc                    # Prettier config
├── jest.config.js                 # Jest config
└── .gitignore                     # Git ignore rules
```

## React Application Structure

```
project_name/
├── node_modules/
├── public/                        # Static assets
│   ├── index.html
│   └── assets/
├── src/
│   ├── index.tsx                  # Entry point
│   ├── App.tsx                    # Root component
│   ├── components/                # Reusable components
│   │   ├── common/                # Shared components
│   │   └── [feature]/             # Feature-specific
│   ├── pages/                     # Page components
│   ├── hooks/                     # Custom React hooks
│   ├── context/                   # React context
│   ├── services/                  # API services
│   ├── utils/                     # Utility functions
│   ├── types/                     # TypeScript types
│   ├── styles/                    # Global styles
│   └── assets/                    # Images, fonts
├── tests/
│   ├── unit/
│   ├── integration/
│   └── __mocks__/
├── CHANGELOG.md
├── README.md
├── DEVLOG.md
├── package.json
├── tsconfig.json
├── .eslintrc.js
└── .gitignore
```

## Project Initialization Sequence

1. **Initialize project**: `npm init` or `yarn init`
2. **Install TypeScript**: `npm install -D typescript @types/node`
3. **Create tsconfig.json**: `npx tsc --init`
4. **Install dev tools**: `npm install -D eslint prettier jest @types/jest`
5. **Create directory structure** as outlined above
6. **Create `.gitignore`** with node_modules, dist, .env, etc.
7. **Create `package.json`** scripts for build, test, lint
8. **Create `CHANGELOG.md`** starting with version 0.1.0
9. **Create `README.md`** with setup and usage
10. **Create `DEVLOG.md`** with initial task list

## package.json Template
```json
{
  "name": "[project-name]",
  "version": "[version-from-changelog]",
  "description": "[project description]",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "ts-node-dev --respawn src/index.ts",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx}\"",
    "type-check": "tsc --noEmit"
  },
  "keywords": [],
  "author": "Benjamin Dourthe <benjamin@adonamed.com>",
  "license": "MIT",
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/jest": "^29.5.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.50.0",
    "jest": "^29.7.0",
    "prettier": "^3.0.0",
    "ts-jest": "^29.1.0",
    "ts-node-dev": "^2.0.0",
    "typescript": "^5.2.0"
  },
  "dependencies": {}
}
```

## tsconfig.json Template
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```


# 3. Code Standards
---

## TypeScript/JavaScript Style Guidelines

### Import Organization
**Always place imports at the top of files in this exact order:**

1. **Node.js built-in modules** (alphabetically sorted)
2. **Third-party library imports** (grouped by functionality)
3. **Local application imports** (alphabetically sorted)
4. **Type imports** (separate from value imports when possible)

**Example:**
```typescript
// Node.js built-ins
import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

// Web framework
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';

// Database
import mongoose from 'mongoose';
import { QueryOptions } from 'mongoose';

// Utilities
import lodash from 'lodash';
import dayjs from 'dayjs';

// Local imports
import { DatabaseManager } from './core/database';
import { DataProcessor } from './core/processors';
import { formatResponse, validateInput } from './core/utils';

// Type imports
import type { UserData, ProcessResult } from './types';
```

**Rules:**
- Each section separated by blank line
- Alphabetized within each section
- Use named imports when possible for tree-shaking
- Prefer ES6 imports over require()
- Group third-party imports by functionality with comment headers

### Line Length and Formatting

**General Rules:**
- **Standard limit**: 100 characters (Prettier standard)
- **Acceptable exceptions**:
  - Long URLs or file paths
  - Import statements with many items
  - Complex string literals
  - Function signatures with many parameters (use multi-line format)

**Multi-line Formatting:**
```typescript
// Function signatures with many parameters
function complexFunction(
  parameterOne: string,
  parameterTwo: number,
  parameterThree: Record<string, unknown> | null = null,
  parameterFour: string[] | null = null,
  parameterFive: boolean = false,
): Promise<string[]> {
  // Implementation
}

// Long strings
const errorMessage =
  'This is a very long error message that needs to be split ' +
  'across multiple lines for better readability and to comply ' +
  'with the 100 character line length limit.';

// Complex conditionals
if (
  conditionOne &&
  conditionTwo &&
  (conditionThree || conditionFour) &&
  !conditionFive
) {
  processComplexLogic();
}

// Object/Array destructuring
const {
  propertyOne,
  propertyTwo,
  propertyThree,
  propertyFour,
} = complexObject;
```

### Code Layout Rules

**Function and Class Structure:**
- **No unnecessary empty lines** inside function/method bodies
- **One blank line** between function/method definitions
- **Two blank lines** between class definitions
- **Group related statements** closely together

**Example:**
```typescript
class DataProcessor {
  private cache: Map<string, unknown>;
  private validator: SchemaValidator;

  constructor(config: ProcessorConfig) {
    this.cache = new Map();
    this.validator = new SchemaValidator(config.schema);
  }

  async processData(data: DataRecord[]): Promise<ProcessedData[]> {
    const cleaned = this.removeNulls(data);
    const normalized = this.normalizeValues(cleaned);
    const validated = await this.validateRecords(normalized);
    return validated;
  }

  private removeNulls(records: DataRecord[]): DataRecord[] {
    return records.filter((record) => record !== null);
  }

  private normalizeValues(records: DataRecord[]): DataRecord[] {
    return records.map((record) => ({
      ...record,
      value: parseFloat(record.value || '0'),
      score: Math.min(Math.max(record.score || 0, 0), 100),
    }));
  }
}


class ValidationError extends Error {
  constructor(
    message: string,
    public errors: string[],
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}
```

### Comment Guidelines

**Placement and Style:**
- **Above code blocks**: Comments explain why, not just what
- **No inline comments**: Avoid same-line comments unless extremely clear
- **JSDoc for functions**: Document public APIs
- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Examples:**
```typescript
// Use binary search for O(log n) performance on sorted data
// This is critical for large datasets (>10k items)
const result = binarySearch(sortedList, target);

// Cache results to avoid expensive API calls during batch processing
// API rate limit is 100 calls/minute, caching prevents exceeding it
if (!this.cache.has(key)) {
  this.cache.set(key, await expensiveApiCall(key));
}

// Implement exponential backoff for rate-limited APIs
// Start with 1 second, double each retry up to 32 seconds max
for (let attempt = 0; attempt < maxRetries; attempt++) {
  const waitTime = Math.min(2 ** attempt, 32);
  await sleep(waitTime * 1000);
}
```

### Function Design Patterns

**Naming Conventions:**
- **Functions/Methods**: `camelCase` with descriptive verbs
- **Private methods**: Prefix with `_` or use TypeScript private
- **Constants**: `UPPER_SNAKE_CASE`
- **Classes**: `PascalCase`
- **Interfaces/Types**: `PascalCase` with descriptive names
- **Boolean variables**: Prefix with `is`, `has`, `should`

**Structure Guidelines:**
- **Single responsibility**: Each function does one thing well
- **Predictable interfaces**: Consistent parameter patterns
- **Type annotations**: Use TypeScript types extensively
- **Error handling**: Explicit try-catch or Promise rejection
- **Return early**: Use guard clauses for validation
- **Async/await**: Prefer over raw Promises for readability

**Examples:**
```typescript
// Good function design
async function fetchUserData(
  userId: string,
  options?: FetchOptions,
): Promise<UserData> {
  // Guard clauses
  if (!userId) {
    throw new Error('User ID is required');
  }

  // Early return for cache
  if (options?.useCache) {
    const cached = cache.get(userId);
    if (cached) return cached;
  }

  // Main logic
  try {
    const response = await api.get(`/users/${userId}`);
    const userData = validateUserData(response.data);

    if (options?.useCache) {
      cache.set(userId, userData);
    }

    return userData;
  } catch (error) {
    throw new Error(`Failed to fetch user ${userId}: ${error.message}`);
  }
}
```


# 4. Documentation Standards
---

## JSDoc Templates

### Complex Functions
```typescript
/**
 * Process and validate user records according to specified rules.
 *
 * Performs data cleaning, validation against business rules, and formatting
 * for downstream processing. Supports both synchronous and asynchronous validation.
 *
 * @param data - Input data records to process
 * @param rules - Validation rules to apply
 * @param options - Optional processing configuration
 * @returns Processed and validated records
 * @throws {ValidationError} When data fails validation
 * @throws {ProcessingError} When processing fails
 *
 * @example
 * ```typescript
 * const result = await processUserData(
 *   rawData,
 *   validationRules,
 *   { strict: true }
 * );
 * ```
 *
 * @author Benjamin Dourthe <benjamin@adonamed.com>
 */
async function processUserData(
  data: DataRecord[],
  rules: ValidationRules,
  options?: ProcessOptions,
): Promise<ProcessedRecord[]> {
  // Implementation
}
```

### Simple Functions
```typescript
/**
 * Calculate total including tax.
 */
function calculateTotal(items: number[]): number {
  return items.reduce((sum, item) => sum + item, 0) * 1.1;
}
```

### React Components
```typescript
/**
 * User profile card component.
 *
 * Displays user information with avatar, name, and bio.
 * Supports loading and error states.
 *
 * @component
 * @example
 * ```tsx
 * <UserCard
 *   user={userData}
 *   onEdit={handleEdit}
 *   loading={isLoading}
 * />
 * ```
 */
interface UserCardProps {
  user: User;
  onEdit?: (user: User) => void;
  loading?: boolean;
}

export const UserCard: React.FC<UserCardProps> = ({ user, onEdit, loading }) => {
  // Implementation
};
```

## README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Installation

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm 9+ or yarn 1.22+
- [Other requirements]

### Setup
    ```bash
    git clone <REPO_URL>
    cd [project-name]
    npm install
    npm run build
    ```

**Note**: Your repository URL is stored in `.git/config`. To retrieve it:

```bash
git config --get remote.origin.url
```

## Usage
    ```typescript
    import { MainModule } from './src/core';

    const result = await MainModule.process("input");
    console.log(result);
    ```

## Development
    ```bash
    npm run dev        # Start development server
    npm test           # Run tests
    npm run lint       # Check code style
    npm run format     # Format code
    ```

## Testing
    ```bash
    npm test              # Run all tests
    npm run test:watch    # Watch mode
    npm run test:coverage # With coverage
    ```

## Scripts
- `npm run build` - Compile TypeScript
- `npm run dev` - Development mode with hot reload
- `npm start` - Run production build
- `npm test` - Run Jest tests
- `npm run lint` - ESLint check
- `npm run format` - Prettier format
```

## CHANGELOG.md Structure
```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements

### Fixed
- Bug fixes

### Removed
- Deprecated items
```

## DEVLOG.md Structure
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Urgent tasks

### Medium Priority
- [ ] Important enhancements

### Low Priority
- [ ] Future features

## Development History

### Project Architecture
- **Initial Design**: [Decisions]
- **Tech Stack**: [Choices]
- **Patterns**: [Applied]

### Implementation Challenges
- **Challenge X**: [Problem]
  - *Solution*: [Resolution]
  - *Trade-offs*: [Considerations]

### Technical Decisions
[Key decisions and rationale]

## Troubleshooting History
### Issue X: [Description]
- **Symptoms**: [Observed]
- **Root Cause**: [Problem]
- **Resolution**: [Fix]
```


# 5. Testing Framework
---

## Test Structure

1. **Jest configuration**: Comprehensive test setup
2. **Unit tests**: Individual function/component tests
3. **Integration tests**: API and service tests
4. **E2E tests**: Full application flow tests

## Jest Configuration (jest.config.js)
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
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

## Test Implementation Template

```typescript
/**
 * Test suite for [feature/module].
 *
 * Comprehensive tests covering normal operations, edge cases, and error conditions.
 *
 * @author Benjamin Dourthe <benjamin@adonamed.com>
 */
import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { DataProcessor } from '@/core/processors';
import type { DataRecord, ProcessOptions } from '@/types';

describe('DataProcessor', () => {
  let processor: DataProcessor;
  let mockData: DataRecord[];

  beforeEach(() => {
    processor = new DataProcessor({
      strict: true,
      cacheEnabled: true,
    });

    mockData = [
      { id: '1', value: '100', score: 85 },
      { id: '2', value: '200', score: 92 },
    ];
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('processData', () => {
    it('should successfully process valid data', async () => {
      const result = await processor.processData(mockData);

      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('id', '1');
      expect(result[0]).toHaveProperty('value', 100);
    });

    it('should filter out null records', async () => {
      const dataWithNulls = [...mockData, null as unknown as DataRecord];
      const result = await processor.processData(dataWithNulls);

      expect(result).toHaveLength(2);
    });

    it('should normalize score values to 0-100 range', async () => {
      const dataWithExtremeScores = [
        { id: '1', value: '100', score: 150 },
        { id: '2', value: '200', score: -10 },
      ];
      const result = await processor.processData(dataWithExtremeScores);

      expect(result[0].score).toBe(100);
      expect(result[1].score).toBe(0);
    });

    it('should throw ValidationError for invalid data', async () => {
      const invalidData = [{ id: '', value: 'invalid', score: 'bad' }];

      await expect(
        processor.processData(invalidData as unknown as DataRecord[])
      ).rejects.toThrow('ValidationError');
    });

    it('should use cache when enabled', async () => {
      const spy = jest.spyOn(processor as any, 'validateRecords');

      await processor.processData(mockData);
      await processor.processData(mockData);

      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  describe('error handling', () => {
    it('should handle empty input gracefully', async () => {
      const result = await processor.processData([]);
      expect(result).toEqual([]);
    });

    it('should provide detailed error messages', async () => {
      const invalidData = [{ id: null, value: null, score: null }];

      try {
        await processor.processData(invalidData as unknown as DataRecord[]);
      } catch (error) {
        expect(error).toBeInstanceOf(Error);
        expect(error.message).toContain('id');
      }
    });
  });
});
```

## React Component Testing
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserCard } from '@/components/UserCard';

describe('UserCard Component', () => {
  const mockUser = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    bio: 'Test bio',
  };

  it('should render user information', () => {
    render(<UserCard user={mockUser} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('should call onEdit when edit button clicked', async () => {
    const handleEdit = jest.fn();
    render(<UserCard user={mockUser} onEdit={handleEdit} />);

    const editButton = screen.getByRole('button', { name: /edit/i });
    await userEvent.click(editButton);

    expect(handleEdit).toHaveBeenCalledWith(mockUser);
  });

  it('should show loading state', () => {
    render(<UserCard user={mockUser} loading />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```


# 6. Development Workflow
---

## Task Breakdown Methodology

### When to Use Task Breakdown
**Apply systematic breakdown for:**
- Projects estimated >30 minutes
- Multi-component applications
- Complex feature implementations
- Integration tasks with dependencies
- Refactoring projects

### Task Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope]

### Prerequisites
- Node.js 18+ installed
- Project dependencies installed
- [Other requirements]

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Outputs]
**Time**: [15-45 min]
**Dependencies**: [Previous tasks]

**Prompt**:
    ```
    [Step-by-step instructions]
    [Expected structure]
    [Standards to follow]
    [Success criteria]

    Complete and pause. Confirm before proceeding.
    ```
```

### Quality Gates
- [ ] Functionality verified
- [ ] Type safety confirmed
- [ ] Tests passing
- [ ] Linting clean
- [ ] Code formatted
- [ ] Documentation complete
- [ ] Performance acceptable
- [ ] Security checked


# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Example:
```
Please run in your terminal:

1. Install dependencies:
   npm install

2. Run tests:
   npm test

3. Share any errors for assistance.
```

## npm/yarn Commands

```bash
# Setup
npm init -y
npm install

# Development
npm run dev
npm run build
npm start

# Testing
npm test
npm run test:watch
npm run test:coverage

# Code Quality
npm run lint
npm run lint:fix
npm run format
npm run type-check

# Dependencies
npm install [package]
npm install -D [dev-package]
npm update
npm audit fix
```

## TypeScript Commands

```bash
# Compile
npx tsc

# Watch mode
npx tsc --watch

# Type checking only
npx tsc --noEmit

# Generate declarations
npx tsc --declaration
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update package.json version
- Change README.md versions
- Create tags/releases

### Version Protocol

1. **Assess**: "Changes might warrant version update from X.Y.Z"
2. **Request**: "Should I update to [version]? Or handle manually?"
3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs
- **Minor (Y+1.0)**: New features, backwards compatible
- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Never suggest:
- `git add/commit/push`
- `git branch/merge/rebase`
- `git tag` or releases
- `git init`

### DEVLOG.md Updates
Safe to update without permission:
- Task lists
- Development history
- Challenges/solutions
- Technical decisions

Never include:
- Commit hashes
- Git workflow assumptions
- Version control strategies


# 9. Implementation Examples
---

## Code Fix Request

**Structure:**
1. Analyze issue
2. Implement fix
3. Explain improvements
4. Provide integration steps

## Project Planning

**Structure:**
1. Break down components
2. Recommend architecture
3. Create subtask breakdown
4. Provide implementation guidance

## Decision Trees

### Module System
```
ES Modules (import/export)? → Prefer for new projects
CommonJS (require)? → Legacy compatibility
Mixed? → Configure tsconfig appropriately
```

### Error Handling
```
Async operation? → try/catch with async/await
  API call? → Handle network errors
  Database? → Handle connection errors
  Multiple? → Promise.allSettled
Sync operation? → try/catch
  Critical? → Throw error
  Recoverable? → Return error object
```


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] Solves problem completely
- [ ] TypeScript types defined
- [ ] Follows style guidelines
- [ ] JSDoc documentation
- [ ] Error handling present
- [ ] Tests included/suggested
- [ ] No console.logs (use logger)
- [ ] Performance considered
- [ ] Security checked
- [ ] Educational value

## Before Delivering Project
- [ ] Standard architecture
- [ ] All config files present
- [ ] Version consistency
- [ ] Documentation complete
- [ ] Scripts configured
- [ ] Testing framework setup
- [ ] Linting configured
- [ ] Git integration
- [ ] Dependencies documented

---
