"""Manage tracked task handoffs and isolated Git worktrees."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path


TASK_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-task-\d{3,}$")


def run_git(*args: str, cwd: Path, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def repo_root(cwd: Path) -> Path:
    return Path(run_git("rev-parse", "--show-toplevel", cwd=cwd)).resolve()


def common_git_dir(root: Path) -> Path:
    value = run_git(
        "rev-parse",
        "--path-format=absolute",
        "--git-common-dir",
        cwd=root,
    )
    return Path(value).resolve()


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("slug must contain an ASCII letter or number")
    return slug[:48].rstrip("-")


def normalize_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("date must use YYYY-MM-DD") from error


def next_task_number(root: Path, task_date: str) -> int:
    registry = common_git_dir(root) / "codex-task-sequence.json"
    lock = registry.with_suffix(".lock")
    deadline = time.monotonic() + 10
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(
                lock,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            )
        except (FileExistsError, PermissionError) as error:
            if isinstance(error, PermissionError) and not lock.exists():
                raise
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Timed out waiting for task lock: {lock}")
            time.sleep(0.05)

    try:
        os.write(descriptor, str(os.getpid()).encode())
        data: dict[str, dict[str, int]] = {"dates": {}}
        if registry.exists():
            data = json.loads(registry.read_text(encoding="utf-8"))
        dates = data.setdefault("dates", {})
        number = int(dates.get(task_date, 0)) + 1
        dates[task_date] = number
        temporary = registry.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, registry)
        return number
    finally:
        os.close(descriptor)
        lock.unlink(missing_ok=True)


def render_template(name: str, values: dict[str, str]) -> str:
    asset = Path(__file__).resolve().parent.parent / "assets" / name
    content = asset.read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def create_handoff(worktree: Path, values: dict[str, str]) -> Path:
    task_date, task_number = values["TASK_ID"].rsplit("-task-", maxsplit=1)
    handoff = (
        worktree
        / ".codex"
        / "handoffs"
        / task_date
        / f"task-{task_number}"
    )
    if handoff.exists():
        raise FileExistsError(f"Handoff already exists: {handoff}")
    handoff.mkdir(parents=True)
    for template, output in (
        ("HANDOFF.template.md", "HANDOFF.md"),
        ("RESULT.template.md", "RESULT.md"),
        ("REVIEW.template.md", "REVIEW.md"),
    ):
        (handoff / output).write_text(
            render_template(template, values),
            encoding="utf-8",
        )
    return handoff


def emit(values: dict[str, str], handoff: Path) -> None:
    payload = {
        "task_id": values["TASK_ID"],
        "slug": values["SLUG"],
        "branch": values["BRANCH"],
        "base": values["BASE"],
        "worktree": values["WORKTREE"],
        "handoff": str(handoff),
    }
    print(json.dumps(payload, indent=2))


def start(args: argparse.Namespace) -> None:
    root = repo_root(Path.cwd())
    slug = normalize_slug(args.slug)
    task_date = normalize_date(args.date) if args.date else date.today().isoformat()
    worktree_root = (
        Path(args.worktree_root).resolve()
        if args.worktree_root
        else root.parent / f"{root.name}-worktrees"
    )
    number = next_task_number(root, task_date)
    task_id = f"{task_date}-task-{number:03d}"
    branch = f"codex/{task_id}-{slug}"
    worktree = (worktree_root / f"{task_id}-{slug}").resolve()
    values = {
        "TASK_ID": task_id,
        "SLUG": slug,
        "CREATED_AT": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "BASE": args.base,
        "BRANCH": branch,
        "WORKTREE": str(worktree),
    }

    if worktree.exists():
        raise FileExistsError(f"Worktree path already exists: {worktree}")
    branch_exists = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=root,
        check=False,
    )
    if branch_exists.returncode == 0:
        raise FileExistsError(f"Branch already exists: {branch}")
    worktree_root.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        run_git(
            "worktree",
            "add",
            "-b",
            branch,
            str(worktree),
            args.base,
            cwd=root,
        )
        created = True
        handoff = create_handoff(worktree, values)
    except Exception:
        if created and worktree.exists():
            if run_git("status", "--porcelain", cwd=worktree):
                print(
                    f"warning: rollback left a dirty worktree for inspection: {worktree}",
                    file=sys.stderr,
                )
            else:
                run_git(
                    "worktree",
                    "remove",
                    str(worktree),
                    cwd=root,
                    check=False,
                )
        if created and not worktree.exists():
            run_git("branch", "-D", branch, cwd=root, check=False)
        raise
    emit(values, handoff)


def init_handoff(args: argparse.Namespace) -> None:
    worktree = repo_root(Path.cwd())
    branch = run_git("branch", "--show-current", cwd=worktree)
    if not branch:
        raise RuntimeError(
            "Create a named branch in this Codex worktree before init-handoff"
        )
    slug = normalize_slug(args.slug)
    task_date = normalize_date(args.date) if args.date else date.today().isoformat()
    number = next_task_number(worktree, task_date)
    task_id = f"{task_date}-task-{number:03d}"
    values = {
        "TASK_ID": task_id,
        "SLUG": slug,
        "CREATED_AT": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "BASE": args.base,
        "BRANCH": branch,
        "WORKTREE": str(worktree),
    }
    handoff = create_handoff(worktree, values)
    emit(values, handoff)


def find_handoffs(root: Path) -> list[Path]:
    handoff_root = root / ".codex" / "handoffs"
    if not handoff_root.exists():
        return []
    return sorted(
        path.parent
        for path in handoff_root.glob("*/task-*/HANDOFF.md")
        if path.is_file()
    )


def metadata(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Za-z][A-Za-z ]*):\s*(.*?)\s*", line)
        if match:
            values.setdefault(match.group(1), match.group(2))
    return values


def prepare_close(_args: argparse.Namespace) -> None:
    root = repo_root(Path.cwd())
    branch = run_git("branch", "--show-current", cwd=root)
    if branch in {"main", "master", ""}:
        raise RuntimeError("prepare-close must run in a task worktree branch")
    handoffs = find_handoffs(root)
    if len(handoffs) != 1:
        raise RuntimeError(
            f"Expected exactly one active handoff, found {len(handoffs)}"
        )
    handoff = handoffs[0].resolve()
    expected_root = (root / ".codex" / "handoffs").resolve()
    if expected_root not in handoff.parents:
        raise RuntimeError(f"Unsafe handoff path: {handoff}")
    task_id = f"{handoff.parent.name}-{handoff.name}"
    if not TASK_PATTERN.fullmatch(task_id):
        raise RuntimeError(f"Invalid handoff task path: {handoff}")

    handoff_values = metadata(handoff / "HANDOFF.md")
    expected_handoff = {
        "Task ID": task_id,
        "Branch": branch,
        "Worktree": str(root),
    }
    for key, expected in expected_handoff.items():
        if handoff_values.get(key) != expected:
            raise RuntimeError(
                f"HANDOFF.md {key} must be {expected!r}, "
                f"found {handoff_values.get(key)!r}"
            )

    result_values = metadata(handoff / "RESULT.md")
    if result_values.get("Task ID") != task_id:
        raise RuntimeError("RESULT.md Task ID does not match the handoff")
    if result_values.get("Status") != "COMPLETE":
        raise RuntimeError("RESULT.md must contain 'Status: COMPLETE'")
    if result_values.get("Validation") != "PASSED":
        raise RuntimeError("RESULT.md must contain 'Validation: PASSED'")

    review_values = metadata(handoff / "REVIEW.md")
    if review_values.get("Task ID") != task_id:
        raise RuntimeError("REVIEW.md Task ID does not match the handoff")
    if review_values.get("Verdict") != "APPROVED":
        raise RuntimeError("REVIEW.md must contain 'Verdict: APPROVED'")
    shutil.rmtree(handoff)
    for parent in (handoff.parent, handoff.parent.parent):
        if parent.exists() and not any(parent.iterdir()):
            parent.rmdir()
    print(f"Removed approved handoff: {handoff}")
    print("Commit this deletion before merging the task branch.")


def worktrees(root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in run_git("worktree", "list", "--porcelain", cwd=root).splitlines():
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def cleanup(args: argparse.Namespace) -> None:
    if not TASK_PATTERN.fullmatch(args.task_id):
        raise ValueError("task-id must look like YYYY-MM-DD-task-NNN")
    root = repo_root(Path.cwd())
    matches = [
        entry
        for entry in worktrees(root)
        if entry.get("branch", "").startswith(
            f"refs/heads/codex/{args.task_id}-"
        )
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one worktree for {args.task_id}, found {len(matches)}"
        )
    entry = matches[0]
    target = Path(entry["worktree"]).resolve()
    if target == root:
        raise RuntimeError("Run cleanup from the local checkout, not the task worktree")
    branch_ref = entry.get("branch", "")
    branch = branch_ref.removeprefix("refs/heads/")
    if run_git("status", "--porcelain", cwd=target):
        raise RuntimeError(f"Worktree is dirty: {target}")
    merged = subprocess.run(
        ["git", "merge-base", "--is-ancestor", branch, args.base],
        cwd=root,
        check=False,
    )
    if merged.returncode != 0:
        raise RuntimeError(f"Branch {branch} is not merged into {args.base}")
    run_git("worktree", "remove", str(target), cwd=root)
    run_git("branch", "-d", branch, cwd=root)
    print(f"Removed worktree: {target}")
    print(f"Deleted merged local branch: {branch}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    start_parser = commands.add_parser("start")
    start_parser.add_argument("--slug", required=True)
    start_parser.add_argument("--base", default="main")
    start_parser.add_argument("--date")
    start_parser.add_argument("--worktree-root")
    start_parser.set_defaults(handler=start)

    init_parser = commands.add_parser("init-handoff")
    init_parser.add_argument("--slug", required=True)
    init_parser.add_argument("--base", default="main")
    init_parser.add_argument("--date")
    init_parser.set_defaults(handler=init_handoff)

    close_parser = commands.add_parser("prepare-close")
    close_parser.set_defaults(handler=prepare_close)

    cleanup_parser = commands.add_parser("cleanup")
    cleanup_parser.add_argument("--task-id", required=True)
    cleanup_parser.add_argument("--base", default="main")
    cleanup_parser.set_defaults(handler=cleanup)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
