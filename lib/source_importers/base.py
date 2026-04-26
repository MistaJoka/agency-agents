from __future__ import annotations

from abc import ABC, abstractmethod


class SourceImporter(ABC):
    """Pluggable sync + discovery for one configured source (see `data/sources.json`)."""

    @abstractmethod
    def sync(self) -> None:
        """Fetch or update the source material on disk (clone/pull or no-op for local)."""

    @abstractmethod
    def discover_items(self) -> list[dict]:
        """
        Return file-level candidates for normalization.

        Each item should include: source_id, source_name, source_url, repo_path (Path to repo root),
        file_path (Path to a .md file), rel_path (posix path from repo root).
        """
