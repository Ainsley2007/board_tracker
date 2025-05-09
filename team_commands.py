import asyncio
import discord
from db import add_team, remove_team, slugify
from game_state import update_game_board
from team_service import fetch_team_by_id


async def create_team_command(inter: discord.Interaction, name: str):
    guild = inter.guild
    role_colour = discord.Colour.random()
    team_id = slugify(name)

    if fetch_team_by_id(team_id) != None:
        return await inter.response.send_message(
            f"Team **{name}** already exists.",
            ephemeral=True,
        )

    role = await guild.create_role(
        name=name,
        colour=role_colour,
        reason="Tile‑race team",
        hoist=True,
    )
    add_team(name, team_id, role.id, role_colour)

    asyncio.create_task(update_game_board(inter.client))

    await inter.response.send_message(
        f"Team **{role.mention}** created!",
        allowed_mentions=discord.AllowedMentions(roles=True),
    )


async def delete_team_command(inter: discord.Interaction, role: discord.Role):
    team_id = slugify(role.name)
    team = fetch_team_by_id(team_id)

    if team == None:
        return await inter.response.send_message(
            f"Team **{role.name}** doesn't exist.",
            ephemeral=True,
        )

    await role.delete(reason="Remove team")

    remove_team(team_id)

    asyncio.create_task(update_game_board(inter.client))

    await inter.response.send_message(
        f"Team **{team.name}** removed!",
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
