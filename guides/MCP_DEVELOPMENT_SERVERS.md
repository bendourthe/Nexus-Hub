# MCP Development Servers Guide

**Recommended MCP servers for development workflows with Claude Code**

[Back to Main](../README.md)

---

## Overview

Model Context Protocol (MCP) servers extend Claude Code with external capabilities. This guide covers the most valuable MCP servers for day-to-day development, organized by workflow stage: Research, Debug, Document, and Test.

---

## Quick Setup

Add these servers to your project `.mcp.json` or user-level `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest"
      ]
    },
    "context7": {
      "command": "npx",
      "args": [
        "-y",
        "@upstash/context7-mcp@latest"
      ]
    },
    "deepwiki": {
      "command": "npx",
      "args": [
        "-y",
        "deepwiki-mcp@latest"
      ]
    },
    "tavily": {
      "type": "http",
      "url": "https://mcp.tavily.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_TAVILY_API_KEY"
      }
    }
  }
}
```

---

## Research Stage

### Context7 (Documentation Lookup)

**Purpose**: Fetch up-to-date documentation for libraries and frameworks directly into Claude Code context. Eliminates hallucinated API calls by grounding responses in real docs.

**When to use**: When working with unfamiliar libraries, checking API signatures, or verifying framework behavior.

**Key capabilities**:
- Look up library documentation by name and version
- Retrieve specific API reference pages
- Get code examples from official docs
- Supports most popular npm, PyPI, and crates.io packages

**Integration with DevAI-Hub skills**: Use alongside `api-design`, `framework-migration-assistant`, and `deprecated-api-updater` to ensure code follows current library conventions.

---

### DeepWiki (Repository Understanding)

**Purpose**: Understand external repositories without cloning them. DeepWiki indexes public GitHub repos and provides structured summaries of architecture, key files, and patterns.

**When to use**: When evaluating third-party libraries, understanding upstream dependencies, or learning from reference implementations.

**Key capabilities**:
- Summarize repository architecture
- Explain key design decisions
- Navigate code structure without cloning
- Answer questions about how a library works internally

**Integration with DevAI-Hub skills**: Pairs well with `trend-research`, `architecture-design`, and `research-plan-implement` for the research phase of new features.

---

### Tavily (Web Search)

**Purpose**: Perform web searches to find solutions, documentation, Stack Overflow answers, and blog posts. Returns structured, LLM-optimized results.

**When to use**: When researching error messages, finding best practices, or looking for solutions to problems not covered in library docs.

**Setup**: Sign up at tavily.com for an API key (free tier available).

**Key capabilities**:
- Search the web with LLM-optimized results
- Filter by domain (docs sites, Stack Overflow, GitHub)
- Get concise answers extracted from search results

**Integration with DevAI-Hub skills**: Supports `research-plan-implement`, `error-explanation-generator`, and `trend-research` workflows.

---

## Debug Stage

### Playwright (Browser Testing and Automation)

**Purpose**: Control a browser for E2E testing, visual regression testing, and debugging web applications. The most versatile MCP server for web development.

**When to use**: When testing web UIs, debugging frontend issues, taking screenshots for documentation, or automating browser workflows.

**Key capabilities**:
- Navigate to URLs and interact with page elements
- Take screenshots and visual comparisons
- Fill forms, click buttons, and verify page content
- Inspect network requests and console output
- Run accessibility audits
- Execute JavaScript in the browser context

**Integration with DevAI-Hub skills**: Essential for `e2e-testing-automation`, `performance-testing`, and `nextjs-expert` workflows.

---

### Chrome DevTools MCP (Performance Analysis)

**Purpose**: Deep performance profiling and debugging through Chrome DevTools Protocol. More specialized than Playwright, focused on performance metrics and network analysis.

**When to use**: When diagnosing performance bottlenecks, analyzing network waterfalls, profiling JavaScript execution, or debugging CSS rendering issues.

**Key capabilities**:
- CPU and memory profiling
- Network request inspection and timing
- CSS/XPath element selection
- Console log monitoring
- Performance metric collection (FCP, LCP, CLS, TTI)

**Integration with DevAI-Hub skills**: Pairs with `code-review-performance`, `performance-testing`, and `observability-setup` for production readiness checks.

---

## Document Stage

### Excalidraw (Diagramming)

**Purpose**: Create architecture diagrams, flowcharts, and visual documentation directly from Claude Code conversations.

**When to use**: When creating visual documentation, architecture diagrams, or explaining system designs.

**Key capabilities**:
- Generate architecture diagrams from descriptions
- Create flowcharts and sequence diagrams
- Export to PNG or SVG for documentation
- Iteratively refine diagrams through conversation

**Integration with DevAI-Hub skills**: Supports `architecture-design`, `technical-documentation`, and `api-documentation` workflows.

---

## Permission Configuration

Add MCP tool permissions to your `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__playwright__*",
      "mcp__context7__*",
      "mcp__deepwiki__*"
    ],
    "ask": [
      "mcp__tavily__*",
      "mcp__excalidraw__*"
    ]
  }
}
```

## Scope Recommendations

| Server | Scope | Rationale |
|--------|-------|-----------|
| Playwright | Project | Testing is project-specific |
| Context7 | User | Useful across all projects |
| DeepWiki | User | Research is cross-project |
| Tavily | User | Web search is universal |
| Chrome DevTools | Project | Performance testing is project-specific |
| Excalidraw | User | Diagramming is cross-project |

**Project scope**: `.mcp.json` in project root (committed to git, shared with team)
**User scope**: `~/.claude/.mcp.json` (personal, not committed)

---

## Related Resources

- [Claude Code Guide](CLAUDE_CODE_GUIDE.md) - Complete Claude Code setup
- [Project Setup Guide](CLAUDE_CODE_PROJECT_SETUP.md) - Project configuration
- [Subagents Guide](SUBAGENTS_GUIDE.md) - Agent configuration
