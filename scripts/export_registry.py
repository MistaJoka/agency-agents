#!/usr/bin/env python3
"""Dump ``data/registry.sqlite`` to JSON for pipelines, grep, and tooling (not the matchmaker UI)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.exporters.json_export import write_registry_json  # noqa: E402
from lib.registry_db import fetch_all_items, open_db  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "registry_export.json",
        help="Output path (default: data/registry_export.json)",
    )
    ap.add_argument(
        "--metadata-only",
        action="store_true",
        help="Omit raw_content and normalized_content (smaller file)",
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
    write_registry_json(args.output, items, metadata_only=args.metadata_only)
    print(f"Wrote {len(items)} items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
