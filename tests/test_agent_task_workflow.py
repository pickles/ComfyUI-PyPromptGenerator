import argparse
import importlib.util
import os
import shutil
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

CHECK_SCRIPT = Path(__file__).parents[1] / ".codex" / "scripts" / "check.py"
CHECK_SPEC = importlib.util.spec_from_file_location("check_script", CHECK_SCRIPT)
assert CHECK_SPEC is not None
assert CHECK_SPEC.loader is not None
CHECK_SCRIPT_MODULE = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(CHECK_SCRIPT_MODULE)


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


def test_check_uses_runner_system_temp_and_removes_only_child(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    (root / ".codex" / "handoffs" / "2026-07-25" / "task-001").mkdir(
        parents=True
    )
    system_temp = tmp_path / "system-temp"
    system_temp.mkdir()
    monkeypatch.setenv("CODEX_SYSTEM_TEMP", str(system_temp))
    base_temp = CHECK_SCRIPT_MODULE.pytest_base_temp(root)

    assert base_temp.name == "pytest"
    assert base_temp.parent.parent == system_temp.resolve()
    assert base_temp.parent.name.startswith("codex-check-")

    base_temp.mkdir(parents=True)
    sibling = base_temp.parent / "keep.txt"
    sibling.write_text("keep", encoding="utf-8")
    CHECK_SCRIPT_MODULE.remove_pytest_base_temp(base_temp)

    assert not base_temp.exists()
    assert sibling.exists()


def test_check_temp_name_includes_execution_principal(tmp_path, monkeypatch):
    monkeypatch.setattr(CHECK_SCRIPT_MODULE, "execution_identity", lambda: "DOM\\sandbox")
    monkeypatch.setenv("CODEX_SYSTEM_TEMP", str(tmp_path))

    base_temp = CHECK_SCRIPT_MODULE.pytest_base_temp(tmp_path / "repository")

    assert CHECK_SCRIPT_MODULE.short_hash("DOM\\sandbox") in base_temp.parent.name


def test_check_temp_name_stays_short_for_long_execution_identity(tmp_path, monkeypatch):
    identity = "very-long-domain-user@" + ("example." * 200) + "invalid"
    monkeypatch.setattr(CHECK_SCRIPT_MODULE, "execution_identity", lambda: identity)
    monkeypatch.setenv("CODEX_SYSTEM_TEMP", str(tmp_path))

    base_temp = CHECK_SCRIPT_MODULE.pytest_base_temp(tmp_path / "repository")

    assert len(base_temp.parent.name) <= 55
    assert identity not in str(base_temp)
    assert CHECK_SCRIPT_MODULE.short_hash(identity) in base_temp.parent.name


def test_check_temp_cleanup_retries_transient_failure(tmp_path, monkeypatch):
    target = tmp_path / "generated"
    target.mkdir()
    original_rmtree = shutil.rmtree
    calls = 0

    def transient_rmtree(path, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("temporary lock")
        original_rmtree(path, **kwargs)

    monkeypatch.setattr(CHECK_SCRIPT_MODULE.shutil, "rmtree", transient_rmtree)
    CHECK_SCRIPT_MODULE.remove_tree(target, timeout=1)

    assert calls == 2
    assert not target.exists()


def test_check_temp_cleanup_raises_for_permanent_failure(tmp_path, monkeypatch):
    target = tmp_path / "generated"
    target.mkdir()

    def permanent_rmtree(_path, **_kwargs):
        raise PermissionError("permanent lock")

    monkeypatch.setattr(CHECK_SCRIPT_MODULE.shutil, "rmtree", permanent_rmtree)
    with pytest.raises(RuntimeError, match="Unable to remove"):
        CHECK_SCRIPT_MODULE.remove_tree(target, timeout=0)
    assert target.exists()


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


def test_start_uses_ignored_primary_paths_and_creates_temp(tmp_path, monkeypatch):
    repo = init_repo(tmp_path / "repo")
    (repo / ".gitignore").write_text(
        "/.codex-worktrees/\n/.codex-tmp/\n",
        encoding="utf-8",
    )
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore task storage")
    monkeypatch.chdir(repo)
    args = argparse.Namespace(
        slug="direct-edit",
        base="main",
        date="2026-07-25",
        worktree_root=None,
    )

    TASK_WORKTREE.start(args)

    task_name = "2026-07-25-task-001-direct-edit"
    worktree = repo / ".codex-worktrees" / task_name
    temp_dir = repo / ".codex-tmp" / task_name
    assert worktree.is_dir()
    assert temp_dir.is_dir()
    assert git(repo, "status", "--porcelain") == ""


def test_run_sets_task_environment_without_shell(tmp_path, monkeypatch):
    repo = init_repo(tmp_path / "repo")
    task_id = "2026-07-25-task-001"
    slug = "run"
    branch = f"codex/{task_id}-{slug}"
    target = repo / "task-worktree"
    git(repo, "worktree", "add", "-b", branch, str(target), "main")
    temp_dir = TASK_WORKTREE.task_temp_dir(repo, task_id, slug)
    temp_dir.mkdir(parents=True)
    probe = target / "probe.py"
    probe.write_text(
        "import os, pathlib; pathlib.Path('result.txt').write_text("
        "'|'.join([os.getcwd(), os.environ['TEMP'], os.environ['TMP'], "
        "os.environ['TMPDIR'], next(value for key, value in os.environ.items() "
        "if key.startswith('GIT_CONFIG_VALUE_') and value.endswith('task-worktree'))]))",
        encoding="utf-8",
    )
    monkeypatch.chdir(repo)

    with pytest.raises(SystemExit, match="0"):
        TASK_WORKTREE.run(
            argparse.Namespace(task_id=task_id, command=["python", "probe.py"])
        )

    assert (target / "result.txt").read_text(encoding="utf-8").split("|") == [
        str(target), str(temp_dir), str(temp_dir), str(temp_dir), str(target)
    ]


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
        "TEMP_DIR": str(TASK_WORKTREE.task_temp_dir(repo, "2026-07-25-task-001", "close")),
    }
    Path(values["TEMP_DIR"]).mkdir(parents=True)
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
    assert not Path(values["TEMP_DIR"]).exists()


def test_prepare_close_rejects_tampered_temp_directory(tmp_path, monkeypatch):
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
        "TEMP_DIR": str(tmp_path / "must-not-delete"),
    }
    protected = Path(values["TEMP_DIR"])
    protected.mkdir()
    handoff = TASK_WORKTREE.create_handoff(repo, values)
    for name, old, new in (("RESULT.md", "Status: PENDING", "Status: COMPLETE"),):
        path = handoff / name
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    result = handoff / "RESULT.md"
    result.write_text(result.read_text(encoding="utf-8").replace("Validation: PENDING", "Validation: PASSED"), encoding="utf-8")
    review = handoff / "REVIEW.md"
    review.write_text(review.read_text(encoding="utf-8").replace("Verdict: PENDING", "Verdict: APPROVED"), encoding="utf-8")

    with pytest.raises(RuntimeError, match="Temp Directory"):
        TASK_WORKTREE.prepare_close(argparse.Namespace())
    assert protected.exists()


def test_prepare_close_rejects_paired_slug_and_temp_escape(tmp_path, monkeypatch):
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
        "TEMP_DIR": str(TASK_WORKTREE.task_temp_dir(repo, "2026-07-25-task-001", "close")),
    }
    handoff = TASK_WORKTREE.create_handoff(repo, values)
    outside = tmp_path / "outside"
    outside.mkdir()
    for name, replacements in {
        "HANDOFF.md": (("Slug: close", "Slug: x/../../../outside"), (values["TEMP_DIR"], str(outside))),
        "RESULT.md": (("Status: PENDING", "Status: COMPLETE"), ("Validation: PENDING", "Validation: PASSED")),
        "REVIEW.md": (("Verdict: PENDING", "Verdict: APPROVED"),),
    }.items():
        path = handoff / name
        content = path.read_text(encoding="utf-8")
        for old, new in replacements:
            content = content.replace(old, new)
        path.write_text(content, encoding="utf-8")

    with pytest.raises(RuntimeError, match="Temp Directory"):
        TASK_WORKTREE.prepare_close(argparse.Namespace())
    assert outside.exists()


def test_primary_checkout_rejects_ambiguous_separate_git_dir(tmp_path):
    repo = tmp_path / "repo"
    git_dir = tmp_path / "git-data"
    repo.mkdir()
    git(repo, "init", "--separate-git-dir", str(git_dir), "-b", "main")
    git(repo, "config", "user.email", "codex-test@example.invalid")
    git(repo, "config", "user.name", "Codex Test")
    git(repo, "commit", "--allow-empty", "-m", "initial")
    linked = tmp_path / "linked"
    git(repo, "worktree", "add", "-b", "codex/linked", str(linked), "main")

    with pytest.raises(RuntimeError, match="primary Git worktree"):
        TASK_WORKTREE.primary_checkout(linked)


def test_reserved_temp_root_rejects_external_link_or_junction(tmp_path):
    repo = init_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "marker.txt"
    marker.write_text("keep", encoding="utf-8")
    redirect = repo / ".codex-tmp"
    if os.name == "nt":
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(redirect), str(outside)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            pytest.skip("Unable to create a Windows junction")
    else:
        redirect.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="link or junction"):
        TASK_WORKTREE.reserved_temp_root(repo)
    assert marker.read_text(encoding="utf-8") == "keep"
