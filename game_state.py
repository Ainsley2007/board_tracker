import discord
from board.board_detector import detect_tiles_by_bg
from board.visualize import paint_team_circles
from db import (
    get_board_channel_id,
    get_board_message_id,
    set_board_message_id,
)
from member_service import fetch_team_members
from team_service import fetch_teams
from tiles import get_tile

BOARD_PNG = "assets/board_state.png"


async def update_game_board(bot: discord.Client) -> None:
    chan_id = get_board_channel_id()
    if not chan_id:
        print("[warn] Board channel ID not set; skipping board update")
        return

    channel = bot.get_channel(chan_id) or await bot.fetch_channel(chan_id)
    if channel is None or not isinstance(channel, discord.TextChannel):
        print("[warn] Board channel not found or not a text channel")
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
            embed.add_field(name="**Tile**", value=team.position, inline=True)
            embed.add_field(name="**Assignment**", value=tile["name"], inline=True)
        else:
            embed.add_field(
                name="**Tile**", value="Your team needs to roll!", inline=True
            )
            embed.add_field(name="**Assignment**", value="/", inline=True)

        embed.add_field(name="**Members**", value=members_str[:-2])

    if message:
        await message.edit(embed=embed, attachments=[discord.File(BOARD_PNG)])
    else:
        sent = await channel.send(embed=embed, file=discord.File(BOARD_PNG))
        set_board_message_id(sent.id)
