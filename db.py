from __future__ import annotations

from discord import Colour

"""TinyDB helper layer – slugs, inserts, and pre‑built query objects."""

from pathlib import Path
from typing import Any

from tinydb import Query, TinyDB

from config import DB_PATH


db = TinyDB(Path(DB_PATH))
teams_table = db.table("teams")
members_table = db.table("members")

Q = Query()


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_")


def add_team(slug: str, role_id: int, role_colour: Colour) -> None:
    if teams_table.contains(Q.slug == slug):
        raise ValueError("Team already exists")
    teams_table.insert(
        {
            "slug": slug,
            "role_id": int(role_id),
            "pos": 0,
            "color": role_colour.value,
            "pending": False,
        }
    )

    # ---------- teams & cascade delete --------------------------------------


def remove_team(slug: str) -> tuple[int, int]:
    if not teams_table.contains(Q.slug == slug):
        raise ValueError("Team does not exist")

    members_removed = members_table.remove(Q.team_slug == slug)

    teams_removed = teams_table.remove(Q.slug == slug)

    return len(teams_removed), len(members_removed)


def get_team(slug: str) -> dict[str, Any] | None:
    return teams_table.get(Q.slug == slug)


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
