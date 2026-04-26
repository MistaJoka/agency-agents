#!/usr/bin/env python3
"""Clone or update enabled non-local sources listed in ``data/sources.json``."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.source_importers.github_repo import GitHubRepoImporter, load_sources_config  # noqa: E402


def main() -> int:
    data_dir = REPO_ROOT / "data"
    sources = load_sources_config(data_dir)
    print("Sync sources (enabled only; local = no git op)")
    for src in sources:
        imp = GitHubRepoImporter(src, repo_root=REPO_ROOT, data_dir=data_dir)
        sid = src.get("id", "?")
        if not src.get("enabled", False):
            print(f"  skip (disabled): {sid}")
            continue
        if src.get("local", False):
            print(f"  local workspace: {sid}")
        else:
            print(f"  git sync: {sid}")
        try:
            imp.sync()
        except Exception as e:
            print(f"  ERROR {sid}: {e}", file=sys.stderr)
            return 1
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
