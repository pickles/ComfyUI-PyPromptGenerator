---
name: agent-task-workflow
description: Coordinate non-trivial repository changes through an orchestrator, coder, and reviewer using a tracked handoff and an isolated Git worktree. Use when planning or implementing a feature, fix, refactor, or review that benefits from role separation, parallel task isolation, or a durable design contract. Do not use for read-only questions or tiny single-file edits.
---

# Agent Task Workflow

Keep the primary context focused on decisions. Put detailed design and task state
in the handoff, implementation logs in `RESULT.md`, and review evidence in
`REVIEW.md`.

## Start a task

1. Inspect the request and repository before creating files.
2. Run:

   ```powershell
   python .agents/skills/agent-task-workflow/scripts/task_worktree.py start --slug <short-slug> --base main
   ```

3. Use the JSON output as the source of truth for `task_id`, `branch`,
   `worktree`, and `handoff`.
4. Complete every required section in `HANDOFF.md` before delegating.
5. Keep each task in its own worktree. Never let two agents write to the same
   worktree concurrently.

When the chat already runs in a Codex-managed worktree, first click
**Create branch here** in Codex. Then create the handoff there instead of
nesting another worktree:

```powershell
python .agents/skills/agent-task-workflow/scripts/task_worktree.py init-handoff --slug <short-slug> --base main
```

`init-handoff` refuses detached HEAD so the task always has a mergeable,
uniquely owned branch.

## Delegate

1. Give the `coding` agent the absolute worktree and handoff paths.
2. Tell it to implement only the approved design, run scoped checks, and update
   `RESULT.md` to `Status: COMPLETE` and `Validation: PASSED` only after all
   required checks pass.
3. Wait for coding to finish before starting review.
4. Give the `reviewer` agent the same paths and the diff base.
5. Ask for correctness, regression, security, and test findings against the
   acceptance criteria.
6. Record its verdict and evidence in `REVIEW.md`.
7. Return actionable findings to `coding`; allow at most two correction cycles
   before escalating design uncertainty to the user.

Use parallel agents only for independent tasks in separate worktrees or
read-only investigation. Do not parallelize dependent coding and review stages.

## Close a task

Require all of the following:

- `RESULT.md` contains `Status: COMPLETE` and `Validation: PASSED`, and lists
  changed files and successful checks.
- `REVIEW.md` contains `Verdict: APPROVED`.
- The task branch is committed and ready to publish.

Remove the handoff before the final task-branch commit:

```powershell
python .agents/skills/agent-task-workflow/scripts/task_worktree.py prepare-close
```

Commit the deletion, push, open a PR, wait for CI, and merge only when the user
explicitly authorizes each applicable Git or GitHub action. Without that
authorization, leave the local branch and working tree ready for the user. Use
a merge commit when preserving the intermediate handoff history matters.

After an authorized merge, run from the local checkout:

```powershell
python .agents/skills/agent-task-workflow/scripts/task_worktree.py cleanup --task-id <YYYY-MM-DD-task-NNN> --base main
```

The cleanup command refuses dirty or unmerged worktrees. For a Codex-managed
worktree, archive the completed chat after merge and let Codex remove the
managed worktree.

## Guardrails

- Do not delete a handoff before result validation and review approval.
- Do not force-remove a dirty worktree.
- Do not reuse a task branch in multiple worktrees.
- Do not silently expand the handoff scope; update the design and decision log
  first.
- Preserve user changes and unrelated worktrees.
