import asyncio
import discord

from commands.common import get_member, get_team
from db.teams_table import (
    add_blacklist_tile,
    consume_blacklist_charge,
    get_blacklist_charges,
    replace_blacklist_tile,
)
from game_state import update_game_board
from services.tiles_service import get_tile


async def blacklist_command(inter: discord.Interaction, tile_nr: int):
    await inter.response.defer(ephemeral=True)

    if not (member := await get_member(inter)):
        return
    if not (team := await get_team(inter, member)):
        return
    error = _validate_new_blacklist_tile(team.position, tile_nr, team.blacklist_tiles)
    if error:
        return await inter.followup.send(error, ephemeral=True)

    remaining = consume_blacklist_charge(member.team_id)
    if remaining is None:
        charges = get_blacklist_charges(member.team_id)
        return await inter.followup.send(
            f"Your team has no blacklist charges left (`{charges}`).",
            ephemeral=True,
        )

    updated_tiles = add_blacklist_tile(member.team_id, tile_nr) or []
    asyncio.create_task(update_game_board(inter.client))
    return await inter.followup.send(
        f"🛑 Added tile `{tile_nr}` to blacklist. "
        f"Charges left: `{remaining}`. "
        f"Blacklisted: `{_format_tiles(updated_tiles)}`.",
        ephemeral=True,
    )


async def change_blacklist_command(
    inter: discord.Interaction,
    old_tile_nr: int,
    new_tile_nr: int,
):
    await inter.response.defer(ephemeral=True)

    if not (member := await get_member(inter)):
        return
    if not (team := await get_team(inter, member)):
        return
    if not team.blacklist_tiles:
        return await inter.followup.send(
            "Your team has no active blacklist yet. Use `/blacklist` first.",
            ephemeral=True,
        )
    if old_tile_nr not in team.blacklist_tiles:
        return await inter.followup.send(
            f"Tile `{old_tile_nr}` is not currently blacklisted.",
            ephemeral=True,
        )
    if old_tile_nr <= team.position:
        return await inter.followup.send(
            f"You already passed tile `{old_tile_nr}` and can no longer change it.",
            ephemeral=True,
        )
    if old_tile_nr == new_tile_nr:
        return await inter.followup.send(
            "New tile must be different from the current blacklisted tile.",
            ephemeral=True,
        )

    existing_other_tiles = [tile for tile in team.blacklist_tiles if tile != old_tile_nr]
    error = _validate_new_blacklist_tile(team.position, new_tile_nr, existing_other_tiles)
    if error:
        return await inter.followup.send(error, ephemeral=True)

    remaining = consume_blacklist_charge(member.team_id)
    if remaining is None:
        charges = get_blacklist_charges(member.team_id)
        return await inter.followup.send(
            f"Your team has no blacklist charges left (`{charges}`).",
            ephemeral=True,
        )

    updated_tiles = replace_blacklist_tile(member.team_id, old_tile_nr, new_tile_nr) or []
    asyncio.create_task(update_game_board(inter.client))
    return await inter.followup.send(
        f"🔁 Changed blacklist tile `{old_tile_nr}` -> `{new_tile_nr}`. "
        f"Charges left: `{remaining}`. "
        f"Blacklisted: `{_format_tiles(updated_tiles)}`.",
        ephemeral=True,
    )


def _validate_new_blacklist_tile(
    team_position: int,
    tile_nr: int,
    existing_tiles: list[int],
) -> str | None:
    if get_tile(tile_nr) is None:
        return "Invalid tile number."
    if tile_nr in (0, 90):
        return "You cannot blacklist tile `0` or tile `90`."
    if tile_nr <= team_position:
        return (
            f"Tile must be after your current team position (`{team_position}`)."
        )
    if tile_nr in existing_tiles:
        return f"Tile `{tile_nr}` is already blacklisted."
    return None


def _format_tiles(tiles: list[int]) -> str:
    return ", ".join(str(tile) for tile in sorted(tiles)) if tiles else "/"
