import pytest
from discord import Colour

import services.member_service as ms
from services.member_service import Member


class DummyTT:
    """Minimal stub of teams_table: only get_team(slug)."""

    def __init__(self):
        self.teams = {}

    def get_team(self, slug):
        return self.teams.get(slug)


class DummyMT:
    """Minimal stub of members_table: tracks data in a dict."""

    def __init__(self):
        self.rows = {}
        self.removed = []

    def get_member(self, user_id):
        return self.rows.get(user_id)

    def get_team_members(self, slug):
        return [r for r in self.rows.values() if r["team_slug"] == slug]

    def add_member(self, user_id, user_name, team_slug):
        self.rows[user_id] = {
            "user_id": user_id,
            "user_name": user_name,
            "team_slug": team_slug,
        }

    def remove_member(self, user_id):
        self.removed.append(user_id)
        self.rows.pop(user_id, None)

    def remove_members_by_team_id(self, team_id):
        to_delete = [uid for uid, r in self.rows.items() if r["team_slug"] == team_id]
        for uid in to_delete:
            self.rows.pop(uid)
            self.removed.append(uid)


@pytest.fixture(autouse=True)
def patch_tables(monkeypatch):
    dummy_tt = DummyTT()
    dummy_mt = DummyMT()
    # override the modules inside member_service
    monkeypatch.setattr(ms, "tt", dummy_tt)
    monkeypatch.setattr(ms, "mt", dummy_mt)
    yield
    # no teardown needed (new Dummy per test)


def test_member_repr_and_str():
    m = Member(user_id=42, name="Alice", team_id="red")
    assert str(m) == "Alice"
    assert repr(m) == "Alice"


def test_fetch_member_not_exists():
    assert ms.fetch_member(99) is None


def test_fetch_member_exists():
    # seed dummy
    ms.mt.rows[5] = {"user_id": 5, "user_name": "Bob", "team_slug": "blue"}
    m = ms.fetch_member(5)
    assert isinstance(m, Member)
    assert m.user_id == 5
    assert m.name == "Bob"
    assert m.team_id == "blue"


def test_fetch_team_members_empty():
    assert ms.fetch_team_members("nope") == []


def test_fetch_team_members_some():
    # seed two members in same team, one in different
    ms.mt.rows[1] = {"user_id": 1, "user_name": "X", "team_slug": "t1"}
    ms.mt.rows[2] = {"user_id": 2, "user_name": "Y", "team_slug": "t1"}
    ms.mt.rows[3] = {"user_id": 3, "user_name": "Z", "team_slug": "t2"}
    lst = ms.fetch_team_members("t1")
    assert {m.user_id for m in lst} == {1, 2}
    assert all(isinstance(m, Member) for m in lst)


def test_add_member_team_missing():
    # no teams in DummyTT
    with pytest.raises(ValueError) as exc:
        ms.add_member(10, "New", "ghost")
    assert "doesn't exist" in str(exc.value)


def test_add_member_already_in_team():
    # seed team and member
    ms.tt.teams["red"] = {"slug": "red"}
    ms.mt.rows[7] = {"user_id": 7, "user_name": "Old", "team_slug": "red"}
    with pytest.raises(ValueError) as exc:
        ms.add_member(7, "Old", "red")
    assert "already in a team" in str(exc.value)


def test_add_member_success():
    ms.tt.teams["green"] = {"slug": "green"}
    ms.add_member(11, "Bravo", "green")
    # now DummyMT has the row
    assert 11 in ms.mt.rows
    row = ms.mt.rows[11]
    assert row["user_name"] == "Bravo" and row["team_slug"] == "green"


def test_remove_member_not_exists():
    with pytest.raises(ValueError) as exc:
        ms.remove_member(123)
    assert "not in a team" in str(exc.value)


def test_remove_member_success():
    ms.tt.teams["blue"] = {"slug": "blue"}
    ms.mt.rows[8] = {"user_id": 8, "user_name": "Anna", "team_slug": "blue"}
    ms.remove_member(8)
    # DummyMT recorded removal
    assert 8 in ms.mt.removed
    # row deleted
    assert 8 not in ms.mt.rows
