from util.logger import log
import discord
from board.board_detector import detect_tiles_by_bg
from board.visualize import paint_team_circles
from db.meta_table import (
    get_board_channel_id,
    get_board_message_id,
    set_board_message_id,
)
from services.member_service import fetch_team_members
from services.team_service import fetch_teams
from services.tiles_service import get_tile

BOARD_PNG = "assets/board_state.png"


async def update_game_board(bot: discord.Client) -> None:
    chan_id = get_board_channel_id()
    if not chan_id:
        log.warning("Board channel ID not set; skipping board update")
        return

    channel = bot.get_channel(chan_id) or await bot.fetch_channel(chan_id)
    if channel is None or not isinstance(channel, discord.TextChannel):
        log.warning("Board channel not found or not a text channel")
        return

    teams = fetch_teams()
    if teams == None:
        return

    tiles = detect_tiles_by_bg("assets/background.png", "assets/board.png")
    paint_team_circles("assets/board.png", tiles, teams, out_path=BOARD_PNG)

    msg_id = get_board_message_id()
    message = None
    if msg_id:
        try:
            message = await channel.fetch_message(msg_id)
        except discord.NotFound:
            message = None

    embed = discord.Embed(title="Board State")

    for team in teams:
        tile = get_tile(team.position)
        role = bot.guilds[0].get_role(team.role_id)
        team_members = fetch_team_members(team.team_id)
        members_str = ""
        for member in team_members:
            members_str += f"{member.name}, "

        embed.add_field(name="", value=role.mention, inline=False)

        if team.pending:
            embed.add_field(name="**Tile**", value=f"`{team.position}`", inline=True)
            embed.add_field(
                name="**Assignment**", value=f"`{tile["name"]}`", inline=True
            )
        else:
            embed.add_field(
                name="**Tile**", value="`Your team needs to roll!`", inline=True
            )
            embed.add_field(name="**Assignment**", value="`/`", inline=True)

        if len(members_str) > 0:
            members_str = members_str[:-2]
            members_str = f"`{members_str}`"
            embed.add_field(name="**Members**", value=members_str)
        else:
            embed.add_field(name="**Members**", value="`/`")

    if message:
        await message.edit(embed=embed, attachments=[discord.File(BOARD_PNG)])
    else:
        sent = await channel.send(embed=embed, file=discord.File(BOARD_PNG))
        set_board_message_id(sent.id)
