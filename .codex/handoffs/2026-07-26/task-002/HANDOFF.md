# Development handoff

Task ID: 2026-07-26-task-002
Slug: automate-worktree-temp
Created: 2026-07-26T00:28:43+00:00
State: READY
Base: main
Branch: codex/2026-07-26-task-002-automate-worktree-temp
Worktree: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator\.cache\codex-worktrees\2026-07-26-task-002-automate-worktree-temp
Temp Directory: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator\.codex-tmp\2026-07-26-task-002-automate-worktree-temp

## Objective

Make task Worktree and temporary-directory lifecycle automatic. A normal
`start` must create a directly writable, Git-ignored Worktree and a reserved
task temp directory inside the primary checkout. Agents must be able to run
commands in it without manual staging copies, `safe.directory` flags, or
TEMP/TMP setup. Approved close and cleanup must safely remove reserved temp
data.

## Non-goals

- Do not weaken Git safe-directory checks globally.
- Do not force-remove dirty Worktrees.
- Do not delete arbitrary user temp directories.
- Do not change product behavior or dependency setup.
- Keep `--worktree-root` as an explicit override.

## Evidence and constraints

- The current default sibling Worktree is outside the active workspace writable
  root, forcing a manual `.task-staging` mirror.
- New Worktrees also trigger Git dubious-ownership checks for the
  `CodexSandboxOffline` process.
- Shared pytest temp storage has produced Windows ACL failures; deep temp paths
  can also exceed Windows path limits.
- `.cache/` proved that nested ignored Worktrees are writable, but it is not a
  stable public location.
- `task_worktree.py` already owns start, close, and cleanup safety boundaries.

## Design

1. Reserve `/.codex-worktrees/` and `/.codex-tmp/` in `.gitignore`.
2. Default `start` to `<primary-checkout>/.codex-worktrees/<task-id>-<slug>`.
   Derive the primary checkout from the common Git directory so invocation from
   a linked Worktree remains deterministic. Preserve `--worktree-root`.
3. Create `<primary-checkout>/.codex-tmp/<task-id>-<slug>` during `start` and
   `init-handoff`. Add `TEMP_DIR` to templates, JSON output, and handoff
   metadata.
4. Add `run --task-id ... -- <argv>` to locate exactly one task Worktree and
   execute without a shell. Inject a command-scoped Git `safe.directory`
   config plus `TEMP`, `TMP`, and `TMPDIR`; set cwd to the task Worktree.
5. Make `check.py` use `<task-temp>/pytest` as explicit `--basetemp` when a
   matching handoff exists, otherwise use a reserved local temp path. Clean
   only that pytest child in `finally`.
6. `prepare-close` validates the handoff Temp Directory against the reserved
   path, removes it, then removes the approved handoff.
7. `cleanup` independently removes the exact reserved task temp path if it
   still exists, after dirty/merged checks and before Worktree removal.
8. Centralize containment checks. Never follow an arbitrary handoff path for
   deletion without equality to the derived reserved path.
9. Update workflow docs to require direct Worktree edits and the `run` helper;
   prohibit staging mirrors for normal tasks.

## Change boundaries

Allowed paths:

- `.gitignore`
- `.agents/skills/agent-task-workflow/SKILL.md`
- `.agents/skills/agent-task-workflow/scripts/task_worktree.py`
- `.agents/skills/agent-task-workflow/assets/HANDOFF.template.md`
- `.codex/scripts/check.py`
- `AGENTS.md`
- `tests/test_agent_task_workflow.py`
- `.codex/handoffs/2026-07-26/task-002/*`

Do not change product source, product tests, sample scripts, remote Git state,
or unrelated ignored user data.

## Acceptance criteria

- [ ] Default Worktree is inside `/.codex-worktrees/` and invisible to parent
      `git status`.
- [ ] Start/init create and emit an exact reserved task temp path.
- [ ] `run` injects cwd, safe.directory, TEMP, TMP, and TMPDIR without a shell.
- [ ] Agents can edit the Worktree directly; no staging mirror is needed.
- [ ] `check.py` uses and cleans a task-local pytest basetemp.
- [ ] Close rejects tampered Temp Directory metadata.
- [ ] Approved close and merged cleanup remove only the reserved temp path.
- [ ] Dirty/unmerged Worktree protections and explicit root override remain.
- [ ] Windows/concurrent lifecycle regression tests pass.

## Validation

- [ ] `python -m ruff check .`
- [ ] `python -m pytest tests/ -q`
- [ ] Start/run/close/merge/cleanup lifecycle in a temporary repository.
- [ ] Confirm parent checkout remains clean while nested Worktree is active.

## Delegation

Coding agent:

- Implement this design without expanding scope.
- Edit the Worktree directly and update `RESULT.md`.

Reviewer agent:

- Review the implementation against this handoff.
- Report concrete findings with file and line references.
- Verify every recursive deletion target is derived and contained.

## Decision log

- 2026-07-26T00:28:43+00:00: Task initialized.
- 2026-07-26: Reproduced writable-root and Git safe.directory failures.
- 2026-07-26: Selected repository-local ignored storage plus command-scoped
  environment injection; rejected global safe.directory weakening.
