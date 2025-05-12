import pytest
from datetime import datetime, timezone, timedelta

from db.client import db
from db.rolls_table import log_roll, last_roll, rolls_table


@pytest.fixture(autouse=True)
def clear_rolls_table():
    rolls_table.truncate()
    yield
    rolls_table.truncate()


def test_last_roll_empty():
    assert last_roll("no_team") is None


def test_log_and_last_roll_single():
    log_roll(
        team_id="T1", user_id=11, user_name="Alice", die=4, pos_before=0, pos_after=4
    )
    row = last_roll("T1")
    assert row is not None
    assert row["team_id"] == "T1"
    assert row["user_id"] == 11
    assert row["user_name"] == "Alice"
    assert row["die"] == 4
    assert row["pos_before"] == 0
    assert row["pos_after"] == 4
    # timestamp is ISO and in UTC
    ts_str = row["ts"]
    assert "T" in ts_str and ts_str.endswith("+00:00")
    # parse it back
    dt = datetime.fromisoformat(ts_str)
    assert dt.tzinfo == timezone.utc


def test_last_roll_filters_by_team():
    # two teams each logging once
    log_roll(team_id="A", user_id=1, user_name="X", die=1, pos_before=0, pos_after=1)
    log_roll(team_id="B", user_id=2, user_name="Y", die=2, pos_before=0, pos_after=2)
    # last_roll for "A" must be the first row
    rA = last_roll("A")
    assert rA["user_name"] == "X"
    # last_roll for "B" is the second
    rB = last_roll("B")
    assert rB["user_name"] == "Y"


def test_last_roll_multiple_timestamps_ordering():
    # manually insert with custom timestamps
    now = datetime.now(timezone.utc)
    early = (now - timedelta(seconds=10)).isoformat(timespec="seconds")
    late = (now + timedelta(seconds=10)).isoformat(timespec="seconds")

    rolls_table.insert(
        {
            "team_id": "Z",
            "user_id": 9,
            "user_name": "E",
            "die": 5,
            "pos_before": 0,
            "pos_after": 5,
            "ts": early,
        }
    )
    rolls_table.insert(
        {
            "team_id": "Z",
            "user_id": 10,
            "user_name": "F",
            "die": 6,
            "pos_before": 5,
            "pos_after": 11,
            "ts": late,
        }
    )

    latest = last_roll("Z")
    assert latest["user_id"] == 10
    assert latest["user_name"] == "F"


def test_logs_do_not_collide_on_same_second():
    # if two logs happen in the same second, max() picks one but both exist
    # force two inserts with identical ts
    ts_str = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for uid in (21, 22):
        rolls_table.insert(
            {
                "team_id": "C",
                "user_id": uid,
                "user_name": f"U{uid}",
                "die": 1,
                "pos_before": 0,
                "pos_after": 1,
                "ts": ts_str,
            }
        )
    last = last_roll("C")
    assert last["ts"] == ts_str
    assert last["user_id"] in (21, 22)  # one of them
