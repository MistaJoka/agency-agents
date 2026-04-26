from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from lib import agent_layout
from lib.source_importers.base import SourceImporter

_SKIPPED_PREFIXES = (
    ".github/",
    "node_modules/",
    "data/imported_sources/",
    "supabase-web/",
    "agent-matchmaker/qa-screenshots/",
)

_DOC_BASE_NAMES = frozenset(
    {
        "readme",
        "changelog",
        "contributing",
        "code_of_conduct",
        "license",
        "security",
        "todo",
    }
)


def load_sources_config(data_dir: Path) -> list[dict[str, Any]]:
    path = data_dir / "sources.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return list(raw.get("sources", []))


def _run_git(args: list[str], *, cwd: Path | None = None) -> None:
    r = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed ({r.returncode}): {err}")


def _should_skip_relpath(rel: str) -> bool:
    r = rel.replace("\\", "/").lower()
    for p in _SKIPPED_PREFIXES:
        if r.startswith(p) or f"/{p}" in f"/{r}/":
            return True
    base = Path(rel).stem.lower()
    if base in _DOC_BASE_NAMES:
        return True
    return False


class GitHubRepoImporter(SourceImporter):
    """Clone/pull GitHub (or any git) URL into ``data/imported_sources/{id}/`` or use repo root for local."""

    def __init__(
        self,
        source: dict[str, Any],
        *,
        repo_root: Path,
        data_dir: Path,
    ) -> None:
        self._source = source
        self._repo_root = repo_root
        self._data_dir = data_dir
        self._id = str(source.get("id", "unknown"))

    def _import_dir(self) -> Path:
        return self._data_dir / "imported_sources" / self._id

    def sync(self) -> None:
        if not self._source.get("enabled", False):
            return
        if self._source.get("local", False):
            if not (self._repo_root / "README.md").is_file():
                print(f"  [{self._id}] local: repo root {self._repo_root} (sanity check: README.md missing)", file=sys.stderr)
            return

        url = (self._source.get("repo_url") or "").strip()
        if not url:
            raise ValueError(f"Source {self._id!r} has no repo_url")
        target = self._import_dir()
        target.parent.mkdir(parents=True, exist_ok=True)
        if not (target / ".git").is_dir():
            _run_git(["clone", "--depth", "1", url, str(target)])
        else:
            # Non-destructive: fast-forward only
            _run_git(["-C", str(target), "fetch", "--depth", "1", "origin"], cwd=None)
            _run_git(["-C", str(target), "pull", "--ff-only"], cwd=None)

    def _walk_root(self) -> Path:
        if self._source.get("local", False):
            return self._repo_root
        return self._import_dir()

    def discover_items(self) -> list[dict[str, Any]]:
        if not self._source.get("enabled", False):
            return []
        root = self._walk_root()
        if not root.is_dir():
            return []
        out: list[dict[str, Any]] = []
        base_url = (self._source.get("repo_url") or "").rstrip("/")
        if base_url.endswith(".git"):
            base_url = base_url[:-4]
        if self._source.get("local", False):
            md_iter: list[Path] = []
            for d in agent_layout.AGENT_DIRS:
                sub = root / d
                if sub.is_dir():
                    md_iter.extend(sorted(sub.rglob("*.md")))
        else:
            globpat = (self._source.get("item_glob") or "").strip()
            if globpat:
                md_iter = sorted(root.glob(globpat))
            else:
                md_iter = sorted(root.rglob("*.md"))
        for md in md_iter:
            try:
                rel = md.relative_to(root)
            except ValueError:
                continue
            rel_s = rel.as_posix()
            if _should_skip_relpath(rel_s):
                continue
            item = {
                "source_id": self._id,
                "source_name": str(self._source.get("name", self._id)),
                "source_url": base_url,
                "source_path": rel_s,
                "repo_path": root,
                "file_path": md,
            }
            out.append(item)
        return out
