import asyncio
import discord

from game_state import update_game_board
from services.team_service import create_team, remove_team
from util.logger import log
from util.utils import slugify


async def create_team_command(inter, name: str):
    await inter.response.defer(ephemeral=True)

    guild = inter.guild
    team_id = slugify(name)
    role_colour = discord.Colour.random(seed=name)

    role = await guild.create_role(
        name=name,
        colour=role_colour,
        reason="Tile-race team",
        hoist=False,
    )

    try:
        create_team(name, team_id, role.id, role_colour)
    except ValueError as ve:
        await role.delete()
        log.error(str(ve))
        return await inter.followup.send(str(ve), ephemeral=True)

    log.info(f"successfully created the team: {team_id}")
    asyncio.create_task(update_game_board(inter.client))

    return await inter.followup.send(
        f"Team **{role.mention}** created!",
        allowed_mentions=discord.AllowedMentions(roles=True),
        ephemeral=True,
    )


async def delete_team_command(inter, role: discord.Role):
    await inter.response.defer(ephemeral=True)

    team_id = slugify(role.name)

    try:
        remove_team(team_id)
    except ValueError as ve:
        return await inter.followup.send(str(ve), ephemeral=True)

    await role.delete(reason="Remove team")

    log.info(f"successfully removed the team: {team_id}")
    asyncio.create_task(update_game_board(inter.client))

    return await inter.followup.send("Team removed!", ephemeral=True)
