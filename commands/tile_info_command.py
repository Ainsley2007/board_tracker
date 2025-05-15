import discord

from commands.common import get_member, get_team
from tiles import get_tile


async def info_command(inter, tile_id: int):
    await inter.response.defer(ephemeral=True)

    if not (member := await get_member(inter)): return
    if not (team := await get_team(inter, member)): return

    if tile_id is not None:
        tile = get_tile(tile_id)
    else:
        tile = get_tile(team.position)

    embed = discord.Embed(title=tile.get("name"))
    embed.add_field(name="**Tile**", value=tile.get("id"), inline=False)
    embed.add_field(name="**Description**", value=tile.get("description"), inline=False)

    if url := tile.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    return await inter.followup.send(embed=embed)

