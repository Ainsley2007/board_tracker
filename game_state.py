import discord
from board.board_detector import detect_tiles_by_bg
from board.visualize import paint_team_circles
from db import (
    get_board_channel_id,
    get_board_message_id,
    get_teams,
    set_board_message_id,
)

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

    # 1 ▸ regenerate PNG ------------------------------------------------
    teams = get_teams()
    tiles = detect_tiles_by_bg("assets/background.png", "assets/board.png")
    paint_team_circles("assets/board.png", tiles, teams, out_path=BOARD_PNG)

    # 2 ▸ edit or send message -----------------------------------------
    msg_id = get_board_message_id()
    message = None
    if msg_id:
        try:
            message = await channel.fetch_message(msg_id)
        except discord.NotFound:
            message = None

    if message:
        await message.edit(attachments=[discord.File(BOARD_PNG)])
    else:
        sent = await channel.send(file=discord.File(BOARD_PNG))
        set_board_message_id(sent.id)
