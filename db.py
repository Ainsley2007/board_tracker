from __future__ import annotations
from datetime import datetime, timezone

from discord import Colour
import discord

"""TinyDB helper layer – slugs, inserts, and pre‑built query objects."""

from pathlib import Path
from typing import Any, List

from tinydb import Query, TinyDB

from config import DB_PATH


db = TinyDB(Path(DB_PATH))

teams_table = db.table("teams")
members_table = db.table("members")
rolls_table = db.table("rolls")
proofs_table = db.table("proofs")
meta = db.table("meta")

Q = Query()


def set_meta(key: str, value):
    if meta.contains(Q.key == key):
        meta.update({"value": value}, Q.key == key)
    else:
        meta.insert({"key": key, "value": value})


def get_meta(key: str, default=None):
    row = meta.get(Q.key == key)
    return row["value"] if row else default


def get_channel_ids():
    return {
        "category": get_meta("tr_category_id"),
        "board": get_meta("tr_board_id"),
        "proofs": get_meta("tr_proofs_id"),
        "cmd": get_meta("tr_cmd_id"),
    }


def get_proofs_channel_id() -> int | None:
    return get_meta("tr_proofs_id")


def get_board_channel_id() -> int | None:
    return get_meta("tr_board_id")


def set_board_message_id(msg_id: int):
    set_meta("tr_board_msg_id", msg_id)


def get_board_message_id() -> int | None:
    return get_meta("tr_board_msg_id")


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_")


def add_team(name: str, slug: str, role_id: int, role_colour: Colour):
    if teams_table.contains(Q.slug == slug):
        raise ValueError("Team already exists")
    teams_table.insert(
        {
            "slug": slug,
            "name": name,
            "role_id": int(role_id),
            "pos": 0,
            "color": role_colour.value,
            "pending": False,
        }
    )


def remove_team(slug: str) -> tuple[int, int]:
    if not teams_table.contains(Q.slug == slug):
        raise ValueError("Team does not exist")

    members_removed = members_table.remove(Q.team_slug == slug)

    teams_removed = teams_table.remove(Q.slug == slug)

    return len(teams_removed), len(members_removed)


def get_team(slug: str):
    return teams_table.get(Q.slug == slug)


def get_teams():
    return {row["slug"]: row for row in teams_table.all()}


def clear_pending_flag(slug: str):
    return teams_table.update({"pending": False}, Q.slug == slug)


def get_team_members(slug: str):
    return members_table.search(Q.team_slug == slug)


def add_member(user_id: int, user_name, team_slug: str):
    # make sure the team exists
    if not teams_table.contains(Q.slug == team_slug):
        raise ValueError("Team does not exist")

    # prevent duplicates
    if members_table.contains(Q.user_id == int(user_id)):
        raise ValueError("User is already in a team")

    members_table.insert(
        {
            "user_id": int(user_id),
            "user_name": user_name,
            "team_slug": team_slug,
        }
    )


def get_member(user_id):
    return members_table.get(Q.user_id == user_id)


def remove_member(user_id: int):
    if not members_table.contains(Q.user_id == int(user_id)):
        raise ValueError("User is not in a team")

    removed_members = members_table.remove(Q.user_id == int(user_id))
    if not removed_members:
        raise ValueError("The member was not removed")


def update_team_position(position, team_name):
    teams_table.update(
        {"pos": position, "pending": True},
        Q.slug == team_name,
    )


def log_roll(
    *,
    team_slug: str,
    user_id: int,
    user_name: str,
    die: int,
    pos_before: int,
    pos_after: int,
):
    rolls_table.insert(
        {
            "team_slug": team_slug,
            "user_id": user_id,
            "user_name": user_name,
            "die": die,
            "pos_before": pos_before,
            "pos_after": pos_after,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def last_roll(team_slug: str) -> dict | None:
    rows = rolls_table.search(Q.team_slug == team_slug)
    return max(rows, key=lambda r: r["ts"]) if rows else None


def add_proof(
    team_slug: str,
    tile: int,
    url: str,
    user_id: int,
    user_name: str,
):
    proofs_table.insert(
        {
            "team_slug": team_slug,
            "tile": tile,
            "url": url,
            "user_id": user_id,
            "user_name": user_name,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def list_proof_urls(
    team_slug: str,
    tile: int,
) -> List[str] | None:

    query = (Q.team_slug == team_slug) & (Q.tile == tile)

    rows = proofs_table.search(query)
    rows.sort(key=lambda r: r["ts"])  # oldest → newest
    urls = [r["url"] for r in rows]

    return urls
