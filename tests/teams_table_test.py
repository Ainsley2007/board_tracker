# test_teams_table.py
import pytest
from discord import Colour

import db.teams_table as tt
from db.teams_table import (
    add_team,
    remove_team,
    get_team,
    get_teams,
    clear_pending_flag,
    update_team_position,
    has_returned,
    mark_returned,
    RETURN_TILES,
)


@pytest.fixture(autouse=True)
def clear_table():
    # wipe before and after each test
    tt.teams_table.truncate()
    yield
    tt.teams_table.truncate()


def test_add_and_get_team():
    add_team("Alpha Squad", "alpha", 42, Colour.green())
    row = get_team("alpha")
    assert row is not None
    assert row["slug"] == "alpha"
    assert row["name"] == "Alpha Squad"
    assert row["role_id"] == 42
    assert row["pos"] == 0
    assert row["pending"] is False
    assert row["return_mask"] == 0


def test_remove_team():
    add_team("Beta Team", "beta", 7, Colour.blue())
    assert get_team("beta") is not None
    remove_team("beta")
    assert get_team("beta") is None


def test_get_teams_list():
    assert get_teams() == []
    add_team("Team One", "one", 1, Colour.red())
    add_team("Team Two", "two", 2, Colour.red())
    slugs = {row["slug"] for row in get_teams()}
    assert slugs == {"one", "two"}


def test_update_and_clear_pending():
    add_team("Gamma", "gamma", 3, Colour.gold())
    # update position sets pending=True
    update_team_position(5, "gamma")
    row = get_team("gamma")
    assert row["pos"] == 5
    assert row["pending"] is True
    # clearing pending resets to False
    clear_pending_flag("gamma")
    row = get_team("gamma")
    assert row["pending"] is False


def test_mark_and_has_returned_single():
    add_team("Delta", "delta", 8, Colour.purple())
    slug = "delta"
    first_tile = RETURN_TILES[0]
    # initially not returned
    assert has_returned(slug, first_tile) is False
    # mark it
    mark_returned(slug, first_tile)
    assert has_returned(slug, first_tile) is True
    # other return tiles still False
    assert has_returned(slug, RETURN_TILES[1]) is False


def test_mark_multiple_and_mask_value():
    add_team("Echo", "echo", 9, Colour.teal())
    slug = "echo"
    t0, t1 = RETURN_TILES[0], RETURN_TILES[1]
    mark_returned(slug, t0)
    mark_returned(slug, t1)
    row = get_team(slug)
    mask = row["return_mask"]
    # bit 0 and bit 1 set → mask == 1<<0 | 1<<1 == 3
    assert mask == ((1 << 0) | (1 << 1))
    # has_returned reflects both
    assert has_returned(slug, t0) is True
    assert has_returned(slug, t1) is True


def test_clear_pending_on_nonexistent():
    # should not raise, returns empty list
    result = clear_pending_flag("no_such")
    assert result == []


def test_remove_nonexistent_team():
    # removing a slug that never existed should not error
    remove_team("ghost")
    # still empty
    assert get_teams() == []
