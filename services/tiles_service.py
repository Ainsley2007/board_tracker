from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List

_TILES_JSON = Path(__file__).resolve().parent.parent / "assets" / "tiles.json"

with _TILES_JSON.open(encoding="utf-8") as fp:
    _raw = json.load(fp)["tiles"]

TILES: Dict[int, Dict[str, Any]] = {t["id"]: t for t in _raw}


def get_tile(tile_id: int) -> Dict[str, Any] | None:
    return TILES.get(tile_id)


def all_tiles() -> Dict[int, Dict[str, Any]]:
    return TILES


def get_tiles_by_type(tile_type: str) -> List[Dict[str, Any]]:
    """
    Return a list of all tile dicts whose "type" matches the given tile_type.

    Example:
        >>> get_tiles_by_type("RETURN")
        [
          {"id": 24, "type": "RETURN", "destination_id": 17},
          {"id": 46, "type": "RETURN", "destination_id": 40},
          ...
        ]
    """
    return [tile for tile in TILES.values() if tile.get("type") == tile_type]
