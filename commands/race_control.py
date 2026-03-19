import discord

from config import ADMIN_USER_IDS
from db.meta_table import is_race_started, set_race_started


async def start_tile_race_command(inter: discord.Interaction):
    if not ADMIN_USER_IDS:
        return await inter.response.send_message(
            "Bot misconfigured: set `ADMIN_USER_ID` in `.env`.",
            ephemeral=True,
        )
    if inter.user.id not in ADMIN_USER_IDS:
        return await inter.response.send_message(
            "You cannot use this command.",
            ephemeral=True,
        )
    if is_race_started():
        return await inter.response.send_message(
            "The tile race is already live.",
            ephemeral=True,
        )
    set_race_started(True)
    return await inter.response.send_message(
        "Tile race is live. Teams can use `/roll`, `/post`, `/complete`, and other game commands.",
        ephemeral=True,
    )
