"""Create a local virtual environment and install development dependencies."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the setup commands without executing them.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    venv = root / ".venv"
    venv_python = (
        venv / "Scripts" / "python.exe"
        if sys.platform == "win32"
        else venv / "bin" / "python"
    )
    commands: list[list[str]] = []
    if not venv_python.exists():
        commands.append([sys.executable, "-m", "venv", str(venv)])
    commands.append(
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--editable",
            f"{root}[dev]",
        ]
    )

    for command in commands:
        print(subprocess.list2cmdline(command))
        if not args.dry_run:
            subprocess.run(command, cwd=root, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
