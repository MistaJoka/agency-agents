from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Mirrors scripts/build_agent_matchmaker.FRONTMATTER_KEY
_FRONTMATTER_KEY = re.compile(r"^([A-Za-z0-9_]+):\s*(.*)$")


def parse_frontmatter(raw: str) -> dict[str, str] | None:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    data: dict[str, str] = {}
    i = 1
    while i < len(lines):
        if lines[i].strip() == "---":
            break
        m = _FRONTMATTER_KEY.match(lines[i])
        if m:
            key, val = m.group(1), m.group(2).strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            data[key] = val
        i += 1
    else:
        return None
    return data


def _strip_frontmatter_block(raw: str) -> str:
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return raw
    i = 1
    while i < len(lines):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1 :]).strip()
        i += 1
    return raw


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def _split_tags(val: str) -> list[str]:
    s = val.strip()
    if not s:
        return []
    if s.startswith("["):
        # crude YAML-like list: [a, b]
        s = s.strip("[]")
    parts = re.split(r"[,;]", s)
    return [p.strip() for p in parts if p.strip()]


def _infer_item_type(fm: dict[str, str], rel: str) -> str:
    low = rel.lower()
    if "name" in fm and "color" in fm and "description" in fm:
        return "agent"
    if "skill" in low or "skills" in low or "/.cursor/" in low:
        return "skill"
    if "name" in fm and "description" in fm:
        return "skill"
    return "markdown"


def item_from_markdown_path(
    *,
    file_path: Path,
    rel_path: str,
    source_id: str,
    source_name: str,
    source_url: str,
    raw: str,
) -> dict[str, Any] | None:
    """
    Return a normalized registry item, or None if this file should not be ingested
    (plain docs, empty, etc.).
    """
    fm = parse_frontmatter(raw)
    if not fm:
        return None
    if "name" not in fm or "description" not in fm:
        return None

    body = _strip_frontmatter_block(raw)
    name = (fm.get("name") or "").strip() or _first_heading(body) or file_path.stem.replace("-", " ").title()
    category = rel_path.split("/")[0] if "/" in rel_path else "root"

    tags: list[str] = []
    if "tags" in fm:
        tags = _split_tags(fm["tags"])
    if "divisions" in fm:
        tags.extend(_split_tags(fm["divisions"]))

    item_type = _infer_item_type(fm, rel_path)
    tool_targets: list[str] = []
    if "tool" in fm:
        tool_targets = _split_tags(fm["tool"])
    for key in ("tools", "targets"):
        if key in fm:
            tool_targets.extend(_split_tags(fm[key]))
    # dedupe preserve order
    seen: set[str] = set()
    tool_targets = [t for t in tool_targets if t and not (t in seen or seen.add(t))]

    norm_body = re.sub(r"\n{3,}", "\n\n", body).strip()[:20000]
    rel_norm = rel_path.replace("\\", "/")
    rec_id = f"{source_id}:{rel_norm}"

    return {
        "id": rec_id,
        "source_id": source_id,
        "source_name": source_name,
        "source_url": source_url,
        "source_path": rel_path,
        "item_type": item_type,
        "name": name,
        "category": category,
        "description": (fm.get("description") or "")[:2000],
        "tags": tags,
        "tool_targets": tool_targets,
        "raw_content": raw,
        "normalized_content": norm_body,
    }
