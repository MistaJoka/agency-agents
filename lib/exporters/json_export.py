from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_registry_json(
    path: Path,
    items: list[dict[str, Any]],
    *,
    metadata_only: bool = False,
) -> None:
    """Write ``{ "count": n, "items": [...] }`` for pipelines / inspection."""
    if metadata_only:
        slim: list[dict[str, Any]] = []
        for it in items:
            slim.append(
                {
                    k: v
                    for k, v in it.items()
                    if k not in ("raw_content", "normalized_content")
                }
            )
        payload = {"count": len(slim), "items": slim}
    else:
        payload = {"count": len(items), "items": items}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
