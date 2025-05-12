import pytest
from db.meta_table import (
    set_meta,
    get_meta,
    get_channel_ids,
    get_proofs_channel_id,
    get_board_channel_id,
    set_board_message_id,
    get_board_message_id,
    CATEGORY_CHANNEL_ID,
    BOARD_CHANNEL_ID,
    PROOFS_CHANNEL_ID,
    COMMANDS_CHANNEL_ID,
    BOARD_MESSAGE_ID,
)
from db.client import db


@pytest.fixture(autouse=True)
def clear_meta():
    tbl = db.table("meta")
    tbl.truncate()
    yield
    tbl.truncate()


def test_get_meta_default():
    assert get_meta("nope") is None
    assert get_meta("nothing", default=42) == 42


def test_set_and_get_meta_new():
    set_meta("foo", "bar")
    assert get_meta("foo") == "bar"


def test_set_and_get_meta_update():
    set_meta("x", 1)
    assert get_meta("x") == 1
    set_meta("x", 2)
    assert get_meta("x") == 2


def test_get_channel_ids_empty():
    # all should default to None
    ids = get_channel_ids()
    assert ids == {"category": None, "board": None, "proofs": None, "cmd": None}


def test_get_channel_ids_populated():
    set_meta(CATEGORY_CHANNEL_ID, 1000)
    set_meta(BOARD_CHANNEL_ID, 2000)
    set_meta(PROOFS_CHANNEL_ID, 3000)
    set_meta(COMMANDS_CHANNEL_ID, 4000)
    ids = get_channel_ids()
    assert ids == {
        "category": 1000,
        "board": 2000,
        "proofs": 3000,
        "cmd": 4000,
    }


def test_special_getters_and_setters():
    # proofs channel
    set_meta(PROOFS_CHANNEL_ID, 555)
    assert get_proofs_channel_id() == 555

    # board channel
    set_meta(BOARD_CHANNEL_ID, 666)
    assert get_board_channel_id() == 666

    # board message
    assert get_board_message_id() is None
    set_board_message_id(777)
    assert get_board_message_id() == 777
