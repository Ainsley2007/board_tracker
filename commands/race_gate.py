import discord

from db.meta_table import is_race_started


async def ensure_tile_race_live(inter: discord.Interaction) -> bool:
    if is_race_started():
        return True
    await inter.response.send_message(
        "The tile race has not started yet. Wait for the organizer to run `/start-tile-race`.",
        ephemeral=True,
    )
    return False
