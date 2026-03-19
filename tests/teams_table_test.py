# test_teams_table.py
import pytest
from discord import Colour

import db.teams_table as tt
from db.teams_table import (
    add_blacklist_tile,
    add_blacklist_charges,
    add_team,
    consume_blacklist_charge,
    get_blacklist_charges,
    get_blacklist_tiles,
    increment_return_blacklist_grant_if_allowed,
    replace_blacklist_tile,
    remove_team,
    get_team,
    get_teams,
    clear_pending_flag,
    update_team_position,
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
    assert row["blacklist_tiles"] == []
    assert row["blacklist_charges"] == 1


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


def test_blacklist_tile_set_and_get():
    add_team("Delta", "delta", 8, Colour.purple())
    assert get_blacklist_tiles("delta") == []
    add_blacklist_tile("delta", 33)
    assert get_blacklist_tiles("delta") == [33]
    replace_blacklist_tile("delta", 33, 36)
    assert get_blacklist_tiles("delta") == [36]


def test_blacklist_charge_flow():
    add_team("Echo", "echo", 9, Colour.teal())
    assert get_blacklist_charges("echo") == 1
    assert consume_blacklist_charge("echo") == 0
    assert consume_blacklist_charge("echo") is None
    assert add_blacklist_charges("echo", 2) == 2
    assert get_blacklist_charges("echo") == 2


def test_return_blacklist_grant_cap():
    add_team("Fox", "fox", 11, Colour.orange())
    assert increment_return_blacklist_grant_if_allowed("fox") == (2, True)
    assert increment_return_blacklist_grant_if_allowed("fox") == (3, True)
    assert increment_return_blacklist_grant_if_allowed("fox") == (3, False)
    assert get_team("fox")["return_blacklist_grants"] == 2


def test_clear_pending_on_nonexistent():
    # should not raise, returns empty list
    result = clear_pending_flag("no_such")
    assert result == []


def test_remove_nonexistent_team():
    # removing a slug that never existed should not error
    remove_team("ghost")
    # still empty
    assert get_teams() == []
