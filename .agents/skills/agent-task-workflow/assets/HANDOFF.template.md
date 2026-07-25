# Development handoff

Task ID: {{TASK_ID}}
Slug: {{SLUG}}
Created: {{CREATED_AT}}
State: DESIGN
Base: {{BASE}}
Branch: {{BRANCH}}
Worktree: {{WORKTREE}}

## Objective

<!-- State the user-visible outcome. -->

## Non-goals

<!-- List adjacent work that must remain unchanged. -->

## Evidence and constraints

<!-- Cite relevant files, symbols, behavior, and compatibility constraints. -->

## Design

<!-- Describe interfaces, data flow, edge cases, and migration behavior. -->

## Change boundaries

Allowed paths:

- <!-- path -->

Do not change:

- <!-- path or behavior -->

## Acceptance criteria

- [ ] <!-- observable criterion -->

## Validation

- [ ] `python -m ruff check .`
- [ ] `python -m pytest tests/ -q`
- [ ] <!-- task-specific check -->

## Delegation

Coding agent:

- Implement this design without expanding scope.
- Update `RESULT.md`.

Reviewer agent:

- Review the implementation against this handoff.
- Report concrete findings with file and line references.

## Decision log

- {{CREATED_AT}}: Task initialized.
