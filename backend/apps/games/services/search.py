# apps/games/services/search.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from .registry import REGISTRY, GameRegistry


class GameSearchService:
    """
    simple substring-based search service over gameregistry
    """

    def __init__(self, registry: GameRegistry = REGISTRY) -> None:
        self.registry = registry

    def search_by_name(
        self,
        *,
        q: str,
        limit: int = 50,
        offset: int = 0,
        platform: Optional[str] = None,
        autoload_dir: Optional[Path] = None,
    ) -> Dict[str, object]:
        """
        search games by name and optional platform filter.
        """
        if autoload_dir is not None:
            self.registry.ensure_loaded(autoload_dir)

        q = (q or "").strip().lower()
        platform = (platform or "").strip().lower()

        if not q:
            return {"total": 0, "items": [], "limit": limit, "offset": offset}

        games = self.registry.games
        lowers = self.registry.lowers

        matched_idx: List[int] = []
        for i, lo in enumerate(lowers):
            if q not in lo["game"]:
                continue
            if platform and platform not in lo["platform"]:
                continue
            matched_idx.append(i)

        total = len(matched_idx)
        slice_idx = matched_idx[offset : offset + limit]
        items = [games[i] for i in slice_idx]

        return {"total": total, "items": items, "limit": limit, "offset": offset}
