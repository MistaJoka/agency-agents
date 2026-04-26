#!/usr/bin/env python3
"""
Write Cursor ``.mdc`` rules from ``data/registry.sqlite`` (same format idea as
``convert.sh`` + ``convert_cursor`` for agency agents, but from the multi-source
registry). Output defaults to ``data/export_packs/cursor/rules/`` (copy to
``.cursor/rules`` in a project, or use Cursor global rules, as you prefer).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.exporters.cursor_pack import export_cursor_rules  # noqa: E402
from lib.registry_db import fetch_all_items, open_db  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "export_packs" / "cursor" / "rules",
        help="Output directory for .mdc files",
    )
    ap.add_argument(
        "--source-id",
        type=str,
        default="",
        help="Only include items where source_id equals this (e.g. claude-skills)",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If >0, only export first N items after filter (for smoke tests)",
    )
    ap.add_argument(
        "--clear",
        action="store_true",
        help="Remove output directory before writing (avoids stale .mdc from old runs)",
    )
    args = ap.parse_args()

    db_path = REPO_ROOT / "data" / "registry.sqlite"
    if not db_path.is_file():
        print(f"Missing {db_path}; run: python3 scripts/normalize_sources.py", file=sys.stderr)
        return 1

    conn = open_db(db_path)
    try:
        items = fetch_all_items(conn)
    finally:
        conn.close()

    if args.source_id:
        items = [i for i in items if i.get("source_id") == args.source_id]
    if args.limit and args.limit > 0:
        items = items[: args.limit]

    if not items:
        print("No items to export (check filters / registry).", file=sys.stderr)
        return 1

    out = Path(args.out)
    if args.clear and out.is_dir():
        shutil.rmtree(out)
    written = export_cursor_rules(out, items)
    print(f"Wrote {len(written)} .mdc files under {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
