import pytest
from datetime import datetime, timezone, timedelta

import db.proofs_table as pt
from db.proofs_table import proofs_table, add_proof, list_proof_urls


@pytest.fixture(autouse=True)
def clear_proofs():
    proofs_table.truncate()
    yield
    proofs_table.truncate()


def test_add_and_list_single():
    add_proof("teamA", 1, "http://url1", 10, "Alice")
    urls = list_proof_urls("teamA", 1)
    assert urls == ["http://url1"]


def test_list_empty_returns_empty_list():
    assert list_proof_urls("no_team", 5) == []


def test_filter_by_team_and_tile():
    # insert for matching team/tile
    add_proof("teamX", 2, "u1", 1, "Bob")
    add_proof("teamX", 3, "u2", 2, "Cara")
    add_proof("teamY", 2, "u3", 3, "Dan")
    # only u1 matches teamX & tile=2
    assert list_proof_urls("teamX", 2) == ["u1"]
    # tile mismatch returns []
    assert list_proof_urls("teamX", 99) == []
    # team mismatch
    assert list_proof_urls("zzz", 2) == []


def test_list_sorted_by_timestamp():
    # manually insert out-of-order timestamps
    now = datetime.now(timezone.utc)
    # older first
    proofs_table.insert(
        {
            "team_id": "teamSort",
            "tile": 7,
            "url": "old",
            "user_id": 5,
            "user_name": "E",
            "ts": (now - timedelta(seconds=10)).isoformat(timespec="seconds"),
        }
    )
    proofs_table.insert(
        {
            "team_id": "teamSort",
            "tile": 7,
            "url": "new",
            "user_id": 6,
            "user_name": "F",
            "ts": (now + timedelta(seconds=10)).isoformat(timespec="seconds"),
        }
    )
    # even though 'new' was inserted second, sorting by ts must put 'old' first
    assert list_proof_urls("teamSort", 7) == ["old", "new"]


def test_timestamps_are_iso_and_utc():
    add_proof("teamUtc", 4, "uX", 11, "Zulu")
    row = proofs_table.all()[0]
    ts_str = row["ts"]
    # must end with "+00:00" and contain a 'T'
    assert ts_str.endswith("+00:00")
    assert "T" in ts_str
    # and be parseable back to a datetime in UTC
    dt = datetime.fromisoformat(ts_str)
    assert dt.tzinfo == timezone.utc
