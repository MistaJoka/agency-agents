#!/usr/bin/env python3
"""
Scan agent markdown files (same roots as lint-agents.sh), parse YAML frontmatter,
and emit agent-matchmaker/index.html with an embedded catalog for offline use.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.agent_layout import AGENT_DIRS  # noqa: E402  (after sys.path)

AGENT_DIR_SET = frozenset(AGENT_DIRS)
OUT_DIR = REPO_ROOT / "agent-matchmaker"
OUT_HTML = OUT_DIR / "index.html"
OUT_CATALOG_JSON = OUT_DIR / "catalog.json"
SOURCES_JSON = REPO_ROOT / "data" / "sources.json"
TEMPLATE = OUT_DIR / "index.template.html"

FRONTMATTER_KEY = re.compile(r"^([A-Za-z0-9_]+):\s*(.*)$")

# Skipped under data/imported_sources/ (index docs, not agent cards)
_IMPORT_DOC_STEMS = frozenset(
    {
        "readme",
        "contributing",
        "code_of_conduct",
        "license",
        "changelog",
        "security",
        "todo",
    }
)


def _is_imported_path(rel: str) -> bool:
    return rel.replace("\\", "/").startswith("data/imported_sources/")


def _default_color_imported(rel: str) -> str:
    """Stable muted hex for packs that omit `color` in frontmatter (e.g. Volt agent MD)."""
    h = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:6]
    # Keep in a cool mid range (readability on dark UI)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = 0x3A + (r * 0x4A) // 0xFF
    g = 0x44 + (g * 0x4E) // 0xFF
    b = 0x5A + (b * 0x44) // 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


def infer_source_id(rel: str) -> str:
    """Map repo-relative path to registry source id (see data/sources.json)."""
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "imported_sources":
        return parts[2]
    if parts and parts[0] in AGENT_DIR_SET:
        return "local-agency-agents"
    return "local-agency-agents"


def infer_subcategory(rel: str) -> str:
    """
    First subfolder under the catalog root (division or imported pack root).
    Empty string when the .md file sits directly in that root.
    """
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "imported_sources":
        if len(parts) <= 3:
            return ""
        if len(parts) == 4:
            return ""
        return parts[3]
    if len(parts) <= 2:
        return ""
    return parts[1]


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
    rel = path.relative_to(REPO_ROOT).as_posix()
    rel_posix = rel.replace("\\", "/")
    imported = _is_imported_path(rel_posix)
    if imported and path.stem.lower() in _IMPORT_DOC_STEMS:
        return None
    if "name" not in fm or "description" not in fm:
        return None
    color_raw = (fm.get("color") or "").strip()
    if not color_raw:
        if not imported:
            return None
        color = _default_color_imported(rel_posix)
    else:
        color = color_raw
    parts = rel_posix.split("/")
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "imported_sources":
        category = parts[2]
    else:
        category = parts[0]
    subcat = infer_subcategory(rel)
    return {
        "id": rel.replace("/", "-").replace(".md", ""),
        "path": rel,
        "source_id": infer_source_id(rel),
        "category": category,
        "subcategory": subcat,
        "name": fm["name"],
        "description": fm["description"],
        "color": color,
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
    imported = REPO_ROOT / "data" / "imported_sources"
    if imported.is_dir():
        for md in sorted(imported.rglob("*.md")):
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
    if "__SOURCES_JSON_B64__" not in template:
        print("Template missing __SOURCES_JSON_B64__ placeholder.", file=sys.stderr)
        return 1
    try:
        src_raw = SOURCES_JSON.read_text(encoding="utf-8")
    except OSError:
        src_raw = '{"sources":[]}'
    src_b64 = base64.b64encode(src_raw.encode("utf-8")).decode("ascii")
    html = template.replace("__AGENT_CATALOG_B64__", b64).replace("__SOURCES_JSON_B64__", src_b64)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CATALOG_JSON.write_text(blob, encoding="utf-8")
    print(f"Wrote {OUT_HTML} ({len(catalog)} agents)")
    print(f"Wrote {OUT_CATALOG_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
