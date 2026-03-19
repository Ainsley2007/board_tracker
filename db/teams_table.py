from discord import Colour
from db.client import db, Q


teams_table = db.table("teams")
DEFAULT_BLACKLIST_CHARGES = 1
MAX_RETURN_BLACKLIST_GRANTS = 2


def add_team(name: str, slug: str, role_id: int, role_colour: Colour):
    teams_table.insert(
        {
            "slug": slug,
            "name": name,
            "role_id": int(role_id),
            "pos": 0,
            "color": role_colour.value,
            "pending": False,
            "blacklist_tiles": [],
            "blacklist_charges": DEFAULT_BLACKLIST_CHARGES,
        }
    )


def remove_team(slug: str):
    teams_table.remove(Q.slug == slug)


def get_team(team_id: str):
    return _normalize_team_doc(teams_table.get(Q.slug == team_id))


def get_teams():
    return [_normalize_team_doc(doc) for doc in teams_table.all()]


def clear_pending_flag(slug: str):
    return teams_table.update({"pending": False}, Q.slug == slug)


def update_team_position(position, team_name):
    teams_table.update(
        {"pos": position, "pending": True},
        Q.slug == team_name,
    )


def get_blacklist_tiles(slug: str) -> list[int]:
    row = get_team(slug)
    if row is None:
        return []
    return [int(tile) for tile in row.get("blacklist_tiles", [])]


def add_blacklist_tile(slug: str, tile_id: int) -> list[int] | None:
    row = get_team(slug)
    if row is None:
        return None
    tiles = [int(tile) for tile in row.get("blacklist_tiles", [])]
    if tile_id not in tiles:
        tiles.append(tile_id)
        tiles.sort()
        teams_table.update({"blacklist_tiles": tiles}, Q.slug == slug)
    return tiles


def replace_blacklist_tile(slug: str, old_tile: int, new_tile: int) -> list[int] | None:
    row = get_team(slug)
    if row is None:
        return None
    tiles = [int(tile) for tile in row.get("blacklist_tiles", [])]
    if old_tile not in tiles:
        return None
    tiles = [new_tile if tile == old_tile else tile for tile in tiles]
    tiles = sorted(set(tiles))
    teams_table.update({"blacklist_tiles": tiles}, Q.slug == slug)
    return tiles


def get_blacklist_charges(slug: str) -> int:
    row = get_team(slug)
    if row is None:
        return 0
    return int(row.get("blacklist_charges", DEFAULT_BLACKLIST_CHARGES))


def add_blacklist_charges(slug: str, amount: int = 1) -> int:
    charges = get_blacklist_charges(slug) + amount
    teams_table.update({"blacklist_charges": charges}, Q.slug == slug)
    return charges


def increment_return_blacklist_grant_if_allowed(slug: str) -> tuple[int, bool]:
    row = get_team(slug)
    if row is None:
        return 0, False
    grants = int(row.get("return_blacklist_grants", 0))
    if grants >= MAX_RETURN_BLACKLIST_GRANTS:
        return get_blacklist_charges(slug), False
    charges = get_blacklist_charges(slug) + 1
    teams_table.update(
        {
            "blacklist_charges": charges,
            "return_blacklist_grants": grants + 1,
        },
        Q.slug == slug,
    )
    return charges, True


def consume_blacklist_charge(slug: str) -> int | None:
    row = get_team(slug)
    if row is None:
        return None
    charges = int(row.get("blacklist_charges", DEFAULT_BLACKLIST_CHARGES))
    if charges <= 0:
        return None
    updated = charges - 1
    teams_table.update({"blacklist_charges": updated}, Q.slug == slug)
    return updated


def _normalize_team_doc(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    updates = {}
    if "blacklist_tiles" not in doc:
        legacy = doc.get("blacklist_tile")
        updates["blacklist_tiles"] = [legacy] if legacy is not None else []
    if "blacklist_charges" not in doc:
        updates["blacklist_charges"] = DEFAULT_BLACKLIST_CHARGES
    if updates:
        teams_table.update(updates, Q.slug == doc["slug"])
        doc = {**doc, **updates}
    return doc
