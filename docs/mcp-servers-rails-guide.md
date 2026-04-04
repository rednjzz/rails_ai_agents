# MCP Servers for Rails Development with Claude Code (March 2026)

A practical guide to extending Claude Code with MCP servers for a modern Ruby on Rails stack (Rails 8.1, PostgreSQL, Inertia.js + React, Kamal).

---

## What Are MCP Servers?

MCP (Model Context Protocol) is an open standard — donated to the Linux Foundation in December 2025 and adopted by OpenAI, Google DeepMind, and Anthropic — that connects AI coding agents to external tools, databases, and APIs.

In Claude Code, MCP servers give Claude **direct access** to systems it can't reach natively: your database schema, production errors, browser automation, live documentation, and more.

**Key principle from the extensibility guide:**
> MCP provides the *connection*. A skill teaches Claude *how to use it effectively*. Combine both for best results.

---

## The Rails Developer's MCP Stack

### Recommended Setup (Priority Order)

| Priority | Server | What It Gives You | Install Effort |
|----------|--------|-------------------|----------------|
| 1 | **rails-mcp-server** | Rails app context (routes, models, schema, Kamal docs) | `gem install` |
| 2 | **Postgres MCP Pro** | Database introspection, query analysis, index tuning | `docker pull` |
| 3 | **Context7** | Live, version-specific documentation (Rails, Ruby, React, Inertia.js) | `npx` |
| 4 | **Playwright MCP** | Browser automation for E2E testing and debugging | `npx` |
| 5 | **GitHub MCP** | Deep GitHub integration (issues, PRs, Actions) | Remote OAuth |
| 6 | **Sentry MCP** | Production error monitoring and root cause analysis | Remote OAuth |
| 7 | **Sequential Thinking** | Structured problem-solving for complex debugging | `npx` |

---

## 1. Rails App Context — rails-mcp-server

**What:** A Ruby gem that gives Claude deep context about your Rails application — routes, models, associations, schema, controller-view relationships, and environment configs.

**Why it matters:** Without this, Claude has to `grep` and `Read` files to understand your app structure. With it, Claude can query routes, inspect model relationships, and access schema information through dedicated tools.

**Features:**
- Browse project files and view filtered routes
- Inspect model relationships and associations
- Access database schema directly
- Execute sandboxed Ruby code
- Built-in Rails and **Kamal** documentation

**Install:**
```bash
gem install rails-mcp-server
rails-mcp-config  # Interactive setup — generates Claude Code config
```

**Or add to your project manually:**
```json
// .mcp.json (project-scoped, shared via git)
{
  "mcpServers": {
    "rails": {
      "command": "rails-mcp-server",
      "args": ["--project-dir", "."]
    }
  }
}
```

**Repo:** [github.com/maquina-app/rails-mcp-server](https://github.com/maquina-app/rails-mcp-server)

### Alternative: ActionMCP (Your App as MCP Server)

If you want to **expose your own Rails app's capabilities** as MCP tools (e.g., letting Claude query your domain models directly):

```bash
bundle add actionmcp
bin/rails action_mcp:install:migrations
bin/rails generate action_mcp:install
bin/rails db:migrate
```

**Requirements:** Ruby 3.4.8+, Rails 8.1.1+, PostgreSQL/MySQL/SQLite3.

**Repo:** [github.com/seuros/action_mcp](https://github.com/seuros/action_mcp)

---

## 2. Database — Postgres MCP Pro

**What:** Production-grade PostgreSQL MCP server with configurable read/write access, performance analysis, index tuning, EXPLAIN plan analysis, and health monitoring.

**Why it matters:** Claude can directly inspect your schema, run queries, analyze slow queries with EXPLAIN, suggest missing indexes, and monitor database health — all without you copy-pasting output.

**Features:**
- Schema introspection and query execution
- Performance analysis with EXPLAIN plans
- Index tuning (explores thousands of possible indexes)
- Health monitoring: vacuum status, connection usage, buffer cache, replication lag
- Configurable access modes (read-only for production safety)

**Install:**
```bash
# Via Docker (recommended)
claude mcp add postgres -- docker run -i --rm \
  -e DATABASE_URI="${DATABASE_URL}" \
  crystaldba/postgres-mcp \
  --access-mode=unrestricted

# Via pip
pipx install postgres-mcp
claude mcp add postgres -- postgres-mcp --access-mode=unrestricted --database-uri "${DATABASE_URL}"
```

**Access modes:**
- `--access-mode=unrestricted` — Development (read + write)
- `--access-mode=restricted` — Production (read-only, safe)

**Repo:** [github.com/crystaldba/postgres-mcp](https://github.com/crystaldba/postgres-mcp)

### Alternatives

| Server | Best For | Source |
|--------|----------|--------|
| **pgEdge Postgres MCP** | Multi-database support, Amazon RDS | [pgedge.com](https://www.pgedge.com/blog/introducing-the-pgedge-postgres-mcp-server) |
| **Google MCP Toolbox** | Multi-engine (Postgres, MySQL, BigQuery, etc.) | [googleapis.github.io](https://googleapis.github.io/genai-toolbox/how-to/connect-ide/postgres_mcp/) |
| **Supabase MCP** | Full Supabase backend (DB + auth + storage) | [github.com/supabase-community/supabase-mcp](https://github.com/supabase-community/supabase-mcp) |

---

## 3. Live Documentation — Context7

**What:** Fetches current, version-specific documentation from official sources at query time. Prevents hallucinated APIs and deprecated patterns.

**Why it matters:** Claude's training data has a cutoff. When you're using Rails 8.1, Inertia.js, or the latest React features, Context7 ensures Claude references the actual current docs rather than hallucinating outdated APIs.

**Install:**
```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

**Usage:** Add "use context7" to any prompt:
```
Set up Inertia.js partial reloads for live updates. use context7
Configure Solid Queue for background jobs. use context7
```

**Limits:** Free tier: 1,000 requests/month, 60/hour (reduced January 2026).

**Repo:** [github.com/upstash/context7](https://github.com/upstash/context7)

---

## 4. Browser Automation — Playwright MCP

**What:** Microsoft's official browser automation MCP. Uses the browser's accessibility tree for fast, deterministic control. Multi-browser: Chrome, Firefox, WebKit.

**Why it matters:** Claude can run your Rails app in a browser, navigate pages, fill forms, click buttons, and verify E2E behavior — all from your conversation. Essential for debugging Inertia page transitions, testing React component interactions, and validating client-side behavior.

**Install:**
```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

**Use cases for Rails:**
- Debug Inertia page rendering and prop passing issues visually
- Test React component interactions
- Verify responsive Tailwind layouts
- Automate E2E test scenarios before writing Capybara specs

**Repo:** [github.com/microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp)

### Alternative: Cloudflare Browser Rendering

Run Playwright MCP in the cloud — no local browser needed:
[developers.cloudflare.com/browser-rendering/playwright/playwright-mcp/](https://developers.cloudflare.com/browser-rendering/playwright/playwright-mcp/)

---

## 5. GitHub Integration — GitHub MCP Server

**What:** The most widely used MCP server overall. Browse repos, manage issues/PRs, search code, analyze commits, monitor GitHub Actions.

**Why it matters:** While Claude Code has built-in `gh` CLI support, the GitHub MCP provides deeper automation — cross-repo search, complex PR workflows, release management, and Actions monitoring.

**Install (Remote OAuth — recommended):**
```bash
claude mcp add github --url https://api.githubcopilot.com/mcp/ \
  --headers "Authorization: Bearer ${GITHUB_TOKEN}"
```

**Install (Docker — local):**
```bash
claude mcp add github -- docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_TOKEN}" \
  ghcr.io/github/github-mcp-server stdio
```

**Repo:** [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server)

---

## 6. Error Monitoring — Sentry MCP

**What:** Remote OAuth server. Query production errors, view stack traces, identify regressions. Integrates with Seer for AI-powered root cause analysis.

**Why it matters:** Claude can pull production error context directly — stack traces, affected users, frequency — and correlate with your codebase to suggest fixes. No more copy-pasting Sentry URLs.

**Install:**
```bash
claude mcp add sentry --url https://mcp.sentry.dev/mcp
# Prompts for OAuth authentication
```

**Use cases:**
- "What are the top errors in production this week?"
- "Analyze this Sentry issue and suggest a fix"
- Automate weekly performance triage

**Repo:** [github.com/getsentry/sentry-mcp](https://github.com/getsentry/sentry-mcp)
**Docs:** [docs.sentry.io/ai/mcp/](https://docs.sentry.io/ai/mcp/)

### Alternative: Datadog MCP (GA March 2026)

If you use Datadog instead of Sentry:
```bash
claude mcp add datadog -- docker run -i --rm \
  -e DD_API_KEY="${DD_API_KEY}" \
  -e DD_APP_KEY="${DD_APP_KEY}" \
  datadog-labs/mcp-server
```

Supports metrics, logs, traces, APM, error tracking, feature flags, and LLM observability.

**Repo:** [github.com/datadog-labs/mcp-server](https://github.com/datadog-labs/mcp-server)
**Docs:** [docs.datadoghq.com/bits_ai/mcp_server/](https://docs.datadoghq.com/bits_ai/mcp_server/)

---

## 7. Structured Problem Solving — Sequential Thinking

**What:** Dynamic, reflective problem-solving through thought sequences. Part of the official MCP reference servers.

**Why it matters:** For complex debugging, architecture decisions, or multi-step reasoning, this server helps Claude break problems into structured thought sequences with branching and revision.

**Install:**
```bash
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking
```

---

## Bonus: Semantic Code Analysis — Serena

**What:** Provides semantic code retrieval and editing at the symbol level via Language Server Protocol. Supports 30+ languages including Ruby.

**Why it matters:** Instead of reading entire files, Claude can find symbols, references, and make precision edits — especially useful in large Rails codebases.

**Install:**
```bash
uvx --from git+https://github.com/oraios/serena serena start-mcp-server \
  --context ide-assistant --project "$(pwd)"
```

**Repo:** [github.com/oraios/serena](https://github.com/oraios/serena)

---

## Complete Setup Script

Copy this to get the full Rails MCP stack running:

```bash
#!/bin/bash
# MCP Server Setup for Rails + PostgreSQL + Kamal

# 1. Rails app context (models, routes, schema, Kamal docs)
gem install rails-mcp-server
rails-mcp-config

# 2. PostgreSQL database access
claude mcp add postgres -- docker run -i --rm \
  -e DATABASE_URI="${DATABASE_URL}" \
  crystaldba/postgres-mcp \
  --access-mode=unrestricted

# 3. Live documentation
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest

# 4. Browser automation
claude mcp add playwright -- npx @playwright/mcp@latest

# 5. GitHub integration (choose one)
claude mcp add github --url https://api.githubcopilot.com/mcp/ \
  --headers "Authorization: Bearer ${GITHUB_TOKEN}"

# 6. Error monitoring
claude mcp add sentry --url https://mcp.sentry.dev/mcp

# 7. Structured thinking
claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# Verify
claude mcp list
```

---

## Project-Scoped Configuration (.mcp.json)

Share MCP config with your team via `.mcp.json` (committed to git):

```json
{
  "mcpServers": {
    "rails": {
      "command": "rails-mcp-server",
      "args": ["--project-dir", "."]
    },
    "postgres": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "DATABASE_URI=${DATABASE_URL}",
        "crystaldba/postgres-mcp",
        "--access-mode=unrestricted"
      ]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    },
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

Environment variables (`${DATABASE_URL}`) are expanded at runtime. Store secrets in `.env`, never in `.mcp.json`.

---

## Best Practices

### Context Window Management

Each MCP server adds tool definitions to Claude's system prompt, consuming context even when not used. Claude Code mitigates this with **Tool Search** (deferred loading) — enabled automatically when MCP tools exceed 10% of context. Only descriptions load at startup; full schemas are fetched on demand.

**Recommendations:**
- Disable MCP servers you're not actively using during long sessions
- Override output limits if needed: `MAX_MCP_OUTPUT_TOKENS` (default: 25,000)
- Override tool search: `ENABLE_TOOL_SEARCH` env var

### Security

- Store tokens in environment variables, never in config files
- Use `--access-mode=restricted` for production database connections
- Be cautious with MCP servers that fetch untrusted content (prompt injection risk)
- Review MCP server code before adding to your project

### Combine MCP + Skills

MCP provides the connection. Skills teach Claude how to use it effectively:

```yaml
# .claude/skills/database-query/SKILL.md
---
name: database-query
description: >-
  Query the PostgreSQL database safely. Use when analyzing data,
  debugging queries, or investigating schema issues.
  WHEN NOT: Simple schema lookups (use rails-mcp-server instead).
user-invocable: false
---

When querying the database via the postgres MCP server:
- Always use EXPLAIN ANALYZE for performance investigation
- Never run DELETE/DROP in production (check access mode first)
- Prefer CTEs over subqueries for readability
- Always include LIMIT for exploratory queries
```

### Scoping

| Scope | Command Flag | Stored In | Use When |
|-------|-------------|-----------|----------|
| Local (default) | `--scope local` | `~/.claude.json` (per-project) | Personal dev tools |
| Project | `--scope project` | `.mcp.json` | Shared team config |
| User | `--scope user` | `~/.claude.json` (global) | Tools for all projects |

### Subagent-Scoped MCP

You can scope MCP servers to specific subagents — the connection starts when the agent spawns and stops when it finishes:

```yaml
# .claude/agents/db-analyst.md
---
name: db-analyst
description: Analyzes database performance and suggests optimizations.
tools: [Read, Grep, Glob]
model: sonnet
mcpServers:
  - postgres
---

You are a database performance analyst. Use the postgres MCP tools
to analyze query plans, suggest indexes, and identify bottlenecks.
```

---

## Ecosystem Snapshot (March 2026)

The MCP ecosystem has grown to **5,000+ community-built servers** on the [official registry](https://registry.modelcontextprotocol.io/). Notable servers beyond the Rails stack:

| Server | Purpose | Source |
|--------|---------|--------|
| **Figma Dev Mode MCP** | Live design structure for code generation | [developers.figma.com](https://developers.figma.com/docs/figma-mcp-server/) |
| **Atlassian MCP** (Jira/Confluence) | Issue tracking, documentation | [github.com/atlassian/atlassian-mcp-server](https://github.com/atlassian/atlassian-mcp-server) |
| **Firecrawl MCP** | Web scraping, returns clean markdown | [github.com/firecrawl/firecrawl-mcp-server](https://github.com/firecrawl/firecrawl-mcp-server) |
| **Kubernetes MCP** | Multi-cluster K8s management | [github.com/containers/kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server) |
| **Docker MCP** | Container orchestration and debugging | Referenced in [InfoWorld](https://www.infoworld.com/article/4096223/10-mcp-servers-for-devops.html) |
| **Claude Code MCP** | Use Claude Code itself as MCP server | [github.com/steipete/claude-code-mcp](https://github.com/steipete/claude-code-mcp) |

### What's Missing (March 2026)

- **Kamal MCP:** No dedicated server yet. Use `rails-mcp-server` (includes Kamal docs) or Claude Code's Bash tool for `kamal deploy`, `kamal app logs`, etc.
- **Ruby LSP Plugin:** The official code intelligence plugin system supports TypeScript, Python, Rust, Go, Java, etc. — but **Ruby is not yet available**. Use Serena as a workaround.

---

## Sources

### Official
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [MCP Official Registry](https://registry.modelcontextprotocol.io/)
- [MCP Reference Servers](https://github.com/modelcontextprotocol/servers)

### MCP Server Repositories
- [rails-mcp-server](https://github.com/maquina-app/rails-mcp-server)
- [ActionMCP](https://github.com/seuros/action_mcp)
- [Postgres MCP Pro](https://github.com/crystaldba/postgres-mcp)
- [Context7](https://github.com/upstash/context7)
- [Playwright MCP](https://github.com/microsoft/playwright-mcp)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Sentry MCP](https://github.com/getsentry/sentry-mcp) / [Docs](https://docs.sentry.io/ai/mcp/)
- [Datadog MCP](https://github.com/datadog-labs/mcp-server) / [Docs](https://docs.datadoghq.com/bits_ai/mcp_server/)
- [Serena](https://github.com/oraios/serena)

### Curated Lists & Articles
- [8 Best MCP Servers for Claude Code (2026) — Bannerbear](https://www.bannerbear.com/blog/8-best-mcp-servers-for-claude-code-developers-in-2026/)
- [10 Best MCP Servers for Developers — Firecrawl](https://www.firecrawl.dev/blog/best-mcp-servers-for-developers)
- [Top 10 MCP Servers for Claude Code — Apidog](https://apidog.com/blog/top-10-mcp-servers-for-claude-code/)
- [Best MCP Servers — MCPcat](https://mcpcat.io/guides/best-mcp-servers-for-claude-code/)
- [10 MCP Servers for DevOps — InfoWorld](https://www.infoworld.com/article/4096223/10-mcp-servers-for-devops.html)
- [Best MCP Servers 2026 — Builder.io](https://www.builder.io/blog/best-mcp-servers-2026)
- [MCP Ecosystem in 2026 — Apify](https://use-apify.com/blog/mcp-standard-ecosystem-2026)
- [JetBrains RubyMine MCP](https://blog.jetbrains.com/ruby/2025/12/rubymine-2025-3-multi-agent-ai-chat-rails-aware-mcp-server-faster-multi-module-projects-startup-and-more/)
- [pgEdge Postgres MCP](https://www.pgedge.com/blog/introducing-the-pgedge-postgres-mcp-server)
- [Google MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/how-to/connect-ide/postgres_mcp/)
- [Configuring MCP Tools in Claude Code — Scott Spence](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
