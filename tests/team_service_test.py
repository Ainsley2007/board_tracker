# test_team_service.py
import pytest
from discord import Colour

import services.team_service as ts
from services.team_service import Team


@pytest.fixture(autouse=True)
def clear_db(monkeypatch):
    # ensure we start with a clean slate for each test
    # replace tt.get_team, tt.add_team, tt.remove_team, tt.get_teams, mt.remove_members_by_team_id
    class DummyTable:
        def __init__(self):
            self.rows = {}

        def get_team(self, slug):
            return self.rows.get(slug)

        def add_team(self, name, slug, role_id, colour):
            self.rows[slug] = {
                "slug": slug,
                "name": name,
                "role_id": role_id,
                "pos": 0,
                "color": colour.value if hasattr(colour, "value") else colour,
                "pending": False,
            }

        def remove_team(self, slug):
            self.rows.pop(slug, None)

        def get_teams(self):
            return list(self.rows.values())

    dummy = DummyTable()

    # monkeypatch team table
    monkeypatch.setattr(ts, "tt", dummy)

    # and members_table for remove_team
    class DummyMembers:
        def __init__(self):
            self.called = False

        def remove_members_by_team_id(self, team_id):
            self.called = True

    dummy_members = DummyMembers()
    monkeypatch.setattr(ts, "mt", dummy_members)
    yield


def test_create_team_success(monkeypatch):
    # first call sees no existing team, then add_team, then get_team returns the row
    name, slug, role_id, colour = "Alpha", "alpha", 123, Colour.red()
    team = ts.create_team(name=name, team_id=slug, role_id=role_id, role_colour=colour)
    assert isinstance(team, Team)
    assert team.team_id == slug
    assert team.name == name
    assert team.role_id == role_id
    assert team.position == 0
    assert team.color == colour.value


def test_create_team_duplicate(monkeypatch):
    # simulate existing team
    dummy = ts.tt
    dummy.rows["dup"] = {
        "slug": "dup",
        "name": "Dup",
        "role_id": 1,
        "pos": 0,
        "color": 0,
        "pending": False,
    }
    with pytest.raises(ValueError) as exc:
        ts.create_team(name="Dup", team_id="dup", role_id=1, role_colour=Colour.blue())
    assert "already exists" in str(exc.value)


def test_remove_team_not_exists():
    with pytest.raises(ValueError) as exc:
        ts.remove_team("nope")
    assert "doesn't exist" in str(exc.value)


def test_remove_team_success():
    dummy = ts.tt
    # add team and members
    dummy.rows["rm"] = {
        "slug": "rm",
        "name": "Rm",
        "role_id": 2,
        "pos": 5,
        "color": 0,
        "pending": False,
    }
    # call remove
    ts.remove_team("rm")
    assert "rm" not in dummy.rows
    assert ts.mt.called is True


def test_fetch_teams_and_sorted():
    dummy = ts.tt
    # add several teams
    dummy.add_team("One", "one", 1, Colour.green())
    dummy.rows["one"]["pos"] = 10
    dummy.add_team("Two", "two", 2, Colour.green())
    dummy.rows["two"]["pos"] = 20
    teams = ts.fetch_teams()
    assert {t.team_id for t in teams} == {"one", "two"}
    sorted_ = ts.fetch_sorted_teams()
    assert [t.team_id for t in sorted_] == ["two", "one"]


def test_fetch_team_by_id():
    dummy = ts.tt
    dummy.add_team("X", "x", 5, Colour.gold())
    t = ts.fetch_team_by_id("x")
    assert isinstance(t, Team)
    assert t.team_id == "x"
    assert ts.fetch_team_by_id("no") is None


def test_fetch_team_position():
    dummy = ts.tt
    # create three teams at positions 5, 15, 10
    dummy.add_team("A", "a", 1, Colour.red())
    dummy.rows["a"]["pos"] = 5
    dummy.add_team("B", "b", 2, Colour.red())
    dummy.rows["b"]["pos"] = 15
    dummy.add_team("C", "c", 3, Colour.red())
    dummy.rows["c"]["pos"] = 10
    # sorted desc → B(15), C(10), A(5)
    assert ts.fetch_team_position("b") == 1
    assert ts.fetch_team_position("c") == 2
    assert ts.fetch_team_position("a") == 3
    with pytest.raises(ValueError):
        ts.fetch_team_position("z")
