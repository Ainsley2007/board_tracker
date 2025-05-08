import discord
from db import add_team, get_team, remove_team, slugify


async def create_team_command(inter: discord.Interaction, name: str):
    guild = inter.guild
    role_colour = discord.Colour.random()
    team_name = slugify(name)

    if get_team(team_name) != None:
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
    add_team(name, team_name, role.id, role_colour)

    await inter.response.send_message(
        f"Team **{role.mention}** created!",
        allowed_mentions=discord.AllowedMentions(roles=True),
    )


async def delete_team_command(inter: discord.Interaction, role: discord.Role):
    team_name = slugify(role.name)
    team = get_team(team_name)

    if team == None:
        return await inter.response.send_message(
            f"Team **{role.name}** doesn't exist.",
            ephemeral=True,
        )

    await role.delete(reason="Remove team")

    remove_team(team_name)

    await inter.response.send_message(
        f"Team **{team_name}** removed!",
        allowed_mentions=discord.AllowedMentions(roles=True),
    )
