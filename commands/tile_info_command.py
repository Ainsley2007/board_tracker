import discord

from commands.common import get_member, get_team
from services.tiles_service import get_tile


async def info_command(inter, tile_id: int):
    await inter.response.defer(ephemeral=True)

    if tile_id is not None:
        tile = get_tile(tile_id)
    else:
        member = await get_member(inter)
        if member is None:
            return await inter.followup.send(
                "Provide a tile number when using `/tile-info` if you're not on a team.",
                ephemeral=True,
            )
        team = await get_team(inter, member)
        if team is None:
            return
        tile = get_tile(team.position)

    if tile is None:
        return await inter.followup.send(
            "Invalid tile number.",
            ephemeral=True,
        )

    embed = discord.Embed(title=tile.get("name"))
    embed.add_field(
        name="**Tile**",
        value=f"`{tile.get('id')}`",
        inline=False,
    )
    embed.add_field(
        name="**Name**",
        value=f"`{tile.get('name')}`",
        inline=False,
    )
    embed.add_field(
        name="**Description**",
        value=f"`{tile.get('description')}`",
        inline=False,
    )

    if url := tile.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    return await inter.followup.send(embed=embed)
