# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: TypeScript/JavaScript (ES2022+)
- **Runtime**: Node.js 20+ / Bun
- **Package Manager**: npm / pnpm / yarn
- **Linting/Formatting**: ESLint + Prettier (or Biome)
- **Testing**: Jest / Vitest
- **Type Checking**: TypeScript strict mode

## Project Structure
```
src/                  - Application source code
├── config/           - Configuration
├── core/             - Core application logic
├── components/       - UI components (if applicable)
├── utils/            - Utility functions
├── types/            - TypeScript type definitions
tests/                - Test suites
├── unit/             - Unit tests
├── integration/      - Integration tests
├── temp/             - Temporary tests (auto-deleted)
dist/                 - Compiled output
docs/                 - Documentation
```

## Key Files
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `.eslintrc.js` - ESLint configuration
- `.prettierrc` - Prettier configuration
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
npm run dev
npm start

# Testing
npm test
npm run test:watch
npm run test:coverage

# Code Quality
npm run lint
npm run lint:fix
npm run format
npx tsc --noEmit
```

## Quick Reference

### Task Types → Focus Areas
| Task Type | Skills Activated |
|-----------|------------------|
| Bug Fix | interaction-principles, code-standards, quality-checklist |
| New Feature | project-setup, workflow-methodology, testing-framework |
| Refactoring | code-standards, implementation-patterns |
| Documentation | documentation-standards |
| Version/Git | version-control |

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete architecture, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers in package.json (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with tests/temp/
- Document progress in DEVLOG.md
- Use TypeScript strict mode for new projects
- Follow the quality checklist before delivering code
