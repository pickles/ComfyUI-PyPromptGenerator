# Development handoff

Task ID: 2026-07-26-task-001
Slug: conditional-chain-scope
Created: 2026-07-25T23:57:46+00:00
State: READY
Base: main
Branch: codex/2026-07-26-task-001-conditional-chain-scope
Worktree: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator-worktrees\2026-07-26-task-001-conditional-chain-scope

## Objective

Every directly chained `dimension()` after one `when()` must share that
condition for both block- and program-scoped declarations. For A/B branches,
an A scene must contain A1/A2 only and a B scene must contain B1/B2 only.

## Non-goals

- Do not change matching, synthesis, ordering, weighting, rendering, or scope.
- Do not change `require()` or `forbid()`.
- Do not store persistent pending-condition state on a block or program.
- A separate later `girl.dimension()` remains unconditional.

## Evidence and constraints

`ConstraintBuilder.dimension()` currently registers one conditional dimension
and returns its `PromptBlock` or `PromptProgram`. The next chained
`.dimension()` therefore calls the owner's unconditional method. Conditional
matching and expansion are already correct.

## Design

Add an internal expression-local `ConditionalDimensionChain` proxy. Factor the
existing registration logic into a builder helper. The first and every
subsequent chain `dimension()` register through the same builder and condition,
returning the chain. Delegate other attributes narrowly through `__getattr__`
to the original owner. Thus `.fixed(...)` or another owner method exits the
conditional chain using its existing return value, and a following owner
`dimension()` remains unconditional. Preserve reusable Dimension validation.

## Change boundaries

Allowed paths:

- `sample_scripts/prompt_cdk.py`
- `tests/test_prompt_cdk.py`
- `sample_scripts/README.md`
- `.codex/handoffs/2026-07-26/task-001/RESULT.md`
- `.codex/handoffs/2026-07-26/task-001/REVIEW.md`

Do not modify `src/`, other tests/samples, synthesis internals, or user scripts.

## Acceptance criteria

- [ ] Block A/B branches with two directly chained dimensions never leak.
- [ ] Selection, summary, and prompt output all reflect the active branch.
- [ ] Program-scoped chained conditional dimensions behave the same way.
- [ ] Block names retain their prefix and program names remain global.
- [ ] Reusable Dimensions work in a conditional chain.
- [ ] Owner continuation exits the chain; its later dimension is unconditional.
- [ ] Existing single conditional and overlapping-branch behavior passes.
- [ ] README explains chained conditions and how to leave the chain.

## Validation

- [ ] `python -m pytest tests/test_prompt_cdk.py -q`
- [ ] `python -m ruff check .`
- [ ] `python .codex/scripts/check.py`

## Delegation

Coding updates RESULT.md to COMPLETE/PASSED after all checks. Reviewer confirms
the condition cannot leak into a separate owner statement and records an
APPROVED verdict only when no actionable findings remain.

## Decision log

- 2026-07-26: Root cause isolated to `ConstraintBuilder.dimension()` return.
- 2026-07-26: Chose an expression-local proxy over persistent owner state.
