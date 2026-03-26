# Claude Code Extensibility Guide (March 2026)

A practical guide to choosing the right extension mechanism: **Skills**, **Hooks**, **Subagents**, **Agent Teams**, **MCP Servers**, **CLAUDE.md**, and **Plugins**.

---

## The Five-Second Decision Tree

```
Need Claude to always know something?          -> CLAUDE.md / .claude/rules/
Need a reusable workflow or task playbook?     -> Skill
Need deterministic automation (no LLM)?        -> Hook
Need context isolation or parallel workers?    -> Subagent
Need cross-agent coordination?                 -> Agent Team
Need external tools/APIs/databases?            -> MCP Server
Need to distribute all of the above?           -> Plugin
```

---

## 1. CLAUDE.md / Memory (Always-On Context)

### What it is
Markdown files loaded at every session start. Project conventions, coding standards, "never do X" rules, build commands. There are two complementary systems: **CLAUDE.md files** (you write) and **Auto Memory** (Claude writes).

### CLAUDE.md vs Auto Memory

| | CLAUDE.md files | Auto Memory |
|---|---|---|
| **Who writes it** | You | Claude |
| **What it contains** | Instructions and rules | Learnings and patterns |
| **Scope** | Project, user, or org | Per working tree |
| **Loaded into** | Every session | Every session (first 200 lines) |
| **Use for** | Coding standards, workflows, architecture | Build commands, debugging insights, preferences |

### Where CLAUDE.md lives
| Scope | Location | Shared? |
|-------|----------|---------|
| Managed (org) | System paths (`/Library/Application Support/ClaudeCode/`) | Yes (deployed by IT) |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Yes (VCS) |
| User | `~/.claude/CLAUDE.md` | No |
| Local | `./CLAUDE.local.md` | No (gitignored) |

### Directory hierarchy loading

Claude Code walks **up** the directory tree from CWD, loading CLAUDE.md at each level. Subdirectory CLAUDE.md files load on-demand when Claude works in that area. This means a monorepo root and each package can each have their own CLAUDE.md.

### Excluding CLAUDE.md files

Use the `claudeMdExcludes` setting to skip specific files by path or glob pattern:

```json
{ "claudeMdExcludes": ["packages/legacy/CLAUDE.md"] }
```

Managed policy CLAUDE.md files cannot be excluded.

### Modular rules with `.claude/rules/`

Instead of bloating CLAUDE.md, split conventions into focused files:

```
.claude/
  CLAUDE.md           # Main project instructions (<200 lines)
  rules/
    models.md         # Model conventions
    controllers.md    # Controller conventions
    testing.md        # Testing conventions
```

Rules exist at two levels:
- **Project rules**: `.claude/rules/` -- apply to this project, committed to VCS
- **User rules**: `~/.claude/rules/` -- apply to every project (loaded first, lower priority)

All `.md` files in `.claude/rules/` are automatically loaded. Symlinks are supported (circular symlinks handled gracefully). **Path-scoping** limits when rules load:

```yaml
---
paths:
  - "app/models/**/*.rb"
  - "spec/models/**/*.rb"
---

# Model Conventions
- Keep models thin: data, validations, associations only
```

This rule only loads when Claude works on model files, saving context tokens.

### @imports syntax

CLAUDE.md supports importing other files:

```markdown
See @README.md for project overview
See @docs/api-patterns.md for API conventions
```

Imports can be recursive (max depth: 5 hops). Use sparingly.

### Subdirectory CLAUDE.md

Files in subdirectories load on-demand when Claude works in that area. Useful for monorepos:

```
packages/
  frontend/.claude/CLAUDE.md    # Frontend-specific rules
  backend/.claude/CLAUDE.md     # Backend-specific rules
```

### Auto Memory

Claude accumulates knowledge across sessions automatically (enabled by default since v2.1.59+). Stored at `~/.claude/projects/<project>/memory/` with a `MEMORY.md` entrypoint. First 200 lines loaded at session start; topic files loaded on demand.

Key details:
- Storage path is based on **git repo root**, not CWD -- all worktrees/subdirectories in the same repo share one memory directory
- Custom location: `autoMemoryDirectory` setting (not accepted from project settings for security)
- Toggle: `/memory` command, `autoMemoryEnabled` setting, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
- CLAUDE.md survives compaction -- after `/compact`, Claude re-reads CLAUDE.md from disk fresh

### Interactive setup with `/init`

Run `/init` to generate a starter CLAUDE.md. Use `CLAUDE_CODE_NEW_INIT=true` for an interactive multi-phase flow that sets up CLAUDE.md, skills, and hooks with follow-up questions.

### Writing effective CLAUDE.md

- **Run `/init`** to generate a starter automatically
- **Under 200 lines** -- move reference content to skills or rules
- **Be specific** -- "Use double quotes" not "Follow good style"
- **No contradictions** -- conflicting rules reduce adherence
- **Include what Claude can't guess** -- exclude what it already knows

### When to use
- Project conventions that apply to every session
- Build/test/lint commands
- Architecture decisions
- "Always do X" / "Never do Y" rules

### When NOT to use
- Reference material (use a skill -- loads on demand, saves context)
- Enforcement that must be 100% reliable (use a hook)
- Content over ~200 lines (move excess to skills or rules)
- Ephemeral task details (use tasks or plans)

### Maintenance strategy: organic growth

The most effective CLAUDE.md files evolve organically through corrections:
1. When Claude makes a wrong assumption, don't just fix it -- tell Claude to add the correction to CLAUDE.md
2. When code reviews reveal undocumented conventions, add them
3. Every few weeks, ask Claude to review and optimize the file (instructions accumulate, become redundant, or conflict)
4. Use emphasis ("IMPORTANT:", "NEVER") sparingly -- if everything is marked important, nothing is

### Debugging loaded instructions

Use the `InstructionsLoaded` hook event to audit which CLAUDE.md and rules files are loaded, when, and why. Useful for complex setups with many rule files.

### Key insight
> CLAUDE.md is *guidance*, not *enforcement*. Claude reads it and tries to follow it, but compliance is probabilistic. For guaranteed behavior, use hooks.

---

## 2. Skills (Reusable Task Playbooks)

### What it is
A directory with a `SKILL.md` file (YAML frontmatter + markdown instructions) that teaches Claude how to perform a specific task. Skills follow the [Agent Skills open standard](https://agentskills.org/) and replace the older `.claude/commands/` system (existing commands still work).

### File structure
```
.claude/skills/deploy/
  SKILL.md           # Required: frontmatter + instructions
  template.md        # Optional: template Claude fills in
  examples/
    sample.md        # Optional: example output
  scripts/
    validate.sh      # Optional: scripts Claude can run
```

### Frontmatter reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name. Lowercase, hyphens, max 64 chars. Defaults to directory name |
| `description` | Recommended | What the skill does and when to use it. **The #1 factor for auto-invocation** |
| `argument-hint` | No | Hint during autocomplete (e.g., `[issue-number]`) |
| `disable-model-invocation` | No | `true` = only user can invoke. Default: `false` |
| `user-invocable` | No | `false` = only Claude can invoke. Default: `true` |
| `allowed-tools` | No | Restrict available tools when skill is active |
| `model` | No | Override model for this skill |
| `effort` | No | `low` / `medium` / `high` / `max` (Opus only) |
| `context` | No | `fork` = run in isolated subagent context |
| `agent` | No | Which subagent type when `context: fork` (Explore, Plan, general-purpose, or custom) |
| `hooks` | No | Hooks scoped to this skill's lifecycle |

### String substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` or `$N` | Specific argument by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing the SKILL.md file |

### Dynamic context injection

The `` !`<command>` `` syntax runs shell commands before the skill content is sent to Claude:

```markdown
Current branch: !`git branch --show-current`
Recent commits: !`git log --oneline -5`
```

### Extended thinking

Include the word **"ultrathink"** anywhere in skill content to enable extended thinking mode. Claude will reason more deeply about the task before responding.

### Where it lives
| Scope | Path | Priority |
|-------|------|----------|
| Enterprise | Managed settings | Highest |
| Personal | `~/.claude/skills/<name>/SKILL.md` | High |
| Project | `.claude/skills/<name>/SKILL.md` | Medium |
| Plugin | `<plugin>/skills/<name>/SKILL.md` | Lowest (namespaced) |

Same-name skills: higher-priority location wins. Plugin skills use `plugin-name:skill-name` namespace.

### Automatic discovery

- Skills in subdirectory `.claude/skills/` are discovered when Claude works in that area (monorepo support)
- Skills from `--add-dir` directories are loaded and live-reloaded during sessions

### Two patterns
1. **Reference skills** -- domain knowledge, conventions, style guides (inline, `user-invocable: false`)
2. **Task skills** -- workflows like deploy, commit, review (`disable-model-invocation: true`)

### Invocation control

| Frontmatter | You can invoke | Claude can invoke | Description loaded |
|-------------|---------------|-------------------|-------------------|
| (default) | Yes | Yes | Always in context |
| `disable-model-invocation: true` | Yes | No | Not in context |
| `user-invocable: false` | No | Yes | Always in context |

### Bundled skills
| Skill | Purpose |
|-------|---------|
| `/batch <instruction>` | Parallel codebase-wide changes. Researches, decomposes into 5-30 units, spawns one background agent per unit in isolated git worktrees. Each opens a PR |
| `/claude-api` | Load API reference for your language (Python, TypeScript, Java, Go, Ruby, C#, PHP, cURL). Auto-activates on `anthropic` / `@anthropic-ai/sdk` imports |
| `/debug [description]` | Troubleshoot current session by reading debug log |
| `/loop [interval] <prompt>` | Repeated execution on interval (default 10m). Useful for polling deploys, babysitting PRs |
| `/simplify [focus]` | Reviews recent changes with 3 parallel review agents, aggregates findings, applies fixes |

### Description engineering (critical)

The `description` field determines whether Claude auto-loads a skill. Generic descriptions fail. Use the **WHEN + WHEN NOT** pattern:

```yaml
description: >-
  Implements Rails caching patterns for performance optimization.
  Use when adding fragment caching, Russian doll caching, low-level
  caching, cache invalidation, or when user mentions caching,
  performance, cache keys, or memoization.
  WHEN NOT: General query optimization (use performance-optimization),
  background job processing, or N+1 queries.
```

**Tips from community testing:**
- Use possessive pronouns for personal skills ("HIS/HER work preferences") to prevent contamination
- Multi-skill coordination works -- Claude successfully loads complementary skills together
- Skills are efficient: ~100 tokens during scanning, <5k when activated

### SKILL.md size guidance

Keep SKILL.md files **under 500 lines**. Move detailed reference material to separate files in the skill directory. Community testing shows that conciseness beats comprehensiveness -- one project reduced agent instructions by 65% (803 → 281 lines) and quality scores improved from 62 to 85.

### Permission rules for skills

Use `Skill(name)` for exact match or `Skill(name *)` for prefix match in permission rules.

### Restricting Claude's skill access

Three ways:
1. Deny the Skill tool entirely in permissions
2. Allow/deny specific skills using permission rules
3. Set `disable-model-invocation: true` on individual skills

### Context budget

Skill descriptions share a character budget (2% of context window, fallback 16,000 chars). Override with `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var.

### Troubleshooting
- **Skill not triggering**: Check description, try `What skills are available?`, rephrase
- **Triggers too often**: Make description more specific, add `disable-model-invocation: true`
- **Not all skills visible**: May exceed character budget

### When to use
- Repeatable workflows (deploy, review, generate)
- Domain-specific coding conventions loaded on demand
- Reference material too large for CLAUDE.md
- Teaching Claude *how* to use a tool or API effectively

### When NOT to use
- Rules that must apply every session (use CLAUDE.md)
- Deterministic enforcement (use hooks)
- One-off tasks (just tell Claude directly)

### Key insight
> The `description` field is the #1 success factor. Claude uses it to decide when to auto-load. Use WHEN + WHEN NOT patterns in descriptions.

---

## 3. Hooks (Deterministic Lifecycle Automation)

### What it is
Shell commands, HTTP endpoints, LLM prompts, or agent prompts that execute automatically at lifecycle events. **No LLM judgment involved** -- they fire every time the event matches.

### Configuration

Three levels of nesting: **hook event** > **matcher group** > **hook handlers**.

```json
// .claude/settings.json or ~/.claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(cat | jq -r '.tool_input.file_path // empty') && [ -n \"$FILE\" ] && [[ \"$FILE\" == *.rb ]] && bundle exec rubocop -a \"$FILE\" > /dev/null 2>&1 || true",
            "timeout": 30,
            "statusMessage": "Auto-formatting with RuboCop..."
          }
        ]
      }
    ]
  }
}
```

### Hook locations (priority order)
| Location | Scope | Shareable |
|----------|-------|-----------|
| Managed policy settings | Organization-wide | Yes |
| `~/.claude/settings.json` | All your projects | No |
| `.claude/settings.json` | Single project | Yes (VCS) |
| `.claude/settings.local.json` | Single project | No |
| Plugin `hooks/hooks.json` | When plugin is enabled | Yes |
| Skill or agent frontmatter | While the component is active | Yes |

### Four handler types
| Type | What it does | Default Timeout |
|------|-------------|---------|
| `command` | Runs shell script, receives JSON on stdin | 600s |
| `http` | POSTs JSON to URL | 30s |
| `prompt` | Single-turn LLM yes/no decision | 30s |
| `agent` | Spawns subagent for complex validation | 60s |

### Common handler fields

| Field | Description |
|-------|-------------|
| `type` | `command`, `http`, `prompt`, or `agent` |
| `timeout` | Override default timeout (ms) |
| `statusMessage` | Text shown in spinner during execution |
| `once` | Run only once per session |
| `async` | `true` for background execution (not supported for decision-making hooks) |

### Hook deduplication

Identical command hooks (same command string) or HTTP hooks (same URL) run only once even if defined in multiple scopes.

### Disabling hooks

Set `"disableAllHooks": true` in settings to disable all hooks. Respects settings hierarchy.

### Complete lifecycle events

| Event | Can Block? | Matcher Target | Common use |
|-------|-----------|----------------|------------|
| `SessionStart` | No | `source` (startup/resume/clear) | Restore context, setup environment |
| `InstructionsLoaded` | No | File path | Audit logging when CLAUDE.md loads |
| `UserPromptSubmit` | Yes | Prompt text | Input validation, prompt rewriting, context injection |
| `PreToolUse` | Yes | Tool name | Security gates, command blocking, auto-allow/deny |
| `PermissionRequest` | Yes | Tool name | Auto-allow/deny specific tools |
| `PostToolUse` | No* | Tool name | Auto-formatting, test running, logging |
| `PostToolUseFailure` | No | Tool name | Structured error logging |
| `Notification` | No | Type (permission_prompt, idle_prompt, etc.) | Desktop notifications, TTS alerts |
| `SubagentStart` | Yes | Agent type | Context injection, spawn logging |
| `SubagentStop` | Yes | Agent type | Agent lifecycle management |
| `Stop` | Yes | -- | Notifications, summary generation, force continuation |
| `StopFailure` | No | Error type (rate_limit, auth, billing, etc.) | Error alerting |
| `TeammateIdle` | Yes | -- | Keep teammates working |
| `TaskCompleted` | Yes | -- | Quality gates before task completion |
| `ConfigChange` | Yes | Config type | Block unauthorized config changes |
| `WorktreeCreate` | Yes | -- | Custom worktree behavior |
| `WorktreeRemove` | No | -- | Cleanup |
| `PreCompact` | No | Trigger (manual/auto) | Transcript backup |
| `PostCompact` | No | -- | Context preservation |
| `Elicitation` | Yes | -- | Auto-respond to MCP server input requests |
| `ElicitationResult` | No | -- | Modify elicitation responses |
| `SessionEnd` | No | -- | Session logging (1.5s default timeout) |

*PostToolUse can provide feedback via `decision: "block"` but tool already executed.

### Exit code protocol
| Exit | Meaning |
|------|---------|
| 0 | Success. Parse JSON from stdout for decisions |
| 2 | **Block the action**. stderr fed back to Claude |
| Other | Non-blocking warning. stderr in verbose mode |

### JSON output from hooks

Hooks can return structured JSON on stdout:

```json
{
  "continue": true,
  "stopReason": "string",
  "suppressOutput": true,
  "decision": "approve",
  "systemMessage": "Context injected into conversation",
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "additionalContext": "Extra context for Claude"
  }
}
```

**Flow control priority:**
1. `"continue": false` -- takes precedence over all
2. `"decision": "block"` -- hook-specific blocking
3. Exit code 2 -- simple blocking via stderr
4. Other exit codes -- non-blocking errors

### PreToolUse decision control

PreToolUse hooks can return decisions for specific tools:

```json
{
  "decision": "approve",
  "updatedInput": { "command": "safer-version-of-command" }
}
```

- `"approve"` -- allow without permission prompt
- `"deny"` -- block execution
- `"ask"` -- show permission prompt (default)

### PermissionRequest decision control

PermissionRequest hooks can dynamically modify permissions via `updatedPermissions` in hook output.

### SessionStart environment injection

SessionStart hooks can write environment variables via `$CLAUDE_ENV_FILE`. Write `KEY=VALUE` lines to the file at this path, and they'll be set for the session.

```bash
# In a SessionStart hook command:
echo "DATABASE_URL=postgres://..." >> "$CLAUDE_ENV_FILE"
```

### SessionEnd timeout

Default timeout for SessionEnd hooks is 1.5 seconds. Override with `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`.

### The "Starter Three" (highest value, lowest effort)

**1. Auto-format** on `PostToolUse` (matcher: `Edit|Write`):
```json
{
  "type": "command",
  "command": "FILE=$(cat | jq -r '.tool_input.file_path // empty') && [ -n \"$FILE\" ] && [[ \"$FILE\" == *.rb ]] && bundle exec rubocop -a \"$FILE\" > /dev/null 2>&1 || true",
  "timeout": 30,
  "statusMessage": "Auto-formatting with RuboCop..."
}
```

**2. Dangerous command blocking** on `PreToolUse` (matcher: `Bash`):
```json
{
  "type": "command",
  "command": "CMD=$(cat | jq -r '.tool_input.command // empty') && if echo \"$CMD\" | grep -qiE '(rm\\s+-rf\\s+[/~]|DROP\\s+TABLE|DROP\\s+DATABASE|git\\s+push\\s+.*--force\\s+.*(main|master|production)|chmod\\s+777)'; then echo 'Blocked: Destructive command' >&2; exit 2; fi",
  "timeout": 5,
  "statusMessage": "Checking command safety..."
}
```

**3. Desktop notifications** on `Stop`:
```json
{
  "type": "command",
  "command": "osascript -e 'display notification \"Claude has finished responding\" with title \"Claude Code\"' 2>/dev/null || true",
  "timeout": 5
}
```

### Hooks in skills and agents

Hooks can be scoped to a component's lifecycle via frontmatter:

```yaml
# In a subagent's .md file
---
name: safe-writer
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "echo 'Bash blocked in this agent' >&2; exit 2"
---
```

### UserPromptSubmit deep dive

This hook fires before Claude processes your prompt. It can:
1. **Log prompts** -- record every prompt with timestamp
2. **Block prompts** -- exit code 2 prevents Claude from seeing the prompt
3. **Add context** -- stdout text is prepended to your prompt
4. **Validate content** -- check for dangerous patterns, secrets, policy violations

### When to use
- Deterministic side effects (linting, formatting, notifications)
- Security enforcement (blocking dangerous commands)
- Audit logging (every Bash command to a file)
- CI triggers (post-edit test runs)
- Permission auto-decisions (allow/deny specific tools)
- Quality gates (TaskCompleted validation)
- Context injection (SessionStart, SubagentStart)

### When NOT to use
- Anything requiring Claude's reasoning (use skills)
- Behavioral guidance (use CLAUDE.md)
- Complex multi-step validation (use a skill with `context: fork`)

### Key insight
> Skills are *suggestions*. Hooks are *guarantees*. If something must happen 100% of the time, it's a hook. If Claude's judgment is acceptable, it's a skill.

---

## 4. Subagents (Isolated Specialist Workers)

### What it is
Specialized AI assistants running in their own context window with custom system prompts, specific tools, and independent permissions. Each subagent runs independently and reports results back to the parent.

### Built-in subagents
| Agent | Model | Tools | Auto-delegated when |
|-------|-------|-------|---------------------|
| **Explore** | Haiku | Read-only | Code search, file discovery (supports thoroughness: quick/medium/very thorough) |
| **Plan** | Inherits | Read-only | Gathering context in plan mode |
| **general-purpose** | Inherits | All | Complex multi-step tasks |
| **Bash** | Inherits | Terminal | Commands needing separate context |
| **statusline-setup** | Sonnet | Read, Edit | Configuring `/statusline` |
| **Claude Code Guide** | Haiku | Web tools | Questions about Claude Code features |

### Creating subagents

**Interactive creation:** Run `/agents` to open the creation interface.

**Manual creation:** Write a markdown file with YAML frontmatter:

```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
description: Reviews code for quality and best practices. Use proactively after code changes. WHEN NOT: Implementing fixes, writing tests, or generating new features.
tools: [Read, Grep, Glob, Bash]
model: sonnet
maxTurns: 20
permissionMode: acceptEdits
memory: project
isolation: worktree
skills:
  - api-conventions
---

You are a code reviewer. Analyze code and provide specific,
actionable feedback on quality, security, and best practices.
```

### Full frontmatter reference

| Field | Description |
|-------|-------------|
| `name` | Display name for the agent |
| `description` | When to use this agent. **Include "use proactively" for auto-delegation** |
| `tools` | Allowlist of tools (e.g., `[Read, Grep, Glob, Bash]`) |
| `disallowedTools` | Denylist alternative to `tools` |
| `model` | `sonnet`, `opus`, `haiku`, full model ID, or `inherit` |
| `permissionMode` | `default`, `acceptEdits`, `plan`, `dontAsk`, `bypassPermissions` |
| `maxTurns` | Maximum conversation turns |
| `skills` | Skills to preload at startup |
| `mcpServers` | MCP servers scoped to this agent (inline or referenced) |
| `hooks` | Hooks scoped to this agent's lifecycle |
| `memory` | Persistent memory scope: `user`, `project`, or `local` |
| `background` | `true` to default to background execution |
| `effort` | `low` / `medium` / `high` / `max` |
| `isolation` | `worktree` for safe parallel edits in isolated git worktree |

### Frontmatter notes

- `tools` vs `disallowedTools`: Use `tools` for an allowlist OR `disallowedTools` for a denylist. `disallowedTools` is applied before `tools`.
- `skills`: Skills listed here are **fully preloaded** (content injected into context), not just made available. Use for skills the agent always needs.
- `mcpServers`: Can be server name references or inline definitions. Scoped MCP servers connect when the subagent starts and disconnect when it finishes, keeping tool descriptions out of the main conversation context.
- Plugin subagents cannot use `hooks`, `mcpServers`, or `permissionMode` fields (security restriction).

### Restricting spawnable subagents

Limit which subagents an agent can spawn:

```yaml
tools: [Read, Write, Edit, Agent(worker, researcher)]
```

This restriction only applies to agents running as the main thread with `claude --agent`.

### File locations (priority order)
1. `--agents` CLI flag or `--agents` JSON (session only, highest)
2. `.claude/agents/` (project)
3. `~/.claude/agents/` (personal)
4. Plugin `agents/` directory (lowest)

### How to invoke subagents

**6 ways** to trigger a subagent -- 3 by you, 3 by Claude:

#### User-initiated

**1. @-mention (explicit, recommended)**
```
@"code-reviewer (agent)" look at the auth changes
```

**2. Natural language (implicit)**
```
Use the code-reviewer subagent to check the authentication module
```

**3. Session-wide via CLI flag**
```bash
claude --agent code-reviewer
```
Or set as project default: `{ "agent": "code-reviewer" }` in `.claude/settings.json`

#### Claude-initiated (automatic delegation)

Claude auto-delegates based on the `description` field (most important), task nature, and conversation context. Include "use proactively" in the description for proactive delegation.

#### Inline definition (ephemeral, no file needed)
```bash
claude --agents '{
  "reviewer": {
    "description": "Expert code reviewer",
    "prompt": "You are a senior reviewer. Focus on quality and security.",
    "tools": ["Read", "Grep", "Glob"],
    "model": "sonnet"
  }
}'
```

### Foreground vs Background execution

| Aspect | Foreground (default) | Background |
|--------|---------------------|------------|
| Blocking | Blocks main conversation | Runs concurrently |
| Permissions | Interactive prompts | Pre-approved only; auto-denies the rest |
| How to trigger | Default | Say "run this in background", press **Ctrl+B**, or `background: true` |
| Limit | 1 at a time | Up to 10 simultaneous |
| Disable | N/A | `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` |

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| **Ctrl+B** | Send current task to background |
| **Ctrl+T** | Toggle task list (shows running agents) |
| **Ctrl+F** | Kill all background agents (press twice) |

### Permission modes

| Mode | Behavior | Best for |
|------|----------|----------|
| `default` | Standard permission prompts | General use |
| `acceptEdits` | Auto-accept file edits, still prompt for Bash | Write-capable agents |
| `plan` | Read-only exploration | Research agents, code review |
| `dontAsk` | Like acceptEdits + auto-deny unknown tools | Automated workflows |
| `bypassPermissions` | Skip all prompts | Trusted, well-tested agents only |

### Persistent memory

Enable with `memory` field:

```yaml
memory: project    # Accumulate project-specific learnings
# or: user, local
```

Agents with memory accumulate knowledge across sessions -- particularly valuable for test patterns, architectural decisions, and debugging insights.

### Resuming a subagent

Claude receives the agent ID on completion and can use `SendMessage` to resume with full context preserved:
```
Continue that code review and now analyze the authorization logic too
```

Transcripts are stored at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.

### Auto-compaction

Subagents auto-compact at ~95% context capacity. Override with `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`.

### Advanced patterns

**Chaining subagents** -- sequential multi-step workflows:
```
1. Use @migration-agent to create the schema
2. Use @model-agent to implement the model
3. Use @service-agent to add business logic
```

**Parallel research** -- multiple background agents investigating independently.

**Isolate high-volume operations** -- delegate test suites, log processing to separate context windows.

### Smart model routing for custom agents

| Model | When to use | Examples |
|-------|-------------|---------|
| `opus` | Deep reasoning, complex decisions | security-auditor, architect-reviewer |
| `sonnet` | Everyday coding, balanced cost/quality | backend-developer, service-agent |
| `haiku` | Quick tasks, high volume | documentation, seo-specialist |

### When to use
- **Context isolation**: exploration would pollute your main conversation
- **Parallel work**: up to 10 simultaneous background agents
- **Verbose operations**: search results, large file reads
- **Specialized workers**: different tools/models/permissions per task
- **Git isolation**: `isolation: worktree` for safe parallel edits

### When NOT to use
- Quick back-and-forth iteration (stay in main conversation)
- Tasks requiring conversation history (subagents start fresh)
- When agents need to talk to each other (use Agent Teams)

### Key insight
> "Since context is your fundamental constraint, subagents are one of the most powerful tools available." Use them to keep your main conversation clean while exploring in parallel.

---

## 5. Agent Teams (Coordinated Multi-Agent Work)

### What it is
Multiple independent Claude Code sessions (2-16) that coordinate with shared task lists and peer-to-peer messaging. One lead agent orchestrates, teammates work independently and communicate directly.

### Status: Experimental

Enable in `.claude/settings.json`:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### How to start a team
Tell Claude in natural language:
```
Create an agent team to refactor the payment module:
- One teammate handles the model layer
- One handles the service layer
- One handles the controller + request specs
Have them coordinate and work in parallel.
```

You can specify models, team size, and constraints:
```
Create a team with 4 teammates using Sonnet. Require plan approval before changes.
```

### Architecture
| Component | Role |
|-----------|------|
| **Lead** | Your main session. Creates the team, spawns teammates, coordinates |
| **Teammates** | Separate Claude Code instances with their own context windows |
| **Task list** | Shared work items with pending/in-progress/completed states. File locking prevents race conditions |
| **Mailbox** | Messaging system for inter-agent communication |

Storage: `~/.claude/teams/{team-name}/config.json`, tasks at `~/.claude/tasks/{team-name}/`

### Display modes

| Mode | Description | Set via |
|------|-------------|---------|
| `in-process` | All teammates in your terminal. Cycle with Shift+Down | `"teammateMode": "in-process"` in settings or `--teammate-mode` flag |
| `tmux` / `iTerm2` / `auto` | Each teammate gets its own pane. Click to interact | Default if in tmux |

### Plan approval

Teammates can be required to plan before implementing. The lead reviews and approves/rejects plans autonomously. Specify with "Require plan approval before changes" in team creation instructions.

### Keyboard shortcuts

| Key | Action |
|-----|--------|
| **Shift+Down** | Cycle to next teammate |
| **Shift+Up** | Cycle to previous teammate |
| **Enter** | View selected teammate's session |
| **Escape** | Interrupt a teammate's current turn |
| **Ctrl+T** | Toggle shared task list |

### Communicating with teammates

**Directly (in-process):** Shift+Down to select, type message, Enter.

**Directly (tmux):** Click into teammate's pane and type.

**Via the lead:**
```
Tell the security reviewer to also check for SQL injection
Ask the researcher teammate to shut down
```

### Quality gates with hooks

```json
{
  "hooks": {
    "TeammateIdle": [{ "hooks": [{ "type": "command", "command": "./check-idle.sh" }] }],
    "TaskCompleted": [{ "hooks": [{ "type": "command", "command": "./validate-task.sh" }] }]
  }
}
```

- `TeammateIdle`: Exit code 2 sends feedback and keeps teammate working
- `TaskCompleted`: Exit code 2 prevents completion and returns feedback

### Best practices
- Give teammates enough context in their initial instructions
- 3-5 teammates recommended, 5-6 tasks per teammate
- Size tasks appropriately -- not too granular, not too broad
- Wait for teammates to finish before evaluating
- Start with research and review before code changes
- Avoid file conflicts -- assign distinct file areas
- Monitor and steer -- check in on progress

### Limitations
- No session resumption with in-process teammates
- Task status can lag
- One team per session, no nested teams
- Lead is fixed, permissions set at spawn
- Split panes require tmux or iTerm2

### Subagents vs Agent Teams decision

| Question | Subagent | Agent Team |
|----------|----------|------------|
| Do agents need to talk to each other? | No -- only report to parent | Yes -- peer-to-peer messaging |
| How many concurrent? | Up to 10 | 2-16 |
| Cost model | Share parent's token budget | Each is a separate Claude instance |
| Coordination | Parent orchestrates | Shared task list + mailbox |
| Use case | "Go do X and report back" | "Work together on X" |

### When to use
- Complex work requiring cross-agent **coordination** and **communication**
- Competing hypotheses (multiple agents try different approaches)
- Large parallel research with shared findings
- Multi-area refactoring where agents need to stay aware of each other's changes

### When NOT to use
- Simple parallelizable tasks (use subagents -- much cheaper)
- Tasks where agents don't need to communicate
- Token-sensitive work (each teammate is a separate Claude instance)

### Key insight
> **Subagents report to a parent. Teammates message each other directly.** Choose subagents for delegation (fan-out/fan-in), teams for collaboration (peer-to-peer).

---

## 6. MCP Servers (External Tool Connections)

### What it is
External tools/services connected via the Model Context Protocol (open standard). Gives Claude access to databases, APIs, browsers, issue trackers, etc.

### Setup
```bash
# Remote server (HTTP) -- recommended
claude mcp add --transport http github https://api.github.com/mcp

# Remote server (SSE) -- deprecated, use http instead
claude mcp add --transport sse sentry https://sentry.io/mcp

# WebSocket server
claude mcp add --transport ws realtime wss://example.com/mcp

# Local server (stdio)
claude mcp add playwright -- npx -y @playwright/mcp@latest

# Project-scoped (shared via .mcp.json)
claude mcp add --scope project db -- npx @mcp/postgres

# From JSON configuration
claude mcp add-json myserver '{"type":"http","url":"https://example.com/mcp"}'

# Import from Claude Desktop
claude mcp add-from-claude-desktop
```

### Managing servers
```bash
claude mcp list              # List all servers
claude mcp get github        # Show server details
claude mcp remove github     # Remove a server
/mcp                         # In-session management and auth
```

### Configuration scopes (priority order)
| Scope | Storage | Shared? |
|-------|---------|---------|
| Local | `~/.claude.json` (per-project) | No |
| Project | `.mcp.json` | Yes (VCS) |
| User | `~/.claude.json` (global) | No |
| Managed | `managed-mcp.json` | Yes (IT) |

### Environment variable expansion in `.mcp.json`

```json
{
  "mcpServers": {
    "db": {
      "command": "npx",
      "args": ["@mcp/postgres", "${DATABASE_URL}"],
      "env": {
        "PG_PASSWORD": "${DB_PASSWORD:-defaultpass}"
      }
    }
  }
}
```

Supports `${VAR}` and `${VAR:-default}` syntax in `command`, `args`, `env`, `url`, and `headers`.

### Authentication

OAuth 2.0 support for remote MCP servers:
- Use `/mcp` to authenticate interactively
- Fixed callback port: `--callback-port 8080`
- Pre-configured OAuth: `--client-id` and `--client-secret`
- Dynamic headers: `headersHelper` field for token refresh scripts

### Tool Search (deferred loading)

Automatically enabled when MCP tools exceed 10% of context. Only descriptions load at startup; full schemas are fetched on demand via `ToolSearch`. Reduces context usage by ~85%.

Override: `ENABLE_TOOL_SEARCH` env var.

### MCP output limits

Default max: 25,000 tokens per tool response. Warning threshold: 10,000 tokens. Override with `MAX_MCP_OUTPUT_TOKENS`.

### Advanced features

- **Push messages with channels**: MCP servers can push events to Claude. Subscribe with `channelsEnabled: true`
- **MCP resources**: Reference with `@server:protocol://resource/path`
- **MCP prompts as commands**: Invoke with `/mcp__servername__promptname`
- **Claude Code as MCP server**: `claude mcp serve` exposes Claude Code itself via MCP
- **Servers from claude.ai**: Servers configured at `claude.ai/settings/connectors` are automatically available
- **Elicitation**: MCP servers can request user input via forms or URLs

### Managed MCP configuration

**Option 1: Exclusive control** -- Deploy `managed-mcp.json` to system directories. Takes full control.

**Option 2: Policy-based** -- `allowedMcpServers` and `deniedMcpServers` in managed settings. Denylist takes absolute precedence.

**Option 3: Strict lockdown** -- `allowManagedMcpServersOnly` in managed settings restricts to admin-defined allowlist only.

### MCP registry

Official registry at `https://api.anthropic.com/mcp-registry/v0/servers` for discovering available servers.

### Per-project MCP approval

Control which `.mcp.json` servers are enabled: `enableAllProjectMcpServers`, `enabledMcpjsonServers`, `disabledMcpjsonServers` in settings.

### Tool naming convention

MCP tools follow `mcp__<server>__<tool>` pattern (e.g., `mcp__memory__create_entities`). Use this pattern in permission rules and hook matchers.

### When to use
- Any external data source or action (databases, APIs, browsers)
- Issue trackers (Linear, Jira, GitHub)
- Communication tools (Slack, email)
- Infrastructure management (Vercel, Firebase, Supabase)
- Design tools (Figma)

### Best combined with skills
MCP provides the *connection*. A skill teaches Claude *how to use it effectively*. Example: MCP connects to your database; a skill teaches query patterns and safety rules.

---

## 7. Plugins (Distribution Bundles)

### What it is
Packages that bundle skills + hooks + subagents + MCP servers into a single installable unit. Plugin skills use `plugin-name:skill-name` namespacing.

### Official marketplace

`claude-plugins-official` is automatically available. Browse at [claude.com/plugins](https://claude.com/plugins).

### Installation
```bash
# Browse available plugins
/plugin    # Opens interactive interface

# Install a plugin
/plugin install plugin-name@marketplace-name

# Management
/plugin disable plugin-name
/plugin enable plugin-name
/plugin uninstall plugin-name

# Marketplace management
/plugin marketplace add owner/repo
/plugin marketplace remove marketplace-name
/plugin marketplace update
/plugin marketplace list

# Apply changes after install
/reload-plugins
```

### Scopes
| Scope | Who uses it |
|-------|-------------|
| User (default) | You, across all projects |
| Project | All collaborators in this project |
| Local | You, in this project only |
| Managed | Organization-wide |

### Code intelligence plugins (official)

Enable LSP tools for jump-to-definition, find references, type errors, and automatic diagnostics after edits:

| Language | Server |
|----------|--------|
| TypeScript | typescript-language-server |
| Python | pyright-langserver |
| Rust | rust-analyzer |
| Go | gopls |
| Java | jdtls |
| Kotlin | kotlin-language-server |
| Ruby | (not yet available) |
| C/C++ | clangd |
| Swift | sourcekit-lsp |
| Lua | lua-language-server |
| PHP | intelephense |
| C# | csharp-ls |

### External integration plugins (official)

GitHub, GitLab, Atlassian (Jira/Confluence), Asana, Linear, Notion, Figma, Vercel, Firebase, Supabase, Slack, Sentry.

### Development workflow plugins (official)

`commit-commands`, `pr-review-toolkit`, `agent-sdk-dev`, `plugin-dev`.

### Auto-updates

Official marketplaces have auto-update enabled by default. Control with `DISABLE_AUTOUPDATER` and `FORCE_AUTOUPDATE_PLUGINS` env vars.

### Team marketplace setup

Use `extraKnownMarketplaces` in `.claude/settings.json` to add custom marketplaces:

```json
{
  "extraKnownMarketplaces": [
    { "name": "team-plugins", "source": "github", "owner": "myorg", "repo": "claude-plugins" }
  ]
}
```

Source types: `github`, `git`, `directory`, `hostPattern`, `settings` (inline definitions without a hosted repository).

### Security
Plugins execute arbitrary code with user privileges. Only install from trusted sources. Review before enabling.

### When to use
- Distributing your extension stack to a team
- Installing community-built capabilities
- Packaging related skills + hooks + agents together
- Adding code intelligence for typed languages

---

## Comparison Matrix

| Feature | Nature | Deterministic? | Context Cost | Loads When |
|---------|--------|---------------|-------------|------------|
| **CLAUDE.md** | Always-on context | Yes (always loads) | Every request | Session start |
| **Rules** | Path-scoped context | Yes (loads when path matches) | On demand | When working in matching paths |
| **Skills** | On-demand playbooks | No (Claude decides) | ~100 tokens scanning; <5k invoked | Description at start; full on use |
| **Hooks** | Lifecycle automation | Yes (always fires) | Zero (external) | On trigger event |
| **Subagents** | Isolated workers | No (Claude delegates) | Separate window | On demand |
| **Agent Teams** | Coordinated squads | No | Separate instances | On demand |
| **MCP Servers** | External connections | Yes (always available) | Deferred via ToolSearch | Session start |
| **Plugins** | Distribution packages | N/A | Depends on contents | When enabled |

---

## Settings Reference

### Configuration scopes (precedence)

1. **Managed** (highest) -- server-managed, plist/registry, or system-level
2. **Command line arguments**
3. **Local project** -- `.claude/settings.local.json`
4. **Shared project** -- `.claude/settings.json`
5. **User** (lowest) -- `~/.claude/settings.json`

Array settings merge across scopes.

### JSON schema

Add to any settings file for editor autocomplete:

```json
{ "$schema": "https://json.schemastore.org/claude-code-settings.json" }
```

### Key settings

| Setting | Description |
|---------|-------------|
| `permissions.allow` | Auto-allow specific tool patterns |
| `permissions.deny` | Block specific tool patterns |
| `hooks` | Lifecycle hooks configuration |
| `env` | Environment variables for all sessions |
| `model` | Default model |
| `availableModels` | List of available models |
| `modelOverrides` | Map model aliases to full IDs (e.g., Bedrock ARNs) |
| `agent` | Default subagent for all sessions |
| `effortLevel` | Default effort level (`low` / `medium` / `high`), persisted across sessions |
| `enableAllProjectMcpServers` | Auto-enable project MCP servers |
| `autoMode` | Enable auto mode (fewer permission prompts) |
| `disableAutoMode` | Set to `"disable"` to prevent auto mode activation |
| `includeGitInstructions` | Set `false` to remove built-in git instructions |
| `language` | Set Claude's response language |
| `outputStyle` | Configure output style adjustment |
| `plansDirectory` | Customize where plan files are stored |
| `autoMemoryDirectory` | Custom auto memory location |
| `cleanupPeriodDays` | Session retention (default: 30 days, set 0 to disable persistence) |
| `claudeMdExcludes` | Skip specific CLAUDE.md files by path or glob |

### Auto mode settings

```json
{
  "autoMode": {
    "environment": ["CI=true"],
    "allow": ["Bash(npm test:*)"],
    "soft_deny": ["WebFetch"]
  }
}
```

### Permission rule syntax

```
Tool                    # Allow/deny entire tool
Tool(specifier)         # Allow/deny specific usage
Bash(npm test:*)        # Allow bash commands starting with "npm test:"
WebFetch(domain:x.com)  # Allow fetching from specific domain
Agent(reviewer)         # Allow spawning specific agent
```

### Sandbox settings

Full filesystem and network isolation:

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["rm"],
    "allowUnsandboxedCommands": false,
    "filesystem": {
      "allowWrite": ["/path/to/project"],
      "denyWrite": ["/etc"],
      "allowRead": ["/usr/local"],
      "denyRead": ["/etc/secrets"]
    },
    "network": {
      "allowedDomains": ["api.example.com"],
      "allowUnixSockets": false,
      "allowLocalBinding": false
    }
  }
}
```

### Worktree settings (monorepo optimization)

```json
{
  "worktree": {
    "symlinkDirectories": ["node_modules", "vendor/bundle"],
    "sparsePaths": ["packages/my-package/**"]
  }
}
```

`symlinkDirectories` avoids re-installing dependencies per worktree. `sparsePaths` limits which files are checked out.

### Attribution settings

Customizable commit and PR attribution. Default includes co-authored-by trailer. Set to empty string to hide.

### Hook security settings

| Setting | Description |
|---------|-------------|
| `allowManagedHooksOnly` | Only allow hooks from managed settings |
| `allowedHttpHookUrls` | Whitelist of allowed HTTP hook URLs |
| `httpHookAllowedEnvVars` | Env vars that can be used in HTTP hook headers |

### Managed settings delivery

Three methods: server-managed (API), MDM/OS-level policies (macOS plist, Windows registry, Linux `/etc/`), and file-based `managed-settings.json` at system paths.

### Verify active settings

Run `/status` to see all active settings, their sources, and loaded instruction files.

---

## Best Practices

### The core constraint
> Claude's context window fills up fast, and performance degrades as it fills.

### Give Claude a way to verify its work

This is the **single highest-leverage thing** you can do:

| Strategy | Before | After |
|----------|--------|-------|
| Provide tests | "implement validateEmail" | "write validateEmail, run the tests after" |
| Visual verification | "make dashboard look better" | "[paste screenshot] implement this design, take a screenshot and compare" |
| Address root causes | "the build is failing" | "the build fails with this error: [paste]. Fix it and verify the build succeeds" |

### Explore first, then plan, then code

Use **Plan Mode** to separate exploration from execution:
1. **Explore** -- read code, understand structure
2. **Plan** -- design the approach, get alignment
3. **Implement** -- execute the plan
4. **Commit** -- verify and commit

### Manage context aggressively

- `/clear` between unrelated tasks
- Auto compaction handles long sessions
- `/compact <instructions>` for manual compaction with guidance
- `/btw` for quick questions that don't enter history
- Use subagents for investigation (separate context window)

### Course-correct early

- `Esc` to stop mid-response
- `Esc + Esc` or `/rewind` to restore to previous checkpoint
- Every action creates a checkpoint -- double-tap Escape to revert

### Run non-interactive mode

```bash
claude -p "fix all lint errors"                    # Single prompt
claude --permission-mode auto -p "run tests"       # Auto mode
claude --continue                                  # Resume last session
```

### Fan out across files

```bash
for file in src/**/*.ts; do
  claude -p "add JSDoc comments to $file" --allowedTools Edit
done
```

### Writer/Reviewer pattern

Use separate sessions for writing and reviewing. One session writes code, another reviews it with fresh context. This avoids bias from the writing session and uses context more efficiently.

### Brainstorm before coding (community pattern)

Before any implementation, have Claude ask what you're really trying to do. Refine ideas through questions, then present the design in digestible sections for validation. This prevents the costly "built the wrong thing" failure mode.

### Separate analysis from execution (community pattern)

Use read-only subagents for analysis (tools: `[Read, Grep, Glob]`), then execute writes in the main conversation or write-capable agents. This hybrid pattern provides:
- Security boundary (analysis can't accidentally modify code)
- Cleaner main context (verbose search results stay in subagent)
- Better quality (analysis is deliberate, execution follows a plan)

### Task sizing heuristic (community pattern)

Break implementation into **2-5 minute tasks**. Each task should have exact file paths, complete code, and verification steps. Write plans for "an enthusiastic junior engineer with poor taste, no judgment, and no project context" -- this forces extreme explicitness that produces better results.

### Smart model routing for subagents (community pattern)

| Tier | Model | Use for |
|------|-------|---------|
| Deep reasoning | `opus` | Architecture decisions, security audits, complex refactoring |
| Everyday coding | `sonnet` | Feature implementation, CRUD, standard patterns |
| Quick tasks | `haiku` | Linting, formatting, documentation, simple searches |

### Avoid common failure patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Kitchen sink session | Context fills up with unrelated work | `/clear` between tasks |
| Correcting over and over | After 2 failures, you're fighting inertia | `/clear` and write a better prompt |
| Over-specified CLAUDE.md | Too many rules reduce adherence | Ruthlessly prune |
| Trust-then-verify gap | Claude produces code you don't test | Always provide verification |
| Infinite exploration | Research spirals without resolution | Scope investigations or use subagents |
| Verbose agent prompts | More lines != better instructions | 65% reduction improved one project's quality score from 62 to 85 |

---

## Adoption Playbook (Start Simple, Add as Needed)

### Phase 1: Foundation
1. Run `/init` to generate a starting `CLAUDE.md`
2. Add project conventions and build commands
3. Keep it under 200 lines
4. Split domain rules into `.claude/rules/` with path-scoping

### Phase 2: Workflows
5. Create skills for your most common tasks (deploy, review, generate)
6. Use WHEN + WHEN NOT patterns in all skill descriptions
7. Add MCP servers for external tools (database, issue tracker, browser)
8. Combine: MCP provides connection, skill teaches usage

### Phase 3: Automation
9. Add the "Starter Three" hooks (auto-format, command blocking, notifications)
10. Add permission hooks to auto-allow trusted tools
11. Add quality gate hooks (TaskCompleted validation)

### Phase 4: Scale
12. Create custom agents with `permissionMode`, `memory`, and clear descriptions
13. Use `isolation: worktree` for agents that run in parallel
14. Add "use proactively" to agents that should auto-run (linter, test writer)
15. Try Agent Teams for complex multi-agent coordination

### Phase 5: Share
16. Package everything into plugins for your team
17. Publish to a marketplace if broadly useful

---

## Common Mistakes

| Mistake | Why it's wrong | Fix |
|---------|---------------|-----|
| Putting everything in CLAUDE.md | Bloats context, reduces adherence | Move reference content to skills, rules to `.claude/rules/` |
| Using CLAUDE.md for enforcement | Claude may not follow it 100% | Use hooks for guaranteed behavior |
| Using hooks for reasoning | Hooks can't think, only execute | Use skills for tasks requiring judgment |
| Running everything in main context | Context window fills up fast | Use subagents for exploration and verbose tasks |
| Using Agent Teams for simple delegation | Massive token overhead | Use subagents unless agents need to coordinate |
| Skipping skill descriptions | Claude won't know when to auto-load | Write clear WHEN/WHEN NOT descriptions |
| Generic skill descriptions | Auto-invocation fails | Be specific: "WHEN: X. WHEN NOT: Y (use Z instead)" |
| Not combining MCP + skills | Claude may misuse the tool | Skill teaches the patterns; MCP provides the connection |
| No `permissionMode` on agents | Constant permission prompts | Use `acceptEdits` for writers, `plan` for readers |
| No `memory` on agents | Agents lose learnings between sessions | Add `memory: project` for persistent knowledge |
| More lines = better agent prompts | Longer doesn't mean better | 54% reduction in one test improved score from 62 to 85 |
| Skipping path-scoping on rules | Rules load when not relevant | Add `paths:` frontmatter to scope by file pattern |

---

## Community Tools & Resources

### Agent Skills Collections
- [obra/superpowers](https://github.com/obra/superpowers) -- Complete SDLC workflow: brainstorming, planning, TDD, code review, subagent-driven development with git worktree isolation. Available as a plugin.
- [Trail of Bits Security Skills](https://github.com/trailofbits/skills) -- Security-focused code auditing
- [Claude Scientific Skills](https://github.com/K-Dense-AI/claude-scientific-skills) -- Research, science, engineering
- [Everything Claude Code](https://github.com/affaan-m/everything-claude-code) -- Core engineering domains
- [cc-devops-skills](https://github.com/akin-ozer/cc-devops-skills) -- DevOps and IaC

### Subagent Collections
- [Awesome Claude Code Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) -- 127+ specialized agents across 10 categories with smart model routing (opus/sonnet/haiku per agent). Includes `rails-expert` for Rails 8 development.

### Orchestrators
- [Claude Squad](https://github.com/smtg-ai/claude-squad) -- Multi-session orchestration with tmux
- [Claude Task Master](https://github.com/eyaltoledano/claude-task-master) -- Task management
- [Claude Swarm](https://github.com/parruda/claude-swarm) -- Swarm orchestration

### Hooks
- [Dippy](https://github.com/ldayton/Dippy) -- AST-based safe bash auto-approval
- [parry](https://github.com/vaporif/parry) -- Prompt injection scanner hook
- [TDD Guard](https://github.com/nizos/tdd-guard) -- TDD enforcement: blocks file changes violating TDD principles

### Tooling
- [Claude Squad](https://github.com/smtg-ai/claude-squad) -- Multi-session management with tmux
- [claude-tmux](https://github.com/nielsgroen/claude-tmux) -- Tmux integration with git worktrees
- [Container Use](https://github.com/dagger/container-use) -- Docker container execution for safe `--dangerously-skip-permissions`
- [claude-esp](https://github.com/phiat/claude-esp) -- Stream hidden output to separate terminal
- [claude-rules-doctor](https://github.com/search?q=claude-rules-doctor) -- Detects dead `.claude/rules/` files where path globs no longer match

### Workflows
- [RIPER Workflow](https://github.com/tony/claude-code-riper-5) -- Research/Innovate/Plan/Execute/Review phases
- [AB Method](https://github.com/ayoubben18/ab-method) -- Spec-driven incremental missions
- [Claude CodePro](https://github.com/maxritter/claude-codepro) -- Spec-driven TDD with cross-session memory
- [Compound Engineering Plugin](https://github.com/search?q=compound-engineering-plugin) -- Turns past mistakes into lessons for future improvement

### CLAUDE.md Examples
- [Awesome Claude Skills](https://github.com/travisvn/awesome-claude-skills) -- Curated skill list with creation guide
- [How to Write a Good CLAUDE.md](https://www.builder.io/blog/claude-md-guide) -- Practical guide with organic growth strategy

---

## Sources

### Official Documentation
- [Skills](https://code.claude.com/docs/en/skills)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [MCP](https://code.claude.com/docs/en/mcp)
- [Memory/CLAUDE.md](https://code.claude.com/docs/en/memory)
- [Plugins](https://code.claude.com/docs/en/discover-plugins)
- [Settings](https://code.claude.com/docs/en/settings)
- [Best Practices](https://code.claude.com/docs/en/best-practices)

### Community Resources
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) -- Curated list of skills, agents, hooks, tools
- [Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery) -- Complete hook lifecycle coverage with UV scripts
- [Awesome Claude Skills](https://github.com/travisvn/awesome-claude-skills) -- Curated skill list and creation guide
- [Awesome Claude Subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) -- 127+ specialized agents
- [How to Write a Good CLAUDE.md](https://www.builder.io/blog/claude-md-guide) -- Practical CLAUDE.md guide
- [Skills vs Commands vs Subagents vs Plugins](https://www.youngleaders.tech/p/claude-skills-commands-subagents-plugins) -- Mental model for the four types
