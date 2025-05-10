from discord import Colour
from tinydb import Query
from db import db


teams_table = db.table("teams")
Q = Query()


def add_team(name: str, slug: str, role_id: int, role_colour: Colour):
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
    teams_table.remove(Q.slug == slug)

def get_team(team_id: str):
    return teams_table.get(Q.slug == team_id)


def get_teams():
    return teams_table.all()


def clear_pending_flag(slug: str):
    return teams_table.update({"pending": False}, Q.slug == slug)


def update_team_position(position, team_name):
    teams_table.update(
        {"pos": position, "pending": True},
        Q.slug == team_name,
    )
