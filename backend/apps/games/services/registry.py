from __future__ import annotations
import json
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Tuple

class GameRegistry:
    def __init__(self) -> None:
        self._games: List[Dict[str, Any]] = []
        self._lowers: List[Dict[str, Any]] = []
        self._loaded = False
        self._lock = RLock()

    def _iter_file(self, p: Path):
        with p.open("r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                return
            if data.lstrip().startswith("["):
                arr = json.loads(data)
                for o in arr:
                    if isinstance(o, dict):
                        yield o
            else:
                for line in data.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(o, dict):
                        yield o

    def _lower_proj(self, rec: Dict[str, Any]) -> Dict[str, Any]:
        game = str(rec.get("Game", "")).lower()
        platform = str(rec.get("Platform", "")).lower()
        dev = str(rec.get("Dev", "")).lower()
        publisher = str(rec.get("Publisher", "")).lower()
        blob = " | ".join([game, platform, dev, publisher, str(rec.get("Year", ""))])
        return {"game": game, "platform": platform, "dev": dev, "publisher": publisher, "blob": blob}

    def load_from_dir(self, dirpath: Path) -> Tuple[int, int]:
        with self._lock:
            if self._loaded:
                return (len(self._games), len(self._games))
            records: List[Dict[str, Any]] = []
            lowers: List[Dict[str, Any]] = []
            if dirpath.exists():
                for p in dirpath.rglob("*.json"):
                    for obj in self._iter_file(p):
                        records.append(obj)
                        lowers.append(self._lower_proj(obj))
            self._games = records
            self._lowers = lowers
            self._loaded = True
            return (len(records), len(records))

    def ensure_loaded(self, default_dir: Path) -> None:
        if not self._loaded:
            self.load_from_dir(default_dir)

    @property
    def games(self) -> List[Dict[str, Any]]:
        return self._games

    @property
    def lowers(self) -> List[Dict[str, Any]]:
        return self._lowers


REGISTRY = GameRegistry()
