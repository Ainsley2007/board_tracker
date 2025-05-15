import asyncio
from datetime import datetime, timezone
import secrets
import discord

from commands.common import get_member, get_team
from db.rolls_table import log_roll
from db.teams_table import update_team_position
from game_state import update_game_board
from services.member_service import fetch_member
from services.team_service import (
    fetch_sorted_teams,
    fetch_team_by_id,
)
from tiles import get_tile

team_locks: dict[str, asyncio.Lock] = {}


def get_team_lock(slug: str) -> asyncio.Lock:
    lock = team_locks.get(slug)
    if lock is None:
        lock = team_locks[slug] = asyncio.Lock()
    return lock


async def roll_dice_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=False)

    if not (member := await get_member(inter)): return
    if not (team := await get_team(inter, member)): return

    lock = get_team_lock(team.team_id)
    async with lock:
        if team.pending:
            return await inter.followup.send(
                "Your team already rolled. Complete the tile first!",
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
    tile = get_tile(rolled_pos) or {}
    tile_type = tile.get("type")
    final_pos = rolled_pos

    if tile_type == "RETURN":
        return _apply_return_tile_effect(tile, rolled_pos, team_id)

    if tile_type == "SKIP":
        return _apply_skip_tile_effect(tile, rolled_pos, team_id)

    return final_pos, ""


def _apply_return_tile_effect(tile, rolled_pos, team_id) -> tuple[int, str]:
    dest = tile.get("destination_id")
    if dest is None:
        return rolled_pos, ""  # no return to apply

    moved_info = f", ↩️ Returned to {dest}"
    sorted_teams = fetch_sorted_teams()

    # guard against too few teams
    if len(sorted_teams) < 2:
        return dest, moved_info

    last = sorted_teams[-1]
    second_last = sorted_teams[-2]
    gap = second_last.position - last.position

    # only skip if you're actually last and gap ≥ 5
    if last.team_id == team_id and gap >= 5:
        final = rolled_pos + 1
        moved_info = " Since you're in last place you skip the return tile."
        return final, moved_info

    return dest, moved_info


def _apply_skip_tile_effect(tile, rolled_pos, team_id) -> tuple[int, str]:
    dest = tile.get("destination_id")
    if dest is None:
        return rolled_pos, ""  # nothing to do if no destination

    # default: skip ahead to dest
    final_pos = dest
    moved_info = f", ⏭️ Skipped to {dest}"

    # fetch standings
    sorted_teams = fetch_sorted_teams()  # highest-pos first
    if len(sorted_teams) < 2:
        return final_pos, moved_info

    leader = sorted_teams[0]
    second = sorted_teams[1]
    gap = leader.position - second.position

    # leader penalty: if you're 1st by ≥5, lose the skip and only advance 1 tile
    if leader.team_id == team_id and gap >= 5:
        final_pos = rolled_pos + 1
        moved_info = " As 1st place with a big lead, you only skip 1 tile."
    return final_pos, moved_info


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
    embed = discord.Embed(
        title=f"🎲 {inter.user.display_name} rolled a {die}!{moved_note}",
        colour=colour,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_author(name=team.name)
    role = inter.guild.get_role(team.role_id)
    embed.add_field(name="**Team**", value=role.mention, inline=False)
    embed.add_field(name="**Tile**", value=tile_info["id"], inline=False)
    embed.add_field(
        name="**Description**", value=tile_info["description"], inline=False
    )

    if url := tile_info.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    embed.set_footer(text="Use /post to upload proof, then /complete")

    return await inter.followup.send(embed=embed, ephemeral=False)
