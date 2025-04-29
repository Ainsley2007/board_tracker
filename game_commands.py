import asyncio, secrets

import discord

from db import get_member, get_team, update_team_position

# ───────────────────────────── Dice roll lock ────────────────────────────────
team_locks: dict[str, asyncio.Lock] = {}


def get_team_lock(slug: str) -> asyncio.Lock:
    lock = team_locks.get(slug)
    if lock is None:
        lock = team_locks[slug] = asyncio.Lock()
    return lock


async def roll_dice_command(inter: discord.Interaction):
    """Allow exactly one unresolved roll per team."""
    await inter.response.defer()

    membership = get_member(inter.user.id)
    if not membership:
        return await inter.followup.send(
            "You’re not on a team. Ask an admin to add you.", ephemeral=True
        )

    team_name = membership["team_slug"]
    team = get_team(team_name)
    if not team:
        return await inter.followup.send(
            "Internal error: your team is missing. Ping an admin.",
            ephemeral=True,
        )

    lock = get_team_lock(team_name)

    async with lock:
        if team["pending"]:
            return await inter.followup.send(
                "Your team already rolled. Complete the tile first!",
            )

        die = secrets.randbelow(6) + 1

        new_pos = team["pos"] + die
        update_team_position(new_pos, team_name)

    # 5 ▸ public announcement (in the channel the command was used)
    await inter.followup.send(
        f"🎲 **{inter.user.display_name}** rolled a **{die}** for **{team['slug']}** "
        f"→ now on tile **{new_pos}**\n"
        f"(Use `/complete <proof>` when you finish the tile.)"
    )
