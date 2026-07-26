"""Manage tracked task handoffs and isolated Git worktrees."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
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


def primary_checkout(root: Path) -> Path:
    """Return Git's primary worktree, including separate-git-dir repositories."""
    entries = worktrees(root)
    if not entries or "worktree" not in entries[0]:
        raise RuntimeError("Unable to identify the primary Git worktree")
    primary = Path(entries[0]["worktree"]).resolve()
    if (primary / ".git").exists():
        return primary
    separate_worktree = run_git(
        "config", "--path", "--get", "core.worktree", cwd=root, check=False
    )
    if separate_worktree:
        candidate = Path(separate_worktree).resolve()
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError("Unable to identify the primary Git worktree")


def reserved_worktree_root(root: Path) -> Path:
    return reserved_root(root, ".codex-worktrees")


def reserved_temp_root(root: Path) -> Path:
    return reserved_root(root, ".codex-tmp")


def reserved_root(root: Path, name: str) -> Path:
    """Reject reserved storage redirected outside the canonical primary checkout."""
    lexical = primary_checkout(root).resolve() / name
    if lexical.resolve() != lexical:
        raise RuntimeError(f"Reserved path must not be a link or junction: {lexical}")
    return lexical


def task_temp_dir(root: Path, task_id: str, slug: str) -> Path:
    if not TASK_PATTERN.fullmatch(task_id):
        raise ValueError("task-id must look like YYYY-MM-DD-task-NNN")
    if slug != normalize_slug(slug):
        raise ValueError("slug must be normalized")
    reserved_root = reserved_temp_root(root).resolve()
    candidate = (reserved_root / f"{task_id}-{slug}").resolve()
    if candidate.parent != reserved_root:
        raise RuntimeError("Task temp path is outside the reserved temp root")
    return candidate


def is_exact_reserved_temp(root: Path, task_id: str, slug: str, value: str) -> bool:
    """Accept only the derived task temp path, never an arbitrary metadata path."""
    try:
        return Path(value).resolve() == task_temp_dir(root, task_id, slug)
    except ValueError:
        return False


def task_worktree_dir(root: Path, task_id: str, slug: str) -> Path:
    """Return the one task directory that may be recovered automatically."""
    if not TASK_PATTERN.fullmatch(task_id):
        raise ValueError("task-id must look like YYYY-MM-DD-task-NNN")
    if slug != normalize_slug(slug):
        raise ValueError("slug must be normalized")
    reserved_root = reserved_worktree_root(root).resolve()
    candidate = (reserved_root / f"{task_id}-{slug}").resolve()
    if candidate.parent != reserved_root:
        raise RuntimeError("Task worktree path is outside the reserved worktree root")
    return candidate


def is_exact_reserved_worktree(root: Path, task_id: str, slug: str, value: Path) -> bool:
    """Accept only the direct derived child of the canonical reserved root."""
    try:
        return value.resolve() == task_worktree_dir(root, task_id, slug)
    except ValueError:
        return False


def is_link_like(path: Path) -> bool:
    """Identify entries that must not be traversed while changing attributes."""
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_point)


def add_owner_write(path: Path) -> None:
    """Add owner-write without changing any other mode bits or following links."""
    mode = stat.S_IMODE(path.lstat().st_mode)
    path.chmod(mode | stat.S_IWUSR, follow_symlinks=False)


def make_tree_writable(target: Path) -> None:
    """Normalize a clean worktree without traversing symlinks or junctions."""
    if is_link_like(target):
        raise RuntimeError(f"Refusing to normalize link-like worktree target: {target}")
    try:
        for current, directories, files in os.walk(target, followlinks=False):
            current_path = Path(current)
            add_owner_write(current_path)
            link_directories = [
                name for name in directories if is_link_like(current_path / name)
            ]
            directories[:] = [name for name in directories if name not in link_directories]
            for name in [*directories, *files]:
                child = current_path / name
                if not is_link_like(child):
                    add_owner_write(child)
    except OSError as error:
        raise RuntimeError(f"Unable to make clean worktree writable: {target}") from error


def make_writable(function, path: str, _exception: object) -> None:
    add_owner_write(Path(path))
    function(path)


def remove_reserved_task_temp(
    root: Path, task_id: str, slug: str, timeout: float = 8.0
) -> None:
    """Safely remove only a derived task temp directory with bounded retries."""
    target = task_temp_dir(root, task_id, slug)
    deadline = time.monotonic() + timeout
    while target.exists():
        try:
            shutil.rmtree(target, onerror=make_writable)
        except OSError as error:
            if not target.exists():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Unable to remove reserved task temp directory: {target}"
                ) from error
            time.sleep(0.1)


def remove_reserved_task_worktree(
    root: Path, task_id: str, slug: str, timeout: float = 8.0
) -> None:
    """Safely remove only the exact derived reserved worktree residue."""
    target = task_worktree_dir(root, task_id, slug)
    deadline = time.monotonic() + timeout
    while target.exists():
        try:
            shutil.rmtree(target, onerror=make_writable)
        except OSError as error:
            if not target.exists():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Unable to remove reserved task worktree residue: {target}"
                ) from error
            time.sleep(0.1)


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
        "temp_dir": values["TEMP_DIR"],
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
        else reserved_worktree_root(root)
    )
    number = next_task_number(root, task_date)
    task_id = f"{task_date}-task-{number:03d}"
    branch = f"codex/{task_id}-{slug}"
    worktree = (worktree_root / f"{task_id}-{slug}").resolve()
    temp_dir = task_temp_dir(root, task_id, slug)
    values = {
        "TASK_ID": task_id,
        "SLUG": slug,
        "CREATED_AT": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "BASE": args.base,
        "BRANCH": branch,
        "WORKTREE": str(worktree),
        "TEMP_DIR": str(temp_dir),
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
    if temp_dir.exists():
        raise FileExistsError(f"Task temp path already exists: {temp_dir}")
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
        temp_dir.mkdir(parents=True)
        handoff = create_handoff(worktree, values)
    except Exception:
        if temp_dir.exists():
            remove_reserved_task_temp(root, task_id, slug)
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
    temp_dir = task_temp_dir(worktree, task_id, slug)
    if temp_dir.exists():
        raise FileExistsError(f"Task temp path already exists: {temp_dir}")
    values = {
        "TASK_ID": task_id,
        "SLUG": slug,
        "CREATED_AT": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "BASE": args.base,
        "BRANCH": branch,
        "WORKTREE": str(worktree),
        "TEMP_DIR": str(temp_dir),
    }
    temp_dir.mkdir(parents=True)
    try:
        handoff = create_handoff(worktree, values)
    except Exception:
        remove_reserved_task_temp(worktree, task_id, slug)
        raise
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
    slug = handoff_values.get("Slug", "")
    temp_metadata = handoff_values.get("Temp Directory", "")
    if not is_exact_reserved_temp(root, task_id, slug, temp_metadata):
        raise RuntimeError("HANDOFF.md Temp Directory is not the reserved task path")
    temp_dir = task_temp_dir(root, task_id, slug)

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
    if temp_dir.exists():
        remove_reserved_task_temp(root, task_id, slug)
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
    slug = branch.removeprefix(f"codex/{args.task_id}-")
    if not slug or "/" in slug:
        raise RuntimeError(f"Invalid task branch: {branch}")
    temp_dir = task_temp_dir(root, args.task_id, slug)
    if temp_dir.exists():
        remove_reserved_task_temp(root, args.task_id, slug)
    make_tree_writable(target)
    try:
        run_git("worktree", "remove", str(target), cwd=root)
    except subprocess.CalledProcessError as error:
        refreshed = worktrees(root)
        still_registered = any(
            Path(current["worktree"]).resolve() == target
            or current.get("branch") == branch_ref
            for current in refreshed
            if "worktree" in current
        )
        if still_registered:
            raise RuntimeError(
                f"Git worktree removal failed and the worktree remains registered: {target}"
            ) from error
        if target.exists():
            if not is_exact_reserved_worktree(root, args.task_id, slug, target):
                raise RuntimeError(
                    "Git worktree registration is gone but residual target requires "
                    f"manual filesystem cleanup: {target}; branch preserved"
                ) from error
            try:
                remove_reserved_task_worktree(root, args.task_id, slug)
            except RuntimeError as cleanup_error:
                raise RuntimeError(
                    f"Git removal partially succeeded; residual cleanup failed: {target}"
                ) from cleanup_error
    if target.exists():
        raise RuntimeError(
            f"Worktree target remains after removal; branch preserved: {target}"
        )
    run_git("branch", "-d", branch, cwd=root)
    print(f"Removed worktree: {target}")
    print(f"Deleted merged local branch: {branch}")


def run(args: argparse.Namespace) -> None:
    if not TASK_PATTERN.fullmatch(args.task_id):
        raise ValueError("task-id must look like YYYY-MM-DD-task-NNN")
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise ValueError("run requires a command after --")
    root = repo_root(Path.cwd())
    matches = [
        entry for entry in worktrees(root)
        if entry.get("branch", "").startswith(f"refs/heads/codex/{args.task_id}-")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one worktree for {args.task_id}, found {len(matches)}")
    target = Path(matches[0]["worktree"]).resolve()
    slug = matches[0]["branch"].removeprefix(f"refs/heads/codex/{args.task_id}-")
    temp_dir = task_temp_dir(root, args.task_id, slug)
    if not temp_dir.is_dir():
        raise RuntimeError(f"Reserved task temp directory does not exist: {temp_dir}")
    env = os.environ.copy()
    env["CODEX_SYSTEM_TEMP"] = str(Path(tempfile.gettempdir()).resolve())
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    env["GIT_CONFIG_COUNT"] = str(count + 1)
    env[f"GIT_CONFIG_KEY_{count}"] = "safe.directory"
    env[f"GIT_CONFIG_VALUE_{count}"] = str(target)
    for name in ("TEMP", "TMP", "TMPDIR"):
        env[name] = str(temp_dir)
    result = subprocess.run(command, cwd=target, env=env, check=False)
    raise SystemExit(result.returncode)


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

    run_parser = commands.add_parser("run")
    run_parser.add_argument("--task-id", required=True)
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    run_parser.set_defaults(handler=run)
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
