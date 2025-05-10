import asyncio
import discord
from game_state import update_game_board
from services.team_service import create_team, fetch_team_by_id, remove_team
from util.utils import slugify


async def create_team_command(inter: discord.Interaction, name: str):
    guild = inter.guild
    team_id = slugify(name)
    role_colour = discord.Colour.random()

    role = await guild.create_role(
        name=name,
        colour=role_colour,
        reason="Tile-race team",
        hoist=True,
    )

    try:
        create_team(name, team_id, role.id, role_colour)
    except ValueError as ve:
        await role.delete()
        return await inter.response.send_message(str(ve), ephemeral=True)

    asyncio.create_task(update_game_board(inter.client))

    await inter.response.send_message(
        f"Team **{role.mention}** created!",
        allowed_mentions=discord.AllowedMentions(roles=True),
    )


async def delete_team_command(inter: discord.Interaction, role: discord.Role):
    team_id = slugify(role.name)

    try:
        remove_team(team_id)
    except ValueError as ve:
        return await inter.response.send_message(str(ve), ephemeral=True)

    await role.delete(reason="Remove team")

    asyncio.create_task(update_game_board(inter.client))

    await inter.response.send_message("Team removed!")
