"""Run the repository's required local verification commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    venv_python = (
        root / ".venv" / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else root / ".venv" / "bin" / "python"
    )
    python = venv_python if venv_python.exists() else Path(sys.executable)
    commands = [
        [str(python), "-m", "ruff", "check", "."],
        [str(python), "-m", "pytest", "tests", "-q"],
    ]
    for command in commands:
        print(f"> {subprocess.list2cmdline(command)}", flush=True)
        subprocess.run(command, cwd=root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
