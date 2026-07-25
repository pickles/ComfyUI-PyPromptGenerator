# Repository agent instructions

## Project

- This is a Python 3.10+ ComfyUI custom node.
- Source lives in `src/pyprompt_generator/`.
- Tests live in `tests/`.
- Tracked examples live in `sample_scripts/`; `scripts/` is ignored user data.
- Preserve unrelated user changes, especially files under ignored directories.

## Setup and verification

- Initialize a fresh checkout or worktree with:
  `python .codex/scripts/setup_worktree.py`
- Run the required checks with:
  `python .codex/scripts/check.py`
- The completion bar is Ruff passing, all tests passing, and the task-specific
  acceptance criteria being demonstrated.

## Agent workflow

Use the `agent-task-workflow` skill for non-trivial features, fixes, refactors,
or reviews. Tiny, low-risk edits and read-only questions may stay in one agent.

1. Delegate design and coordination to the `orchestration` agent.
2. `orchestration` creates the isolated task worktree and completes the tracked
   handoff before implementation begins.
3. Delegate implementation to `coding`.
4. After coding and scoped checks finish, delegate review to `reviewer`.
5. Return concrete findings to `coding`; do not let review and coding write in
   the same worktree concurrently.
6. Close the handoff only after approval and successful checks.
7. Push, open a PR, or merge only when the user explicitly authorizes it.
   Otherwise, stop with the local task branch ready for the user.
8. After an authorized merge, clean up the task worktree.

Keep raw exploration, logs, and implementation details out of the primary
thread. Return concise evidence and decisions from subagents.

## Handoffs and worktrees

- Store active handoffs under
  `.codex/handoffs/YYYY-MM-DD/task-NNN/`.
- Track handoffs on the task branch while work is active.
- Remove the task handoff before the final task-branch commit. Use merge commits
  when preserving the intermediate handoff history matters.
- Use one branch and one worktree per task.
- Parallelize independent tasks only when they use different worktrees.
- Never force-remove a dirty or unmerged worktree.
- Prefer Codex-managed Worktree chats for interactive background work. Use the
  lifecycle script when an orchestrated task needs deterministic paths.

## Engineering conventions

- Keep changes scoped to the approved handoff.
- Add or update tests for behavior changes.
- Preserve backward compatibility unless the handoff explicitly changes it.
- Use `rg` for search and `apply_patch` for edits.
- Do not commit, push, merge, or delete remote data unless the user requests it.
- Reviewer output must prioritize correctness, regressions, security, and
  missing tests over style-only feedback.
