#!/usr/bin/env python3
"""
Scan agent markdown files (same roots as lint-agents.sh), parse YAML frontmatter,
and emit agent-matchmaker/index.html with an embedded catalog for offline use.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

# Keep in sync with scripts/lint-agents.sh AGENT_DIRS
AGENT_DIRS = (
    "academic",
    "design",
    "engineering",
    "finance",
    "game-development",
    "marketing",
    "paid-media",
    "product",
    "project-management",
    "sales",
    "spatial-computing",
    "specialized",
    "strategy",
    "support",
    "testing",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "agent-matchmaker"
OUT_HTML = OUT_DIR / "index.html"
OUT_CATALOG_JSON = OUT_DIR / "catalog.json"
TEMPLATE = OUT_DIR / "index.template.html"

FRONTMATTER_KEY = re.compile(r"^([A-Za-z0-9_]+):\s*(.*)$")


def parse_frontmatter(raw: str) -> dict[str, str] | None:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str] = {}
    i = 1
    while i < len(lines):
        if lines[i].strip() == "---":
            break
        m = FRONTMATTER_KEY.match(lines[i])
        if m:
            key, val = m.group(1), m.group(2).strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            data[key] = val
        i += 1
    else:
        return None
    return data


def load_agent(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = parse_frontmatter(text)
    if not fm:
        return None
    required = ("name", "description", "color")
    if not all(k in fm for k in required):
        return None
    rel = path.relative_to(REPO_ROOT).as_posix()
    category = rel.split("/")[0]
    return {
        "id": rel.replace("/", "-").replace(".md", ""),
        "path": rel,
        "category": category,
        "name": fm["name"],
        "description": fm["description"],
        "color": fm.get("color", ""),
        "emoji": fm.get("emoji", ""),
        "vibe": fm.get("vibe", ""),
        "source": text,
    }


def collect_catalog() -> list[dict]:
    agents: list[dict] = []
    for d in AGENT_DIRS:
        root = REPO_ROOT / d
        if not root.is_dir():
            continue
        for md in sorted(root.rglob("*.md")):
            row = load_agent(md)
            if row:
                agents.append(row)
    agents.sort(key=lambda a: (a["category"], a["name"].lower()))
    return agents


def main() -> int:
    catalog = collect_catalog()
    if not catalog:
        print("No agents found; check AGENT_DIRS paths.", file=sys.stderr)
        return 1
    if not TEMPLATE.is_file():
        print(f"Missing template: {TEMPLATE}", file=sys.stderr)
        return 1
    template = TEMPLATE.read_text(encoding="utf-8")
    blob = json.dumps(catalog, ensure_ascii=False)
    b64 = base64.b64encode(blob.encode("utf-8")).decode("ascii")
    if "__AGENT_CATALOG_B64__" not in template:
        print("Template missing __AGENT_CATALOG_B64__ placeholder.", file=sys.stderr)
        return 1
    html = template.replace("__AGENT_CATALOG_B64__", b64)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CATALOG_JSON.write_text(blob, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(catalog)} agents)")
    print(f"Wrote {OUT_CATALOG_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
