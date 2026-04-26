from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS registry_items (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  source_name TEXT,
  source_url TEXT,
  source_path TEXT,
  item_type TEXT,
  name TEXT,
  category TEXT,
  description TEXT,
  tags TEXT,
  tool_targets TEXT,
  raw_content TEXT,
  normalized_content TEXT
);
"""


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def replace_all_items(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM registry_items")
    for it in items:
        conn.execute(
            """
            INSERT INTO registry_items (
              id, source_id, source_name, source_url, source_path, item_type,
              name, category, description, tags, tool_targets, raw_content, normalized_content
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                it.get("id"),
                it.get("source_id"),
                it.get("source_name"),
                it.get("source_url"),
                it.get("source_path"),
                it.get("item_type"),
                it.get("name"),
                it.get("category"),
                it.get("description"),
                json.dumps(it.get("tags") or []),
                json.dumps(it.get("tool_targets") or []),
                it.get("raw_content") or "",
                it.get("normalized_content") or "",
            ),
        )
    conn.commit()


def fetch_all_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT id, source_id, source_name, source_url, source_path, item_type,
               name, category, description, tags, tool_targets, raw_content, normalized_content
        FROM registry_items
        ORDER BY source_id, source_path
        """
    )
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        try:
            tags = json.loads(row[9]) if row[9] else []
        except json.JSONDecodeError:
            tags = []
        try:
            tool_targets = json.loads(row[10]) if row[10] else []
        except json.JSONDecodeError:
            tool_targets = []
        out.append(
            {
                "id": row[0],
                "source_id": row[1],
                "source_name": row[2],
                "source_url": row[3],
                "source_path": row[4],
                "item_type": row[5],
                "name": row[6],
                "category": row[7],
                "description": row[8],
                "tags": tags,
                "tool_targets": tool_targets,
                "raw_content": row[11],
                "normalized_content": row[12],
            }
        )
    return out
