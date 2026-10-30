from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(project_root / "aethera" / "app.py"),
        "--server.headless=false",
    ]
    subprocess.run(cmd, cwd=str(project_root), check=False)


if __name__ == "__main__":
    main()
