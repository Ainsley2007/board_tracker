import asyncio
from datetime import datetime, timezone
import secrets
import discord

from commands.common import get_member, get_team
from db.rolls_table import log_roll
from db.teams_table import add_blacklist_charges
from db.teams_table import update_team_position
from game_state import update_game_board
from services.member_service import fetch_member
from services.team_service import (
    fetch_team_by_id,
)
from services.tiles_service import get_tile

team_locks: dict[str, asyncio.Lock] = {}


def get_team_lock(slug: str) -> asyncio.Lock:
    lock = team_locks.get(slug)
    if lock is None:
        lock = team_locks[slug] = asyncio.Lock()
    return lock


async def roll_dice_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=False)

    if not (member := await get_member(inter)):
        return
    if not (team := await get_team(inter, member)):
        return

    lock = get_team_lock(team.team_id)
    async with lock:
        if team.pending:
            return await inter.followup.send(
                "Your team has already rolled. Complete the tile first!",
                ephemeral=True,
            )

        if team.position >= 90:
            return await inter.followup.send(
                "Your team has finished the race! any further rolls are pointless.",
                ephemeral=True,
            )

        die, old_pos, rolled_pos = _roll_die(team.position)
        final_pos, moved_note = _apply_tile_effect(rolled_pos, member.team_id)
        await _update_state(
            member.team_id, old_pos, final_pos, die, inter.user, inter.client
        )

        tile_info = get_tile(final_pos) or {}
        await _send_roll_embed(inter, team, tile_info, die, moved_note)


def _roll_die(position):
    die = secrets.randbelow(6) + 1
    old_pos = position
    rolled_pos = min(old_pos + die, 90)
    return die, old_pos, rolled_pos


def _apply_tile_effect(rolled_pos: int, team_id: str) -> tuple[int, str]:
    final_pos = rolled_pos
    notes: list[str] = []

    for _ in range(20):
        redirected_pos, blacklist_note = _apply_blacklist_redirect(final_pos, team_id)
        if redirected_pos != final_pos:
            final_pos = redirected_pos
            if blacklist_note:
                notes.append(blacklist_note)
            continue

        effected_pos, effect_note = _apply_primary_tile_effect(final_pos, team_id)
        if effected_pos != final_pos:
            final_pos = effected_pos
            if effect_note:
                notes.append(effect_note)
            continue
        break

    return final_pos, "".join(notes)


def _apply_primary_tile_effect(rolled_pos: int, team_id: str) -> tuple[int, str]:
    tile = get_tile(rolled_pos) or {}
    if tile.get("type") == "RETURN":
        return _apply_return_tile_effect(tile, rolled_pos, team_id)
    return rolled_pos, ""


def _apply_return_tile_effect(tile, rolled_pos: int, team_id: str) -> tuple[int, str]:
    dest = tile.get("destination_id")
    if dest is None:
        return rolled_pos, ""
    charges = add_blacklist_charges(team_id, 1)
    return dest, f" ⏮️ Returned to {dest}. +1 blacklist charge ({charges})."


def _apply_blacklist_redirect(position: int, team_id: str) -> tuple[int, str]:
    team = fetch_team_by_id(team_id)
    if team is None or not team.blacklist_tiles:
        return position, ""
    if position >= 90:
        return position, ""

    steps = 0
    final_pos = position
    blacklisted = set(team.blacklist_tiles)
    while final_pos in blacklisted and final_pos < 90:
        final_pos = min(final_pos + 1, 90)
        steps += 1

    if steps == 0:
        return final_pos, ""
    if steps == 1:
        return final_pos, f" 🚫 Blacklist hit, moved to {final_pos}."
    return final_pos, f" 🚫 Blacklist chain skipped {steps} tiles to {final_pos}."



async def _update_state(team_id, old_pos, final_pos, die, user, bot):
    update_team_position(final_pos, team_id)
    log_roll(
        team_id=team_id,
        user_id=user.id,
        user_name=user.display_name,
        die=die,
        pos_before=old_pos,
        pos_after=final_pos,
    )
    asyncio.create_task(update_game_board(bot))


async def _send_roll_embed(inter, team, tile_info, die, moved_note):
    colour = discord.Colour(team.color) if team.color else discord.Colour.gold()
    tile_id = tile_info.get("id", team.position)
    description = tile_info.get("description", "No tile description available.")
    embed = discord.Embed(
        title=f"🎲 {inter.user.display_name} rolled a {die}!{moved_note}",
        colour=colour,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name=team.name)
    role = inter.guild.get_role(team.role_id)
    embed.add_field(name="**Team**", value=role.mention, inline=False)
    embed.add_field(name="**Tile**", value=f"`{tile_id}`", inline=False)
    embed.add_field(
        name="**Description**", value=f"`{description}`", inline=False
    )

    if url := tile_info.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    embed.set_footer(text="Use /post to upload proof, then /complete")

    return await inter.followup.send(embed=embed, ephemeral=False)
