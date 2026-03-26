---
name: feature
description: >-
  Orchestrates the full feature lifecycle: specification, review, planning, and
  implementation using TDD. Use when the user wants to build a complete feature
  end-to-end, or mentions feature workflow, feature lifecycle, or full feature.
  WHEN NOT: Running a single phase (use /feature-spec, /feature-review,
  /feature-plan, or specialist agents directly).
user-invocable: true
disable-model-invocation: true
argument-hint: "[feature name or spec file path]"
---

# Feature Lifecycle Orchestrator

You guide the user through the complete feature development lifecycle, phase by phase.

## Workflow

### Phase 1: Specification

Run `/feature-spec $ARGUMENTS` to create or refine the feature specification.

Wait for the user to review and confirm the spec before proceeding.

### Phase 2: Review

Run `/feature-review` on the generated spec file.

The review must score >= 7/10 and reach "Ready for Development" status. If it doesn't:
- Show the user the gaps identified
- Ask if they want to refine the spec (loop back to Phase 1)
- Or proceed despite the score (with acknowledgment)

### Phase 3: Planning

Run `/feature-plan` on the reviewed spec file.

Present the implementation plan with PR breakdown to the user. Wait for approval before proceeding.

### Phase 4: Implementation

Execute the plan using TDD for each PR:

1. **RED:** Use `@rspec-agent` to write failing tests from the Gherkin scenarios
2. **GREEN:** Use `@implementation-agent` to make tests pass (it delegates to specialist subagents)
3. **REFACTOR:** Use `@tdd-refactoring-agent` to clean up the implementation

Repeat for each PR in the plan.

### Phase 5: Final Verification

After all PRs are implemented:
- Run `bundle exec rspec` (full suite)
- Run `bundle exec rubocop -a` (linting)
- Run `bin/brakeman --no-pager` (security)
- Report completion with summary of what was built

## Phase Transitions

Always pause between phases for user confirmation:
- After spec: "Spec ready. Proceed to review?"
- After review: "Review score X/10. Proceed to planning?"
- After plan: "Plan has N PRs. Proceed to implementation?"
- After each PR: "PR #N complete (tests green). Continue to PR #N+1?"

## Guidelines

- Never skip phases -- each builds on the previous one
- Always wait for user confirmation at phase transitions
- If a phase produces unsatisfactory results, offer to re-run it
- Track progress explicitly so the user always knows which phase and PR they're in
