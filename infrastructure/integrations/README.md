# External Integrations & MCPs

Model Context Protocol (MCP) integrations and external service configurations for Claude Code skills.

## What are MCPs?

**Model Context Protocol (MCP)** is Anthropic's standard for connecting Claude to external tools, services, and data sources. MCPs enable Claude Code to:

- Access external APIs (GitHub, databases, cloud services)

- Read/write to specialized data stores

- Interact with development tools

- Retrieve real-time information

## MCP Configuration

MCPs are configured in `.mcp.json` at your project root:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "API_KEY": "your-key-here"
      }
    }
  }
}
```

---

## Available MCP Templates

### Development Tools

#### 1. GitHub Integration

**Purpose:** Access GitHub repositories, issues, PRs, and code

**Configuration:**
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

**Setup:**

1. Generate GitHub Personal Access Token:

   - Go to GitHub Settings > Developer settings > Personal access tokens

   - Generate new token (classic)

   - Select scopes: `repo`, `read:org`, `read:user`

2. Add token to `.mcp.json`

3. Restart Claude Code

**Skills that use this:**

- `code-commit-workflow`

- `dependency-security-audit`

- `code-review-*` (for remote repos)

---

#### 2. GitLab Integration

**Purpose:** Access GitLab repositories and CI/CD pipelines

**Configuration:**
```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "your_gitlab_token_here",
        "GITLAB_API_URL": "https://gitlab.com/api/v4"
      }
    }
  }
}
```

---

### Database Integrations

#### 3. PostgreSQL

**Purpose:** Query and analyze database schemas and data

**Configuration:**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/dbname"
      }
    }
  }
}
```

**Skills that use this:**

- `generate-api-docs` (for database-backed APIs)

- `code-review-performance` (for query optimization)

---

#### 4. MySQL/MariaDB

**Configuration:**
```json
{
  "mcpServers": {
    "mysql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mysql"],
      "env": {
        "MYSQL_CONNECTION_STRING": "mysql://user:password@localhost:3306/dbname"
      }
    }
  }
}
```

---

#### 5. MongoDB

**Configuration:**
```json
{
  "mcpServers": {
    "mongodb": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mongodb"],
      "env": {
        "MONGODB_CONNECTION_STRING": "mongodb://user:password@localhost:27017/dbname"
      }
    }
  }
}
```

---

### Cloud Services

#### 6. AWS

**Purpose:** Access AWS resources (S3, Lambda, DynamoDB, etc.)

**Configuration:**
```json
{
  "mcpServers": {
    "aws": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-aws"],
      "env": {
        "AWS_ACCESS_KEY_ID": "your_access_key",
        "AWS_SECRET_ACCESS_KEY": "your_secret_key",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

---

#### 7. Google Cloud Platform

**Configuration:**
```json
{
  "mcpServers": {
    "gcp": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-gcp"],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json"
      }
    }
  }
}
```

---

#### 8. Azure

**Configuration:**
```json
{
  "mcpServers": {
    "azure": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-azure"],
      "env": {
        "AZURE_CLIENT_ID": "your_client_id",
        "AZURE_CLIENT_SECRET": "your_client_secret",
        "AZURE_TENANT_ID": "your_tenant_id"
      }
    }
  }
}
```

---

### AI Services

#### 9. OpenAI

**Purpose:** Use OpenAI models for specialized tasks

**Configuration:**
```json
{
  "mcpServers": {
    "openai": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-openai"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key"
      }
    }
  }
}
```

---

### Documentation & Knowledge

#### 10. Confluence

**Purpose:** Access company documentation and knowledge bases

**Configuration:**
```json
{
  "mcpServers": {
    "confluence": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-confluence"],
      "env": {
        "CONFLUENCE_URL": "https://your-company.atlassian.net",
        "CONFLUENCE_EMAIL": "your.email@company.com",
        "CONFLUENCE_API_TOKEN": "your_confluence_token"
      }
    }
  }
}
```

---

#### 11. Notion

**Configuration:**
```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-notion"],
      "env": {
        "NOTION_API_KEY": "your_notion_integration_token"
      }
    }
  }
}
```

---

## MCP Setup Guide

### Step 1: Identify Required MCPs

Review your skills and determine which MCPs are needed:

```bash
# Check which skills require external services
python tools/install_skill.py --info skill-name
# Look for "Tools Required" or "External Services" sections
```

### Step 2: Create .mcp.json

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {}
}
```

### Step 3: Add Configurations

Copy relevant configurations from templates above.

### Step 4: Obtain API Keys

For each MCP:

1. Visit the service's developer portal

2. Generate API keys/tokens

3. Add to `.mcp.json` env section

### Step 5: Test Configuration

```bash
# Restart Claude Code
# Test MCP access by using a skill that requires it
"Use the code-review-security skill to audit dependencies"
```

---

## Security Best Practices

### Never Commit Secrets

**Bad:**
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_abc123..."
      }
    }
  }
}
```

**Good:**
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

Then set environment variable:
```bash
# Linux/Mac
export GITHUB_TOKEN="ghp_abc123..."

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_abc123..."

# Windows CMD
set GITHUB_TOKEN=ghp_abc123...
```

### Use .gitignore

Add to `.gitignore`:
```
.mcp.json
.env
*.secrets
credentials.json
```

### Use Environment Files

Create `.env` file (add to .gitignore):
```
GITHUB_TOKEN=ghp_abc123...
OPENAI_API_KEY=sk-abc123...
AWS_ACCESS_KEY_ID=AKIA...
```

Load in `.mcp.json`:
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Rotate Keys Regularly

- Change API keys every 90 days

- Use short-lived tokens when possible

- Revoke unused keys immediately

---

## Troubleshooting

### MCP Not Found

**Problem:** `Cannot find module '@modelcontextprotocol/server-github'`

**Solution:**
```bash
# Install MCP package globally
npm install -g @modelcontextprotocol/server-github

# Or use npx (auto-installs)
# Already used in configuration examples above
```

### Authentication Failed

**Problem:** `401 Unauthorized` or `403 Forbidden`

**Solution:**

1. Verify API key is correct

2. Check key has required permissions

3. Ensure key hasn't expired

4. Test key directly with service API

### Connection Timeout

**Problem:** `ETIMEDOUT` or connection errors

**Solution:**

1. Check network connectivity

2. Verify service URL is correct

3. Check firewall settings

4. Test with curl/wget:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

### Rate Limiting

**Problem:** `429 Too Many Requests`

**Solution:**

1. Reduce API call frequency

2. Implement caching in your workflows

3. Upgrade to higher rate limit tier

4. Use authenticated requests (higher limits)

---

## MCP Development

Want to create custom MCPs? See:

- [Anthropic MCP Documentation](https://docs.anthropic.com/model-context-protocol)

- [MCP SDK](https://github.com/anthropics/mcp-sdk)

- [Example MCPs](https://github.com/anthropics/mcp-examples)

---

## Common MCP Patterns

### Pattern 1: Multi-Service Setup

```json
{
  "mcpServers": {
    "github": { ... },
    "postgres": { ... },
    "aws": { ... }
  }
}
```

### Pattern 2: Environment-Specific

```json
{
  "mcpServers": {
    "database": {
      "env": {
        "DB_URL": "${DATABASE_URL}",
        "ENVIRONMENT": "${NODE_ENV}"
      }
    }
  }
}
```

### Pattern 3: Conditional Loading

Load different MCPs based on project type:

**For web projects:**

- GitHub

- PostgreSQL/MySQL

- AWS/GCP

- OpenAI

**For data science projects:**

- GitHub

- MongoDB

- AWS S3

- OpenAI

**For enterprise projects:**

- GitLab

- Oracle/SQL Server

- Azure

- Confluence

---

## Skills by MCP Requirement

### Requires GitHub MCP:
- `code-commit-workflow`

- `dependency-security-audit` (for remote repos)

### Requires Database MCP:
- `generate-api-docs` (for DB-backed APIs)

- `code-review-performance` (for query analysis)

### Requires Cloud MCP:
- `dependency-security-audit` (for cloud dependencies)

- `generate-sbom` (for cloud resources)

### No MCP Required:
- Most skills work with local files only

- MCP is optional enhancement for additional functionality

---

*MCP Integration Guide - Part of DevAI-Hub v0.9.7*

*Last Updated: April 2026*
