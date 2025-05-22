import json
import pytest

# import your module under test; adjust the name if needed
import services.tiles_service as tiles


def test_tiles_json_loads_and_builds_dict():
    # this executes the top‐level JSON load and dict comprehension
    raw = json.load(tiles._TILES_JSON.open(encoding="utf-8"))["tiles"]
    # TILES should be a dict mapping each id to its dict
    assert isinstance(tiles.TILES, dict)
    assert len(tiles.TILES) == len(raw)
    # check that keys match the ids in the JSON
    json_ids = {t["id"] for t in raw}
    assert set(tiles.TILES.keys()) == json_ids


def test_get_tile_existing_and_identity():
    # pick a known ID; e.g. 0 is "Start"
    tile0 = tiles.get_tile(0)
    assert tile0 is tiles.TILES[0]
    assert tile0["name"] == "Start"
    assert tile0["type"] == "START"


def test_get_tile_missing():
    # nonexistent IDs should return None
    assert tiles.get_tile(-1) is None
    assert tiles.get_tile(9999) is None


def test_all_tiles_returns_the_same_dict():
    # should return the very same dict object
    all_ = tiles.all_tiles()
    assert all_ is tiles.TILES
    # sanity‐check that it has at least one entry
    assert 0 in all_


def test_get_tiles_by_type_return():
    # There are exactly four RETURN tiles in the sample JSON
    returns = tiles.get_tiles_by_type("RETURN")
    ids = {t["id"] for t in returns}
    assert ids == {24, 46, 72, 89}
    assert all(t["type"] == "RETURN" for t in returns)


def test_get_tiles_by_type_tile():
    # TILE appears many times; check a couple invariants
    tiles_list = tiles.get_tiles_by_type("TILE")
    assert all(t["type"] == "TILE" for t in tiles_list)
    # Ensure a known TILE ID is present
    assert any(t["id"] == 1 for t in tiles_list)


def test_get_tiles_by_type_challenge_and_skip_and_end_and_start():
    # Check CHALLENGE
    ch = tiles.get_tiles_by_type("CHALLENGE")
    assert any(t["id"] == 17 for t in ch)
    # Check SKIP
    sk = tiles.get_tiles_by_type("SKIP")
    assert any(t["id"] == 20 for t in sk)
    # Check END
    end = tiles.get_tiles_by_type("END")
    assert any(t["id"] == 90 for t in end)
    # Check START
    start = tiles.get_tiles_by_type("START")
    assert any(t["id"] == 0 for t in start)


def test_get_tiles_by_type_none():
    # Unknown types yield an empty list
    assert tiles.get_tiles_by_type("FOOBAR") == []
