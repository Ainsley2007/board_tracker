from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

# Pad naar het JSON-bestand (pas aan als je structuur anders is)
_TILES_JSON = Path(__file__).with_name("assets") / "tiles.json"

with _TILES_JSON.open(encoding="utf-8") as fp:
    _raw = json.load(fp)["tiles"]

# Maak er een dict van: id → tile-dict (snelle O(1) lookup)
TILES: Dict[int, Dict[str, Any]] = {t["id"]: t for t in _raw}


def get_tile(tile_id: int) -> Dict[str, Any] | None:
    return TILES.get(tile_id)


def all_tiles() -> Dict[int, Dict[str, Any]]:
    return TILES
