from tinydb import Query
from db import db

CATEGORY_CHANNEL_ID = "tr_category_id"

BOARD_CHANNEL_ID = "tr_board_id"
BOARD_MESSAGE_ID = "tr_board_msg_id"

PROOFS_CHANNEL_ID = "tr_proofs_id"
COMMANDS_CHANNEL_ID = "tr_cmd_id"

meta_table = db.table("meta")
Q = Query()


def set_meta(key: str, value):
    if meta_table.contains(Q.key == key):
        meta_table.update({"value": value}, Q.key == key)
    else:
        meta_table.insert({"key": key, "value": value})


def get_meta(key: str, default=None):
    row = meta_table.get(Q.key == key)
    return row["value"] if row else default


def get_channel_ids():
    return {
        "category": get_meta(CATEGORY_CHANNEL_ID),
        "board": get_meta(BOARD_CHANNEL_ID),
        "proofs": get_meta(PROOFS_CHANNEL_ID),
        "cmd": get_meta(COMMANDS_CHANNEL_ID),
    }


def get_proofs_channel_id() -> int | None:
    return get_meta(PROOFS_CHANNEL_ID)


def get_board_channel_id() -> int | None:
    return get_meta(BOARD_CHANNEL_ID)


def set_board_message_id(msg_id: int):
    set_meta(BOARD_MESSAGE_ID, msg_id)


def get_board_message_id() -> int | None:
    return get_meta(BOARD_MESSAGE_ID)
