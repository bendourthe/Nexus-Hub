---
name: init-javascript-project
description: Initialize complete JavaScript/TypeScript project with Node.js backend, React frontend, or Next.js full-stack configuration
version: 1.0.0
author: Benjamin Dourthe
language: JavaScript/TypeScript
category: Project Initialization
tags: [javascript, typescript, nodejs, react, nextjs, initialization, setup, project-structure]
priority: MEDIUM
template_source: agent_prompts/autonomous_agents/claude_code/javascript/
---

# Initialize JavaScript Project

Create a complete, production-ready JavaScript/TypeScript project with standard structure, configuration files, testing framework, and documentation in minutes. Supports Node.js backend, React frontend, and Next.js full-stack applications.

## When to Use This Skill

Use this skill when you need to:
- ✅ Start a new JavaScript/TypeScript project from scratch
- ✅ Set up Node.js backend with Express
- ✅ Initialize React frontend application
- ✅ Create Next.js full-stack application
- ✅ Establish standard project structure quickly
- ✅ Configure TypeScript, ESLint, and Prettier
- ✅ Set up testing framework (Jest)
- ✅ Create documentation templates (README, CHANGELOG, DEVLOG)
- ✅ Initialize CI/CD with GitHub Actions

## What This Skill Does

Creates a complete JavaScript/TypeScript project structure following industry best practices:

### 1. Directory Structure

#### Node.js Backend (Express)
```
project_name/
├── node_modules/           # Dependencies
├── src/
│   ├── index.ts           # Entry point
│   ├── app.ts             # Express app configuration
│   ├── server.ts          # Server initialization
│   ├── controllers/       # Request handlers
│   ├── models/            # Data models
│   ├── routes/            # API routes
│   ├── middleware/        # Custom middleware
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   ├── config/            # Configuration
│   └── types/             # TypeScript types
├── tests/                  # Test suite
│   ├── integration/
│   ├── unit/
│   └── setup.ts
├── dist/                   # Compiled output
├── .github/                # GitHub workflows
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .eslintrc.json
├── .prettierrc
├── tsconfig.json
├── jest.config.js
├── package.json
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

#### React Frontend
```
project_name/
├── node_modules/
├── public/                 # Static assets
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── index.tsx          # Entry point
│   ├── App.tsx            # Root component
│   ├── components/        # React components
│   │   ├── common/
│   │   └── features/
│   ├── hooks/             # Custom hooks
│   ├── pages/             # Page components
│   ├── services/          # API services
│   ├── store/             # State management
│   ├── styles/            # CSS/SCSS files
│   ├── types/             # TypeScript types
│   ├── utils/             # Utilities
│   └── config/            # Configuration
├── tests/
│   ├── components/
│   ├── integration/
│   └── setup.ts
├── build/                  # Production build
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .eslintrc.json
├── .prettierrc
├── tsconfig.json
├── jest.config.js
├── package.json
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

#### Next.js Full-Stack
```
project_name/
├── node_modules/
├── public/                 # Static assets
├── src/
│   ├── app/               # App router (Next.js 13+)
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── api/           # API routes
│   │   └── [features]/
│   ├── components/        # React components
│   ├── hooks/             # Custom hooks
│   ├── lib/               # Utilities and helpers
│   ├── services/          # Business logic
│   ├── styles/            # Global styles
│   └── types/             # TypeScript types
├── tests/
│   ├── components/
│   ├── integration/
│   └── setup.ts
├── .next/                  # Build output
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── .eslintrc.json
├── .prettierrc
├── tsconfig.json
├── jest.config.js
├── next.config.js
├── package.json
├── CHANGELOG.md
├── DEVLOG.md
├── README.md
└── CLAUDE.md
```

### 2. Configuration Files
- **package.json**: Dependencies, scripts, and project metadata
- **tsconfig.json**: TypeScript compiler configuration
- **.eslintrc.json**: ESLint code quality rules
- **.prettierrc**: Code formatting configuration
- **jest.config.js**: Testing framework configuration
- **.gitignore**: Comprehensive ignore patterns

### 3. Documentation
- **README.md**: Installation, usage, and feature documentation
- **CHANGELOG.md**: Version history following Keep a Changelog format
- **DEVLOG.md**: Development task list and decision log
- **CLAUDE.md**: Claude Code project guidelines

### 4. Testing Framework
- Jest for unit and integration testing
- React Testing Library for component tests
- Supertest for API endpoint tests (backend)
- Code coverage reporting

### 5. Development Tools
- TypeScript for type safety
- ESLint for code linting
- Prettier for code formatting
- Nodemon for development server (backend)
- Hot module replacement (frontend)

## Prerequisites

- Node.js 18+ installed
- npm, yarn, or pnpm (package manager)
- git (version control)
- (Optional) Claude Code for AI assistance

## Instructions

### Step 1: Define Project Requirements

Gather this information before initialization:

**Project Details**:
- **Name**: Project identifier (kebab-case recommended)
- **Description**: One-line summary of purpose
- **Type**: Node.js Backend / React Frontend / Next.js Full-Stack
- **Author**: Your name and email
- **Package Manager**: npm / yarn / pnpm

**Dependencies**:
- Core dependencies (e.g., express, react, next)
- Development dependencies (testing, linting)

**Features**:
- Key capabilities to document
- Initial version number (default: 0.1.0)

### Step 2: Invoke the Skill

#### Example: Node.js Backend
```
"Use the init-javascript-project skill to create a new Node.js backend project.

Project Details:
- Name: my-awesome-api
- Description: RESTful API for task management
- Type: Node.js Backend (Express)
- Author: Your Name (your.email@example.com)
- Package Manager: npm

Dependencies:
- express (web framework)
- cors (CORS middleware)
- dotenv (environment variables)
- joi (validation)

Features:
- User authentication
- Task CRUD operations
- Task categorization
- RESTful API design

Please initialize the complete project structure with TypeScript."
```

#### Example: React Frontend
```
"Use the init-javascript-project skill to create a new React frontend project.

Project Details:
- Name: task-manager-ui
- Description: Modern task management interface
- Type: React Frontend
- Author: Your Name (your.email@example.com)
- Package Manager: yarn

Dependencies:
- react-router-dom (routing)
- axios (HTTP client)
- @tanstack/react-query (data fetching)
- tailwindcss (styling)

Features:
- Task dashboard
- User authentication
- Real-time updates
- Responsive design

Please initialize the complete project structure with TypeScript."
```

#### Example: Next.js Full-Stack
```
"Use the init-javascript-project skill to create a new Next.js full-stack project.

Project Details:
- Name: fullstack-app
- Description: Full-stack task management application
- Type: Next.js Full-Stack
- Author: Your Name (your.email@example.com)
- Package Manager: pnpm

Dependencies:
- prisma (ORM)
- next-auth (authentication)
- zod (validation)
- tailwindcss (styling)

Features:
- Server-side rendering
- API routes
- Database integration
- Authentication system

Please initialize the complete project structure with TypeScript and App Router."
```

### Step 3: Review Generated Structure

The skill will create all files and directories. Verify:

```bash
# Check structure
tree my-awesome-api/

# Navigate to project
cd my-awesome-api

# Verify package.json
cat package.json
```

### Step 4: Install Dependencies

```bash
# Using npm
npm install

# Using yarn
yarn install

# Using pnpm
pnpm install

# Verify installation
npm list --depth=0
```

### Step 5: Set Up Environment

Create `.env` file for environment variables:

#### Backend
```env
# Server Configuration
PORT=3000
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Authentication
JWT_SECRET=your-secret-key-here
JWT_EXPIRES_IN=7d

# CORS
CORS_ORIGIN=http://localhost:3001
```

#### Frontend
```env
# API Configuration
REACT_APP_API_URL=http://localhost:3000
REACT_APP_API_TIMEOUT=10000

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
```

#### Next.js
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# API Keys
NEXT_PUBLIC_API_KEY=your-public-key
```

### Step 6: Verify Setup

Run development server and tests:

```bash
# Development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

### Step 7: Initialize Git Repository

```bash
# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial project structure

- Standard JavaScript/TypeScript project layout
- Testing framework configured
- Development tools configured
- Documentation templates created

Generated with init-javascript-project skill"

# (Optional) Add remote and push
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 8: Start Development

Your project is now ready! Begin developing:

```bash
# Start development server with watch mode
npm run dev

# Run tests in watch mode
npm run test:watch

# Build for production
npm run build

# Start production server (after build)
npm start
```

## Generated File Contents

### package.json (Node.js Backend)
```json
{
  "name": "my-awesome-api",
  "version": "0.1.0",
  "description": "RESTful API for task management",
  "main": "dist/index.js",
  "scripts": {
    "dev": "nodemon src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src tests --ext .ts",
    "lint:fix": "eslint src tests --ext .ts --fix",
    "format": "prettier --write \"src/**/*.ts\" \"tests/**/*.ts\"",
    "type-check": "tsc --noEmit"
  },
  "keywords": ["api", "express", "typescript", "rest"],
  "author": "Your Name <your.email@example.com>",
  "license": "MIT",
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "joi": "^17.10.0",
    "helmet": "^7.0.0",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.18",
    "@types/cors": "^2.8.14",
    "@types/node": "^20.8.0",
    "@types/jest": "^29.5.5",
    "@types/supertest": "^2.0.13",
    "@typescript-eslint/eslint-plugin": "^6.7.5",
    "@typescript-eslint/parser": "^6.7.5",
    "eslint": "^8.51.0",
    "jest": "^29.7.0",
    "nodemon": "^3.0.1",
    "prettier": "^3.0.3",
    "supertest": "^6.3.3",
    "ts-jest": "^29.1.1",
    "ts-node": "^10.9.1",
    "typescript": "^5.2.2"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

### package.json (React Frontend)
```json
{
  "name": "task-manager-ui",
  "version": "0.1.0",
  "description": "Modern task management interface",
  "private": true,
  "scripts": {
    "dev": "react-scripts start",
    "build": "react-scripts build",
    "start": "serve -s build",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src --ext .ts,.tsx",
    "lint:fix": "eslint src --ext .ts,.tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit",
    "eject": "react-scripts eject"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "axios": "^1.5.1",
    "@tanstack/react-query": "^5.0.0",
    "tailwindcss": "^3.3.3"
  },
  "devDependencies": {
    "@types/react": "^18.2.24",
    "@types/react-dom": "^18.2.8",
    "@types/node": "^20.8.0",
    "@types/jest": "^29.5.5",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.3",
    "@testing-library/user-event": "^14.5.1",
    "react-scripts": "5.0.1",
    "typescript": "^5.2.2",
    "eslint": "^8.51.0",
    "@typescript-eslint/eslint-plugin": "^6.7.5",
    "@typescript-eslint/parser": "^6.7.5",
    "prettier": "^3.0.3",
    "serve": "^14.2.1"
  },
  "browserslist": {
    "production": [">0.2%", "not dead", "not op_mini all"],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### package.json (Next.js Full-Stack)
```json
{
  "name": "fullstack-app",
  "version": "0.1.0",
  "description": "Full-stack task management application",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "next lint",
    "lint:fix": "next lint --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "prisma": "^5.4.0",
    "@prisma/client": "^5.4.0",
    "next-auth": "^4.23.1",
    "zod": "^3.22.4",
    "tailwindcss": "^3.3.3"
  },
  "devDependencies": {
    "@types/react": "^18.2.24",
    "@types/react-dom": "^18.2.8",
    "@types/node": "^20.8.0",
    "@types/jest": "^29.5.5",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.3",
    "typescript": "^5.2.2",
    "eslint": "^8.51.0",
    "eslint-config-next": "^14.0.0",
    "@typescript-eslint/eslint-plugin": "^6.7.5",
    "@typescript-eslint/parser": "^6.7.5",
    "prettier": "^3.0.3",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31"
  }
}
```

### tsconfig.json (Node.js Backend)
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
    "moduleResolution": "node",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "types": ["node", "jest"]
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

### tsconfig.json (React/Next.js)
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "jsx": "react-jsx",
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowJs": true,
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "incremental": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

### jest.config.js
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.interface.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

### .eslintrc.json
```json
{
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module",
    "ecmaFeatures": {
      "jsx": true
    }
  },
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/no-unused-vars": ["error", {
      "argsIgnorePattern": "^_"
    }],
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  },
  "env": {
    "node": true,
    "es2022": true,
    "jest": true
  }
}
```

### .prettierrc
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### .gitignore
```
# Dependencies
node_modules/
/.pnp
.pnp.js

# Testing
/coverage

# Production
/build
/dist
/.next
/out

# Environment
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Editor
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# OS
Thumbs.db

# TypeScript
*.tsbuildinfo
next-env.d.ts

# Misc
.cache
.turbo
```

### README.md (Node.js Backend)
```markdown
# My Awesome API - v0.1.0

## What's New
- Initial release
- RESTful API endpoints
- User authentication
- Task CRUD operations
- Input validation

## Overview
A RESTful API for task management built with Express and TypeScript. Provides endpoints for user authentication, task creation, and task management with comprehensive validation.

## Features
- **Authentication**: JWT-based user authentication
- **Task Management**: Create, read, update, and delete tasks
- **Validation**: Request validation with Joi
- **Security**: Helmet security headers, CORS configuration
- **Logging**: Request logging with Morgan
- **Error Handling**: Centralized error handling middleware

## Installation

### Prerequisites
- Node.js 18 or higher
- npm, yarn, or pnpm

### Setup
```bash
git clone <repository-url>
cd my-awesome-api
npm install
cp .env.example .env
# Edit .env with your configuration
npm run dev
```

## Usage

### Start Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
npm start
```

### API Endpoints
```
POST   /api/auth/register    - Register new user
POST   /api/auth/login       - Login user
GET    /api/tasks            - Get all tasks
POST   /api/tasks            - Create new task
GET    /api/tasks/:id        - Get task by ID
PUT    /api/tasks/:id        - Update task
DELETE /api/tasks/:id        - Delete task
```

## Development

### Running Tests
```bash
# All tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Code Quality
```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type check
npm run type-check
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License
MIT

## Contact
Your Name - your.email@example.com
```

### CHANGELOG.md
```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.1.0] - 2025-10-21

### Added
- Initial project structure
- Express server setup
- TypeScript configuration
- User authentication endpoints
- Task CRUD operations
- Request validation with Joi
- Security middleware (Helmet, CORS)
- Comprehensive test suite
- ESLint and Prettier configuration
- Documentation templates
```

### DEVLOG.md
```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement user authentication
- [ ] Create task CRUD endpoints
- [ ] Add input validation
- [ ] Set up database connection

### Medium Priority
- [ ] Add pagination to task list
- [ ] Implement task filtering
- [ ] Add task categories
- [ ] Create API documentation (Swagger)

### Low Priority
- [ ] Add task search functionality
- [ ] Implement task sharing
- [ ] Add email notifications
- [ ] Create admin dashboard

## Development History

### Project Architecture
- **Design**: RESTful API with Express and TypeScript
- **Tech Stack**: Node.js, Express, TypeScript, Jest
- **Pattern**: MVC architecture with service layer

### Initial Setup - 2025-10-21
- Created standard Node.js project structure
- Configured TypeScript with strict mode
- Set up testing framework (Jest)
- Configured development tools (ESLint, Prettier)
- Initialized documentation

## Troubleshooting History

(Document issues and solutions here as they arise)
```

### src/index.ts (Node.js Backend)
```typescript
/**

 * My Awesome API - Main Entry Point
 *

 * RESTful API for task management.
 *

 * @author Your Name (your.email@example.com)
 */
import dotenv from 'dotenv';
import app from './app';

// Load environment variables
dotenv.config();

const PORT = process.env.PORT || 3000;

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});
```

### src/app.ts (Node.js Backend)
```typescript
/**

 * Express Application Configuration
 *

 * @author Your Name (your.email@example.com)
 */
import express, { Application } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';

const app: Application = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (_req, res) => {
  res.status(200).json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Routes
app.get('/', (_req, res) => {
  res.json({
    message: 'My Awesome API',
    version: '0.1.0',
    documentation: '/api/docs',
  });
});

export default app;
```

## Project Types and Variations

### Node.js Backend with Database
```
Additional Dependencies:

- pg (PostgreSQL)
- typeorm or prisma (ORM)
- bcrypt (password hashing)
- jsonwebtoken (JWT)

Structure additions:
- src/entities/
- src/migrations/
- src/database/
```

### React Frontend with State Management
```
Additional Dependencies:

- redux and @reduxjs/toolkit
- react-hook-form
- react-toastify
- framer-motion

Structure additions:
- src/store/
- src/features/
- src/animations/
```

### Next.js with Authentication
```
Additional Dependencies:

- next-auth
- @auth/prisma-adapter
- prisma
- bcrypt

Structure additions:
- src/app/api/auth/
- prisma/
- middleware.ts
```

## Customization Options

### Minimal Setup (Fast Start)
```
"Use init-javascript-project with minimal configuration:

- Basic structure only
- Essential documentation
- Skip CI/CD files
- No example tests"
```

### Full Setup (Production-Ready)
```
"Use init-javascript-project with full configuration:

- Complete directory structure
- GitHub Actions CI/CD
- Docker configuration
- Comprehensive documentation
- Example tests and fixtures
- Pre-commit hooks"
```

### Custom Template
```
"Use init-javascript-project with custom requirements:

- GraphQL API with Apollo Server
- MongoDB database
- Redis caching
- Docker and docker-compose
- Kubernetes configuration"
```

## Common Post-Initialization Tasks

### 1. Configure IDE
- Install recommended extensions (ESLint, Prettier, TypeScript)
- Set up auto-format on save
- Configure debugger launch configurations
- Set up path aliases

### 2. Set Up Git Hooks
```bash
npm install --save-dev husky lint-staged
npx husky init
```

Create `.husky/pre-commit`:
```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
```

Add to package.json:
```json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

### 3. Set Up Docker
Create `Dockerfile`:
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY dist ./dist

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:

      - "3000:3000"
    environment:

      - NODE_ENV=production
    volumes:

      - ./.env:/app/.env
```

### 4. Configure GitHub Repository
- Create repository on GitHub
- Add description and topics
- Set up branch protection rules
- Enable GitHub Actions
- Add status badges to README

## Success Criteria

After initialization, verify:

- [ ] All directories created correctly
- [ ] Configuration files are valid
- [ ] Dependencies installed successfully
- [ ] Development server starts
- [ ] Tests run and pass
- [ ] Linting and formatting tools work
- [ ] TypeScript compilation succeeds
- [ ] Documentation is complete and accurate
- [ ] Git repository initialized
- [ ] Ready to begin development

## Related Skills

**Use After Initialization**:
- `setup-javascript-system-prompt`: Configure Claude Code standards
- `create-claude-md`: Customize project guidelines
- `generate-test-cases`: Add comprehensive tests

**For Development**:
- `plan-before-code`: Plan features before implementing
- `test-driven-development`: Write tests first
- `cleanup-javascript`: Clean code periodically

## Additional Resources

- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Express.js Guide](https://expressjs.com/en/guide/routing.html)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - JavaScript Project Standards
**Priority**: MEDIUM - Standard JavaScript/TypeScript project initialization
