import argparse
import importlib.util
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).parents[1]
    / ".agents"
    / "skills"
    / "agent-task-workflow"
    / "scripts"
    / "task_worktree.py"
)
SPEC = importlib.util.spec_from_file_location("task_worktree", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
TASK_WORKTREE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TASK_WORKTREE)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def init_repo(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.email", "codex-test@example.invalid")
    git(path, "config", "user.name", "Codex Test")
    git(path, "commit", "--allow-empty", "-m", "initial")
    return path.resolve()


def test_normalize_date_rejects_non_iso_and_path_input():
    assert TASK_WORKTREE.normalize_date("2026-07-25") == "2026-07-25"

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        TASK_WORKTREE.normalize_date("../../escape")

    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        TASK_WORKTREE.normalize_date("2026-7-25")


def test_task_numbers_are_unique_during_concurrent_allocation(tmp_path):
    repo = init_repo(tmp_path / "repo")

    with ThreadPoolExecutor(max_workers=8) as executor:
        numbers = list(
            executor.map(
                lambda _index: TASK_WORKTREE.next_task_number(
                    repo,
                    "2026-07-25",
                ),
                range(16),
            )
        )

    assert sorted(numbers) == list(range(1, 17))


def test_init_handoff_rejects_detached_head(tmp_path, monkeypatch):
    repo = init_repo(tmp_path / "repo")
    git(repo, "checkout", "--detach")
    monkeypatch.chdir(repo)
    args = argparse.Namespace(
        slug="detached",
        base="main",
        date="2026-07-25",
    )

    with pytest.raises(RuntimeError, match="named branch"):
        TASK_WORKTREE.init_handoff(args)

    assert not (repo / ".codex" / "handoffs").exists()


def test_start_keeps_dirty_worktree_when_handoff_creation_fails(
    tmp_path,
    monkeypatch,
):
    repo = init_repo(tmp_path / "repo")
    worktree_root = tmp_path / "worktrees"
    target = worktree_root / "2026-07-25-task-001-rollback"
    monkeypatch.chdir(repo)

    def fail_after_write(worktree, _values):
        (worktree / "rollback-marker.txt").write_text(
            "preserve",
            encoding="utf-8",
        )
        raise RuntimeError("injected handoff failure")

    monkeypatch.setattr(TASK_WORKTREE, "create_handoff", fail_after_write)
    args = argparse.Namespace(
        slug="rollback",
        base="main",
        date="2026-07-25",
        worktree_root=str(worktree_root),
    )

    with pytest.raises(RuntimeError, match="injected"):
        TASK_WORKTREE.start(args)

    assert (target / "rollback-marker.txt").read_text(encoding="utf-8") == (
        "preserve"
    )
    assert (
        git(
            repo,
            "show-ref",
            "--verify",
            "refs/heads/codex/2026-07-25-task-001-rollback",
        )
        != ""
    )


def test_prepare_close_requires_matching_metadata_and_completed_results(
    tmp_path,
    monkeypatch,
):
    repo = init_repo(tmp_path / "repo")
    branch = "codex/2026-07-25-task-001-close"
    git(repo, "switch", "-c", branch)
    monkeypatch.chdir(repo)
    values = {
        "TASK_ID": "2026-07-25-task-001",
        "SLUG": "close",
        "CREATED_AT": "2026-07-25T00:00:00+00:00",
        "BASE": "main",
        "BRANCH": branch,
        "WORKTREE": str(repo),
    }
    handoff = TASK_WORKTREE.create_handoff(repo, values)

    with pytest.raises(RuntimeError, match="Status: COMPLETE"):
        TASK_WORKTREE.prepare_close(argparse.Namespace())

    result = handoff / "RESULT.md"
    result.write_text(
        result.read_text(encoding="utf-8")
        .replace("Status: PENDING", "Status: COMPLETE")
        .replace("Validation: PENDING", "Validation: PASSED"),
        encoding="utf-8",
    )
    review = handoff / "REVIEW.md"
    review.write_text(
        review.read_text(encoding="utf-8").replace(
            "Verdict: PENDING",
            "Verdict: APPROVED",
        ),
        encoding="utf-8",
    )
    contract = handoff / "HANDOFF.md"
    original_contract = contract.read_text(encoding="utf-8")
    contract.write_text(
        original_contract.replace(
            f"Worktree: {repo}",
            f"Worktree: {repo}-other",
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="HANDOFF.md Worktree"):
        TASK_WORKTREE.prepare_close(argparse.Namespace())

    contract.write_text(original_contract, encoding="utf-8")
    TASK_WORKTREE.prepare_close(argparse.Namespace())

    assert not handoff.exists()
