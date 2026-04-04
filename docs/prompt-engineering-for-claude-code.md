# Prompt Engineering for Claude Code (2026)

A practical guide to writing effective prompts for Claude Code in web development contexts. Covers core principles, prompt structure, common anti-patterns, optimization frameworks, and Rails-specific patterns.

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [The Prompt Quality Spectrum](#2-the-prompt-quality-spectrum)
3. [Prompt Structure Framework](#3-prompt-structure-framework)
4. [Context Engineering](#4-context-engineering)
5. [Rails-Specific Prompting Patterns](#5-rails-specific-prompting-patterns)
6. [Anti-Patterns](#6-anti-patterns)
7. [Prompt Optimization Techniques](#7-prompt-optimization-techniques)
8. [Session Management](#8-session-management)
9. [Writing Effective Skills](#9-writing-effective-skills)

---

## 1. Core Principles

### Intelligence is not the bottleneck -- context is

Claude is already capable. What limits output quality is the context you provide. Every project has unique workflows, standards, and constraints that Claude doesn't inherently know. Your job is to bridge that gap.

### Specificity beats verbosity

A prompt with 3 precise sentences outperforms a vague paragraph. State exactly what you want, the constraints, and what "done" looks like.

### Lead with the outcome, not the process

Tell Claude what you need, not how to think about it. Claude will determine the best approach. Reserve process instructions for cases where the approach genuinely matters.

### Give Claude a feedback loop

Include test commands, linter checks, or expected outputs so Claude can self-correct. When Claude runs tests, sees failures, and fixes them -- you don't have to intervene.

### One task, one prompt

Don't bundle unrelated tasks. Each prompt should have a single, clear objective. For multi-step work, use Plan Mode or break into sequential prompts.

---

## 2. The Prompt Quality Spectrum

### Level 1: Vague (poor)

```
fix the user model
```

Problems: No context on what's broken, no success criteria, Claude will guess.

### Level 2: Directional (mediocre)

```
The User model has a validation bug. Fix it.
```

Better, but: which validation? What's the expected behavior? What's failing?

### Level 3: Specific (good)

```
The User model allows blank emails to pass validation.
Add a presence and format validation for email.
Run the model specs after.
```

Clear problem, clear solution, includes verification step.

### Level 4: Structured (excellent)

```
Bug: User model accepts blank and malformed emails.

Expected: email must be present, unique (case-insensitive), and match
a standard email format.

Constraints:
- Add validations to app/models/user.rb
- Follow existing validation style in that file
- Add specs in spec/models/user_spec.rb
- Run specs to verify

Reference: @app/models/user.rb @spec/models/user_spec.rb
```

Has: problem statement, expected behavior, constraints, verification, file references.

### Level 5: Context-rich (exceptional)

```
Bug: Users can register with blank/malformed emails, causing
downstream failures in the mailer (Entities::NotificationService
crashes on nil email).

Expected: email must be present, unique (case-insensitive), and match
standard format. Return clear error messages for the registration form.

Constraints:
- Add validations to User model following existing patterns
- Add model specs covering: blank, malformed, duplicate (case variants),
  and valid email
- Run specs after changes
- Don't modify the controller or service -- this is a model-layer fix

Context: This is part of the registration flow. The form already
displays model errors via @app/views/users/_form.html.erb
```

Adds: root cause context, downstream impact, scope boundaries, architectural awareness.

---

## 3. Prompt Structure Framework

### The 6-Layer Architecture

Every strong prompt contains some or all of these layers:

| Layer | Purpose | Example |
|-------|---------|---------|
| **Role** | Set expertise context | "You're working on a Rails 8 app with Inertia.js + React" |
| **Objective** | What "done" looks like | "Create a service that processes refunds" |
| **Context** | Background, constraints, scope | "This replaces the callback in Order model" |
| **Input** | Files, data, references | `@app/models/order.rb` `@spec/` |
| **Output** | Expected format/structure | "Follow service object pattern from CLAUDE.md" |
| **Verification** | How to confirm success | "Run `bundle exec rspec spec/services/`" |

Not every prompt needs all 6. Simple tasks need 2-3 layers. Complex tasks benefit from all 6.

### Templates by task type

**Bug fix:**
```
Bug: [what's broken]
Expected: [correct behavior]
Repro: [how to trigger it]
Fix in: [file/layer scope]
Verify: [test command]
```

**New feature:**
```
Feature: [what it does]
Context: [why it's needed, where it fits]
Acceptance criteria:
- [criterion 1]
- [criterion 2]
Constraints: [scope boundaries, patterns to follow]
Reference: @[relevant files]
```

**Refactoring:**
```
Refactor: [what to improve]
Current: [what exists now, what's wrong]
Target: [desired structure/pattern]
Constraint: All existing tests must stay green
Verify: [test command]
```

**Code review / analysis:**
```
Review @[file] for:
- [specific concern 1]
- [specific concern 2]
Don't modify code -- just report findings.
```

---

## 4. Context Engineering

### Use @ references instead of descriptions

```
# Bad
Look at the user model file

# Good
@app/models/user.rb
```

Claude reads the actual file, not a guess about its contents.

### Pipe data directly

```bash
# Feed error output
rails test 2>&1 | claude "Fix these test failures"

# Feed a spec
cat spec/models/user_spec.rb | claude "These specs are failing. Read the model and fix it."
```

### Strategic file references

Reference only what's relevant. Too many files dilute focus:

```
# Bad: information overload
@app/models/ @app/controllers/ @app/services/ @app/views/ @spec/

# Good: targeted context
@app/models/order.rb @app/services/create_order.rb @spec/services/create_order_spec.rb
```

### CLAUDE.md as persistent context

Your CLAUDE.md is loaded every session. Use it for things Claude can't guess:
- Project-specific patterns (service naming, test structure)
- Commands Claude needs to run (test suite, linter)
- Architecture decisions ("services return Result objects")
- Hard rules ("never use callbacks for side effects")

Keep it under 200 lines. Move details to skills or rules.

### Use Plan Mode for ambiguous work

When the task is multi-file, architectural, or you're not sure of the approach:

```
/plan Implement user authentication with has_secure_password
```

Plan Mode forces Claude to research and propose before acting. The overhead (a few minutes) prevents 20 minutes solving the wrong problem.

---

## 5. Rails-Specific Prompting Patterns

### TDD cycle prompt

```
TDD Red phase: Write a failing spec for Entities::CreateService.
It should:
- Create an entity with valid params
- Return a failure result with invalid params
- Enqueue a notification job on success

Don't write the implementation yet. Just the specs.
```

Then:
```
TDD Green phase: Make the failing specs pass with minimal implementation.
Follow the service object pattern from CLAUDE.md.
```

Then:
```
TDD Refactor phase: Clean up the implementation while keeping specs green.
Run specs after each change.
```

### Migration prompt

```
Create a migration to add a status column to orders.
- Type: integer, not null, default 0
- Add an index on [:user_id, :status]
- Make it reversible
- Don't modify the model yet
```

### Inertia prompt

```
Add inline editing for the entity name field on the Show page.
- Use React state to toggle between display and edit mode
- Submit the update via Inertia.router.patch
- Use partial reload to refresh only the entity props
- Keep it in the existing page component, no separate route
Reference: @app/frontend/pages/Entities/Show.tsx
```

### Service extraction prompt

```
Extract the order processing logic from OrdersController#create
into a service object.

Current: @app/controllers/orders_controller.rb (lines 15-45)
Pattern: .call class method, returns Result object
Specs: Create service specs, update controller request specs
Verify: bundle exec rspec spec/services/ spec/requests/orders_spec.rb
```

---

## 6. Anti-Patterns

### The wishful thinker

```
# Bad: no actionable detail
Make the app better and faster
```

Claude can't optimize what isn't defined. Be specific about what "better" means.

### The over-specifier

```
# Bad: micromanaging implementation
Create a method called process_order that takes an order parameter,
assigns it to @order, then calls @order.validate!, then if valid
calls PaymentGateway.charge(@order.total), then...
```

If you know every line, write it yourself. Tell Claude the *what* and *why*, let it determine the *how*.

### The kitchen sink

```
# Bad: too many unrelated tasks
Add user authentication, create an admin dashboard, set up
background jobs for email, and refactor the test suite
```

Split into separate prompts. Each task deserves focused attention.

### The context amnesiac

```
# Bad: assumes Claude remembers a previous session
Continue what we were working on yesterday
```

Claude starts fresh each session. Provide context or reference files.

### The implicit assumption

```
# Bad: assumes knowledge of project decisions
Add caching like we discussed
```

State the caching strategy explicitly. Don't rely on conversational memory for technical decisions.

### The premature optimizer

```
# Bad: optimizing before understanding
Make this query faster

# Good: provides baseline
This query in app/queries/active_users_query.rb takes 3.2s
on production (12M rows). The EXPLAIN output shows a seq scan
on sessions. Add the missing index and optimize the query.
```

---

## 7. Prompt Optimization Techniques

### The 5-dimension quality check

Before submitting a complex prompt, score it on:

| Dimension | Question | Target |
|-----------|----------|--------|
| **Clarity** | Is the goal unambiguous? | No room for interpretation |
| **Specificity** | Are inputs, outputs, and constraints defined? | Concrete, not abstract |
| **Context** | Does Claude have the background it needs? | Relevant files referenced |
| **Completeness** | Are success criteria stated? | "Done" is defined |
| **Structure** | Is the prompt scannable? | Uses bullets, sections, or templates |

### Chain-of-thought for complex logic

For algorithmic or multi-step reasoning:

```
Think through the authorization logic step by step:
1. What roles exist?
2. What resources does each role access?
3. What are the edge cases (owner vs admin, soft-deleted records)?
Then implement the Pundit policy.
```

### Constraint narrowing

Start broad, then narrow iteratively:

```
# Round 1: broad
Add search to the entities index page

# Round 2: narrower (after reviewing what Claude produced)
Good start. Now:
- Use a query object instead of scoping in the controller
- Support searching by name and status
- Add a debounced input handler in the React component
- Use Inertia partial reloads for filtered results
```

### The "what, not how" rule

```
# Bad (how)
Use gsub to replace all occurrences of the old domain in the config

# Good (what)
Update all references to the old domain (app.example.com) to the
new domain (app.newdomain.com) across config files
```

### Explicit scope boundaries

```
Scope: Only modify files in app/services/ and spec/services/
Do NOT change controllers, models, or views.
```

Prevents Claude from making well-intentioned but unwanted changes elsewhere.

---

## Sources

- [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Prompting Best Practices - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Prompt Engineering Overview - Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview)
- [Extend Claude with Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Skill Authoring Best Practices - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code Best Practices: Lessons From Real Projects](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/)
- [50 Claude Code Tips and Best Practices](https://www.builder.io/blog/claude-code-tips-best-practices)
- [CLAUDE.md Best Practices](https://uxplanet.org/claude-md-best-practices-1ef4f861ce7c)
- [Claude Prompt Engineering Best Practices 2026](https://promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026)
- [Claude's Context Engineering Secrets](https://01.me/en/2025/12/context-engineering-from-claude/)
- [Claude Skills and Subagents: Escaping the Prompt Engineering Hamster Wheel](https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel/)
- [prompt-architect Claude Skill](https://github.com/ckelsoe/claude-skill-prompt-architect)
- [The Complete Guide to Building Skills for Claude](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf)
- [7 Claude Code Best Practices for 2026](https://www.eesel.ai/blog/claude-code-best-practices)
- [10 Must-Have Skills for Claude in 2026](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051)
