from __future__ import annotations

import logging
import os

import discord
from discord import app_commands

from config import DISCORD_TOKEN
from db.db import get_channel_ids, set_meta
from game_commands import (
    complete_command,
    info_command,
    post_command,
    roll_dice_command,
)
from game_state import update_game_board
from commands.member_commands import add_member_command, remove_member_command
from commands.team_commands import create_team_command, delete_team_command

# ───────────────────────────── logging ────────────────────────────────
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("tile_race_bot")

# ───────────────────────────── discord.py ─────────────────────────────
intents = discord.Intents.default()
# Enable privileged members intent **only if** user asked for it and has
# toggled it on in the Developer Portal (otherwise the gateway disconnects).
if os.getenv("ENABLE_MEMBERS_INTENT") == "1":
    intents.members = True

bot = discord.Client(intents=intents)
cmds = app_commands.CommandTree(bot)


@cmds.command(
    name="create-team",
    description="Create a new race team & role",
)
@app_commands.describe(name="Team name (role name)")
@app_commands.default_permissions(administrator=True)
async def create_team(
    inter: discord.Interaction,
    name: str,
):
    return await create_team_command(inter, name)


@cmds.command(name="delete-team", description="Delete a team")
@app_commands.describe(name="Team name (role name)")
@app_commands.default_permissions(administrator=True)
async def delete_team(
    inter: discord.Interaction,
    name: discord.Role,
):
    return await delete_team_command(inter, name)


@cmds.command(
    name="add-member",
    description="Assign a Discord user to a team role",
)
@app_commands.describe(user="User to add", team="Team role to assign")
@app_commands.default_permissions(administrator=True)
async def add_member_cmd(
    inter: discord.Interaction,
    user: discord.Member,
    team: discord.Role,
):
    return await add_member_command(inter, user, team)


@cmds.command(
    name="remove-member",
    description="Remove a Discord user from a team role",
)
@app_commands.describe(user="User to remove", team="Team to be removed from")
@app_commands.default_permissions(administrator=True)
async def remove_member_cmd(
    inter: discord.Interaction,
    user: discord.Member,
    team: discord.Role,
):
    return await remove_member_command(inter, user, team)


@cmds.command(name="roll", description="Roll the dice for your team")
async def roll_cmd(inter: discord.Interaction):
    return await roll_dice_command(inter)


@cmds.command(
    name="tile-info", description="Get more info about your team's current tile"
)
async def info_cmd(inter: discord.Interaction):
    return await info_command(inter)


@cmds.command(name="post", description="Upload a screenshot for the current tile")
@app_commands.describe(proof="Image or short video that shows your progress")
async def post_cmd(inter: discord.Interaction, proof: discord.Attachment):
    return await post_command(inter, proof)


@cmds.command(name="complete", description="Complete the current tile for your team")
async def complete_cmd(inter: discord.Interaction):
    return await complete_command(inter)


DESIRED = {
    "category": "Tile Race",
    "board": "tr-board",
    "proofs": "tr-proofs",
    "cmd": "tr-commands",
}


@bot.event
async def on_ready():
    guilds = [g async for g in bot.fetch_guilds(limit=None)]
    for g in guilds:
        await ensure_tile_race_channels(g)

    log.info("Logged in as %s (ID %s)", bot.user, bot.user.id)
    try:
        await cmds.sync()
        log.info("Commands synced globally (may take up to 1 h)")
    except Exception:
        log.exception("Slash command sync failed")


async def ensure_tile_race_channels(guild: discord.Guild):
    ids = get_channel_ids()

    cat_id = ids.get("category")
    category = await guild.fetch_channel(cat_id) if cat_id else None

    if category is None:
        category = await guild.create_category(DESIRED["category"])

    set_meta("tr_category_id", category.id)

    async def need(name_key):
        chan = await guild.fetch_channel(ids[name_key]) if ids[name_key] else None
        if chan is None:
            chan = await guild.create_text_channel(
                DESIRED[name_key],
                category=category,
                topic="OSRS Tile-Race" if name_key != "proofs" else "Screenshots only",
            )
        set_meta(f"tr_{name_key}_id", chan.id)
        return chan

    await need("board")
    await need("proofs")
    await need("cmd")

    await update_game_board(bot)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN missing in .env")

    bot.run(DISCORD_TOKEN, reconnect=True)
