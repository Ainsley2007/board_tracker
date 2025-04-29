import discord

from db import add_member, get_team, get_team_members, remove_member, slugify


async def add_member_command(
    inter: discord.Interaction,
    user: discord.Member,
    team: discord.Role,
):
    slug = slugify(team.name)
    team_row = get_team(slug)
    if not team_row or team_row.get("role_id") != team.id:
        return await inter.response.send_message(
            "That role is not a registered race team.",
            ephemeral=True,
        )

    other_members = get_team_members(slug)

    try:
        add_member(user.id, user.display_name, slug)
    except ValueError as ve:
        return await inter.response.send_message(f"An error occurred: {ve}")

    try:
        await user.add_roles(team, reason="Added to tile-race team")
    except discord.Forbidden:
        return await inter.response.send_message(
            "I don't have permission to add that role.",
            ephemeral=True,
        )

    await inter.response.send_message(
        f"{user.mention} added to **{team.name}**, along with {list(map(lambda m: m["user_name"], other_members))}!",
        allowed_mentions=discord.AllowedMentions(users=True, roles=True),
    )


async def remove_member_command(
    inter: discord.Interaction,
    user: discord.Member,
    team: discord.Role,
):
    try:
        remove_member(user.id)
    except ValueError as ve:
        return await inter.response.send_message(
            f"An error occurred: {ve}",
            ephemeral=True,
        )

    try:
        await user.remove_roles(team, reason="removed from tile-race team")
    except discord.Forbidden:
        return await inter.response.send_message(
            "I don't have permission to remove that role.",
            ephemeral=True,
        )

    await inter.response.send_message(
        f"{user.name} has been removed from {team}",
        ephemeral=True,
    )
