#!/usr/bin/env python3
"""
Start the local Agent Matchmaker (same as run-agent-matchmaker.sh).

Use this if your runner only executes Python — do not run the ``.sh`` file with
``python3`` (that causes SyntaxError: bash is not Python).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
webapp = ROOT / "agent-matchmaker" / "webapp.py"

def _venv_python() -> str:
    for rel in (".venv/bin/python3", ".venv/bin/python"):
        p = ROOT / rel
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return sys.executable

def main() -> None:
    py = _venv_python()
    os.execv(py, [py, str(webapp), *sys.argv[1:]])

if __name__ == "__main__":
    main()
