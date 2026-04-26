#!/usr/bin/env python3
"""
Walk enabled sources, normalize markdown into ``data/registry.sqlite``.

Does not replace ``agent-matchmaker/catalog.json``; run ``build_agent_matchmaker.py`` for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.normalizers.markdown_agent import item_from_markdown_path  # noqa: E402
from lib.registry_db import open_db, replace_all_items  # noqa: E402
from lib.source_importers.github_repo import GitHubRepoImporter, load_sources_config  # noqa: E402


def main() -> int:
    data_dir = REPO_ROOT / "data"
    db_path = data_dir / "registry.sqlite"
    sources = load_sources_config(data_dir)
    items: list = []
    for src in sources:
        if not src.get("enabled", False):
            continue
        imp = GitHubRepoImporter(src, repo_root=REPO_ROOT, data_dir=data_dir)
        for disc in imp.discover_items():
            fp = disc["file_path"]
            try:
                raw = fp.read_text(encoding="utf-8")
            except OSError as e:
                print(f"  skip read {fp}: {e}", file=sys.stderr)
                continue
            rel = disc["source_path"].replace("\\", "/")
            row = item_from_markdown_path(
                file_path=fp,
                rel_path=rel,
                source_id=disc["source_id"],
                source_name=disc["source_name"],
                source_url=disc.get("source_url") or "",
                raw=raw,
            )
            if row:
                items.append(row)
    items.sort(key=lambda r: (r.get("source_id", ""), r.get("source_path", "")))
    conn = open_db(db_path)
    try:
        replace_all_items(conn, items)
    finally:
        conn.close()
    print(f"Wrote {len(items)} items to {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
