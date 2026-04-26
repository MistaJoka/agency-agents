from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Mirrors scripts/convert.sh slugify
_RE_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(s: str) -> str:
    t = s.strip().lower()
    t = _RE_SLUG.sub("-", t)
    t = re.sub(r"-+", "-", t).strip("-")
    return t or "item"


def _one_line_description(text: str, max_len: int = 2000) -> str:
    return " ".join(text.split())[:max_len]


def mdc_file_body(item: dict[str, Any]) -> str:
    return (item.get("normalized_content") or item.get("raw_content") or "").strip()


def build_mdc_text(item: dict[str, Any]) -> str:
    desc = _one_line_description(str(item.get("description") or ""))
    if not desc and item.get("name"):
        desc = _one_line_description(str(item.get("name", "")))
    body = mdc_file_body(item)
    prov = f"<!-- agency-registry: {item.get('id', '')} -->\n\n"
    return (
        "---\n"
        f'description: {desc!r}\n'
        'globs: ""\n'
        "alwaysApply: false\n"
        "---\n"
        f"{prov}{body}\n"
    )


def export_cursor_rules(
    out_dir: Path,
    items: list[dict[str, Any]],
) -> list[Path]:
    """
    Write one ``.mdc`` per item under ``out_dir`` (e.g. ``.../rules``).
    Slugs from item ``name``; suffix ``-2``, ``-3`` on duplicate basenames.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    used: dict[str, int] = {}
    written: list[Path] = []
    for it in items:
        base = slugify(str(it.get("name", "item")))[:100]
        if base in used:
            used[base] += 1
            fname = f"{base}-{used[base]}.mdc"
        else:
            used[base] = 1
            fname = f"{base}.mdc"
        path = out_dir / fname
        path.write_text(build_mdc_text(it), encoding="utf-8")
        written.append(path)
    return written
