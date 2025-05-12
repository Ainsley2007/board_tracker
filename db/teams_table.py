from discord import Colour
from db.client import db, Q


teams_table = db.table("teams")
RETURN_TILES = [24, 46, 72, 89]


def add_team(name: str, slug: str, role_id: int, role_colour: Colour):
    teams_table.insert(
        {
            "slug": slug,
            "name": name,
            "role_id": int(role_id),
            "pos": 0,
            "return_mask": 0,
            "color": role_colour.value,
            "pending": False,
        }
    )


def remove_team(slug: str):
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


def has_returned(slug: str, tile_id: int) -> bool:
    idx = RETURN_TILES.index(tile_id)
    if idx is None:
        return False
    mask = teams_table.get(Q.slug == slug).get("return_mask", 0)
    return bool(mask & (1 << idx))


def mark_returned(slug: str, tile_id: int) -> None:
    idx = RETURN_TILES.index(tile_id)
    if idx is None:
        return
    row = teams_table.get(Q.slug == slug)
    mask = row.get("return_mask", 0) | (1 << idx)
    teams_table.update({"return_mask": mask}, Q.slug == slug)
