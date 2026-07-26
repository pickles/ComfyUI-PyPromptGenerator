# Development handoff

Task ID: 2026-07-26-task-003
Slug: harden-partial-worktree-cleanup
Created: 2026-07-26T02:01:58+00:00
State: DESIGN
Base: main
Branch: codex/2026-07-26-task-003-harden-partial-worktree-cleanup
Worktree: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator\.codex-worktrees\2026-07-26-task-003-harden-partial-worktree-cleanup
Temp Directory: D:\tools\StabilityMatrix-win-x64\Data\Packages\ComfyUI\custom_nodes\ComfyUI-PyPromptGenerator\.codex-tmp\2026-07-26-task-003-harden-partial-worktree-cleanup

## Objective

Make `task_worktree.py cleanup` recover safely when `git worktree remove`
partially succeeds: improve removal reliability for clean worktrees containing
read-only entries, distinguish a still-registered failure from an unregistered
filesystem residue, remove only an exact task directory under the canonical
reserved worktree root, and delete the merged branch only after the worktree
target is gone.

## Non-goals

- Do not change task creation, handoff initialization, task command execution,
  close preparation, merge checks, dirty-worktree refusal, or temp-directory
  cleanup semantics except for sharing an internal bounded removal helper where
  useful.
- Do not force-remove a registered worktree or delete an unmerged/dirty
  worktree.
- Do not recursively delete a worktree created under an explicit external
  `--worktree-root`; a residual external directory always requires manual
  cleanup.
- Do not change product code under `src/`, tracked examples, documentation, or
  unrelated tests.

## Evidence and constraints

- `.agents/skills/agent-task-workflow/scripts/task_worktree.py::cleanup`
  currently validates a unique task worktree, cleanliness, and ancestry, removes
  the reserved task temp directory, then calls `git worktree remove` followed
  immediately by `git branch -d`. It does not inspect state after a remove
  failure.
- The measured Windows failure occurred after dirty/merged/temp checks passed:
  `git worktree remove` exited 255, Git removed the worktree registration, but
  the filesystem directory remained because contents had mixed access/read-only
  state. The local task branch therefore also remained. Manual recovery required
  deleting the residue as the normal sandbox identity and deleting the branch
  through elevated Git.
- `reserved_worktree_root(root)` already anchors `.codex-worktrees` to the
  canonical primary checkout and rejects a redirected root.
- `make_writable` and `remove_reserved_task_temp` already provide read-only
  recovery and bounded retry behavior for an exact derived reserved temp path.
  Worktree residue removal should reuse/generalize these mechanics rather than
  introduce unbounded retries.
- `start --worktree-root ...` intentionally permits worktrees outside the
  canonical reserved root. That override is trusted for Git worktree use, but
  not as authorization for recursive deletion after Git has unregistered it.
- Python 3.10+ and Windows remain supported. Attribute normalization must
  preserve existing mode bits and must not follow symlinks, junctions, or other
  link-like children outside the worktree.
- Preserve unrelated user changes and ignored-directory contents. Only the
  exact target derived from the selected task id and branch slug may be
  considered for automatic residue removal.

## Design

1. Add a derived reserved-worktree target check analogous to the reserved temp
   path check. The only auto-removable worktree residue is:
   `reserved_worktree_root(root) / f"{task_id}-{slug}"`, after resolution, with
   its parent exactly equal to the validated canonical reserved worktree root.
   Comparing only a common prefix, accepting a descendant, or trusting the path
   returned by stale metadata is insufficient.
2. After the existing task-id, unique registration, clean-status, merge, branch,
   and slug validations succeed, normalize read-only attributes inside the
   clean registered target before invoking `git worktree remove`. Preserve all
   existing mode bits while adding owner-write permission where needed. Include
   the target directory itself, do not traverse/follow link-like entries, and
   fail before Git removal with an actionable error if safe normalization cannot
   be completed. This applies to the selected registered worktree even when it
   came from an explicit external root; it is not recursive deletion.
3. Keep the normal success path: if `git worktree remove <target>` returns
   successfully and the target no longer exists, delete the already-validated
   merged branch with `git branch -d`.
4. If `git worktree remove` raises/fails, immediately refresh
   `git worktree list --porcelain`. Match conservatively against both the
   original resolved target and original branch ref:
   - If either still appears in a refreshed entry, report that the worktree is
     still registered, preserve its branch, and do not invoke recursive
     deletion.
   - If neither appears, Git removal partially succeeded. Inspect the original
     target on disk.
5. For partial success where the target still exists:
   - If it is the exact derived task directory directly under the canonical
     `reserved_worktree_root`, remove the residue using the existing
     read-only callback and bounded retry behavior (a shared internal bounded
     tree-removal helper is acceptable). If retries expire, raise an actionable
     residual-cleanup error and preserve the branch.
   - If it is any external override or otherwise not the exact canonical task
     directory, do not call `shutil.rmtree`. Raise a specific error naming the
     residual target, stating that Git registration is gone, manual filesystem
     cleanup is required, and the branch was preserved.
6. Once the original target is confirmed absent, whether because Git removal
   succeeded, Git failed after removing both registration and directory, or
   bounded reserved-residue recovery succeeded, proceed to `git branch -d`.
   Never delete the branch while the refreshed registration remains or the
   target still exists.
7. Preserve the original Git failure as exception context or include its stderr
   in the actionable error without exposing unrelated environment data. Do not
   convert a registered failure or refused external residue into a success
   message.
8. Add focused tests in `tests/test_agent_task_workflow.py`:
   - Full success: a clean registered task worktree with read-only content is
     made writable, Git removal succeeds, the target disappears, and branch
     deletion follows.
   - Registered failure: simulated `git worktree remove` failure plus a refreshed
     entry for the original target/branch raises, does not recursively delete,
     and does not delete the branch.
   - Partial reserved recovery: simulated remove failure after registration
     disappears leaves the exact reserved task directory; bounded/read-only
     cleanup removes it and branch deletion follows. Exercise a transient
     deletion failure so retry behavior is observable.
   - External refusal: the same partial state for an explicit external
     worktree target raises a concrete manual-cleanup error, leaves the directory
     and branch intact, and never calls recursive deletion.
   Tests must also retain the existing reserved temp cleanup coverage and avoid
   depending on administrator privileges or platform-specific ACL setup.

## Change boundaries

Allowed paths:

- `.agents/skills/agent-task-workflow/scripts/task_worktree.py`
- `tests/test_agent_task_workflow.py`
- `.codex/handoffs/2026-07-26/task-003/HANDOFF.md`
- `.codex/handoffs/2026-07-26/task-003/RESULT.md`
- `.codex/handoffs/2026-07-26/task-003/REVIEW.md`

Do not change:

- `src/`, `sample_scripts/`, `scripts/`, project configuration, or any file not
  listed above.
- Existing cleanup gates for invalid task ids, ambiguous task matches, running
  cleanup from the task worktree, dirty state, unmerged branches, malformed task
  branch names, and reserved temp validation.
- The rule that `git branch -d` is used only after successful merge validation
  and complete worktree target removal.

## Acceptance criteria

- [ ] Clean worktree contents have read-only attributes safely normalized before
  `git worktree remove`, without following link-like entries or clearing
  unrelated mode bits.
- [ ] A successful Git removal with no target residue deletes the merged task
  branch and reports normal completion.
- [ ] A failed Git removal always triggers a fresh worktree-list query.
- [ ] If the refreshed registration still contains the original target or
  branch, cleanup raises and neither recursive deletion nor branch deletion is
  attempted.
- [ ] If registration disappeared but the exact canonical reserved task
  directory remains, bounded read-only-aware removal is attempted; branch
  deletion occurs only after the directory is confirmed absent.
- [ ] If registration disappeared but an external/otherwise non-exact target
  remains, cleanup refuses automatic recursive deletion, names the residual
  path and manual action required, and preserves the branch.
- [ ] Permanent reserved residue deletion failure preserves the branch and
  returns an actionable error.
- [ ] Tests cover full success, still-registered failure, partial reserved
  recovery, and external residue refusal without privileged setup.
- [ ] Existing agent task workflow tests continue to pass.

## Validation

- [ ] `python -m ruff check .`
- [ ] `python -m pytest tests/ -q`
- [ ] `python -m pytest tests/test_agent_task_workflow.py -q`
- [ ] `python .codex/scripts/check.py`

## Delegation

Coding agent:

- Work only in the task worktree named above.
- Implement this design without expanding scope or weakening cleanup safety
  gates.
- Run the scoped workflow tests first, then the required repository check.
- Update `RESULT.md` with exact changed files, validation commands, and outcomes.

Reviewer agent:

- Begin only after coding and scoped checks finish.
- Review correctness, regressions, deletion-boundary safety, branch preservation,
  link handling, failure messages, and test completeness against this handoff.
- Report concrete findings with file and line references in `REVIEW.md`.

## Decision log

- 2026-07-26T02:01:58+00:00: Task initialized.
- 2026-07-26: Recorded the measured partial-cleanup failure: Git registration
  disappeared while a mixed-access filesystem residue and the task branch
  remained.
- 2026-07-26: Chose refreshed Git registration as the first recovery boundary.
  A still-registered target or branch is never recursively removed.
- 2026-07-26: Limited automatic partial-success residue deletion to the exact
  derived task directory directly under the canonical reserved worktree root.
  External override residues require manual cleanup.
- 2026-07-26: Required branch deletion to remain last, after both registration
  and filesystem target are absent.
