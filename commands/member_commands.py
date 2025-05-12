import discord

from services.member_service import add_member, fetch_team_members, remove_member
from services.team_service import fetch_team_by_id
from util.utils import slugify


async def add_member_command(
    inter: discord.Interaction,
    user: discord.Member,
    role: discord.Role,
):
    team_id = slugify(role.name)
    team = fetch_team_by_id(team_id)

    if not team or team.role_id != role.id:
        return await inter.response.send_message(
            "That role is not a registered race team.",
            ephemeral=True,
        )

    other_members = fetch_team_members(team_id)

    try:
        add_member(user.id, user.display_name, team_id)
    except ValueError as ve:
        return await inter.response.send_message(str(ve), ephemeral=True)

    await user.add_roles(role, reason="Added to tile-race team")

    await inter.response.send_message(
        f"{user.mention} added to **{team.name}**, along with {other_members}!",
        allowed_mentions=discord.AllowedMentions(users=True, roles=True),
    )


async def remove_member_command(
    inter: discord.Interaction,
    user: discord.Member,
    role: discord.Role,
):
    try:
        remove_member(user.id)
    except ValueError as ve:
        return await inter.response.send_message(str(ve), ephemeral=True)

    try:
        await user.remove_roles(role, reason="removed from tile-race team")
    except discord.Forbidden:
        return await inter.response.send_message(
            "I don't have permission to remove that role.",
            ephemeral=True,
        )

    await inter.response.send_message(
        f"{user.name} has been removed from {role}",
    )
