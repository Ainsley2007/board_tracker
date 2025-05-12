# test_members_table.py

import pytest

import db.members_table as mt
from db.members_table import (
    add_member,
    get_member,
    get_team_members,
    remove_member,
    remove_members_by_team_id,
)


@pytest.fixture(autouse=True)
def clear_members_table():
    """Truncate the members table before and after each test."""
    mt.members_table.truncate()
    yield
    mt.members_table.truncate()


def test_add_and_get_member():
    add_member(123, "Alice", "team_alpha")
    member = get_member(123)
    assert member is not None
    assert member["user_id"] == 123
    assert member["user_name"] == "Alice"
    assert member["team_slug"] == "team_alpha"


def test_get_team_members_returns_only_that_team():
    add_member(1, "Bob", "team_one")
    add_member(2, "Cara", "team_one")
    add_member(3, "Dan", "team_two")

    team_one = get_team_members("team_one")
    assert len(team_one) == 2
    assert {m["user_id"] for m in team_one} == {1, 2}

    team_two = get_team_members("team_two")
    assert len(team_two) == 1
    assert team_two[0]["user_name"] == "Dan"

    team_none = get_team_members("no_such_team")
    assert team_none == []


def test_remove_member_by_user_id():
    add_member(10, "Eve", "team_x")
    assert get_member(10) is not None

    remove_member(10)
    assert get_member(10) is None

    # calling again should not raise
    remove_member(10)
    assert get_member(10) is None


def test_remove_members_by_team_id():
    add_member(20, "Fay", "team_y")
    add_member(21, "Gus", "team_y")
    add_member(22, "Hank", "team_z")

    remove_members_by_team_id("team_y")
    assert get_team_members("team_y") == []
    # ensure other teams unaffected
    remaining = get_team_members("team_z")
    assert len(remaining) == 1 and remaining[0]["user_name"] == "Hank"
