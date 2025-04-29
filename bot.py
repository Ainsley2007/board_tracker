from __future__ import annotations

import logging
import os

import discord
from discord import app_commands

from config import DISCORD_TOKEN

from game_commands import roll_dice_command
from member_commands import add_member_command, remove_member_command
from team_commands import create_team_command, delete_team_command

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


@bot.event
async def on_ready():
    log.info("Logged in as %s (ID %s)", bot.user, bot.user.id)
    try:
        await cmds.sync()  # <— global sync only
        log.info("Commands synced globally (may take up to 1 h)")
    except Exception:
        log.exception("Slash command sync failed")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN missing in .env")

    bot.run(DISCORD_TOKEN, reconnect=True)
