"""Run the repository's required local verification commands."""

from __future__ import annotations

import getpass
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def execution_identity() -> str:
    """Identify the OS principal that owns temp files, not just its display name."""
    if os.name == "nt":
        try:
            return subprocess.run(
                ["whoami"], check=True, capture_output=True, text=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return getpass.getuser()
    return f"{getpass.getuser()}-{os.getuid()}"


def system_temp_dir() -> Path:
    """Use the pre-task environment when invoked by the lifecycle runner."""
    return Path(os.environ.get("CODEX_SYSTEM_TEMP", tempfile.gettempdir())).resolve()


def pytest_base_temp(root: Path) -> Path:
    """Return a short, per-user and per-task pytest child under system temp."""
    handoffs = sorted((root / ".codex" / "handoffs").glob("*/task-*/HANDOFF.md"))
    task_id = handoffs[0].parent.parent.name + "-" + handoffs[0].parent.name if handoffs else "local"
    identity = execution_identity()
    name = (
        f"codex-check-{short_hash(identity)}-"
        f"{short_hash(str(root.resolve()))}-{short_hash(task_id)}"
    )
    return system_temp_dir() / name / "pytest"


def make_writable(function, path: str, _exception: object) -> None:
    Path(path).chmod(stat.S_IWRITE)
    function(path)


def remove_tree(path: Path, timeout: float = 8.0) -> None:
    """Remove a generated directory, retrying transient Windows file locks."""
    deadline = time.monotonic() + timeout
    while path.exists():
        try:
            shutil.rmtree(path, onerror=make_writable)
        except OSError as error:
            if not path.exists():
                return
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Unable to remove temporary directory: {path}") from error
            time.sleep(0.1)


def remove_pytest_base_temp(base_temp: Path) -> None:
    expected_parent = system_temp_dir()
    child = base_temp.resolve()
    if (
        child.name == "pytest"
        and child.parent.parent == expected_parent
        and child.parent.name.startswith("codex-check-")
    ):
        remove_tree(child)
        if child.parent.exists() and not any(child.parent.iterdir()):
            remove_tree(child.parent)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    venv_python = (
        root / ".venv" / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else root / ".venv" / "bin" / "python"
    )
    python = venv_python if venv_python.exists() else Path(sys.executable)
    base_temp = pytest_base_temp(root)
    base_temp.parent.mkdir(parents=True, exist_ok=True)
    commands = [
        [str(python), "-m", "ruff", "check", "."],
        [str(python), "-m", "pytest", "tests", "-q", "--basetemp", str(base_temp)],
    ]
    try:
        for command in commands:
            print(f"> {subprocess.list2cmdline(command)}", flush=True)
            subprocess.run(command, cwd=root, check=True)
    finally:
        remove_pytest_base_temp(base_temp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
