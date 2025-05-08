from datetime import datetime, timezone
import asyncio, secrets
from typing import Union

import discord

from db import (
    add_proof,
    clear_pending_flag,
    get_member,
    get_proofs_channel_id,
    get_team,
    list_proof_urls,
    log_roll,
    update_team_position,
)
from game_state import update_game_board

# ───────────────────────────── Dice roll lock ────────────────────────────────
team_locks: dict[str, asyncio.Lock] = {}


def get_team_lock(slug: str) -> asyncio.Lock:
    lock = team_locks.get(slug)
    if lock is None:
        lock = team_locks[slug] = asyncio.Lock()
    return lock


async def roll_dice_command(inter: discord.Interaction):
    await inter.response.defer()

    membership = get_member(inter.user.id)
    if not membership:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
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
        old_pos = team["pos"]
        new_pos = team["pos"] + die

        update_team_position(new_pos, team_name)

        log_roll(
            team_slug=team_name,
            user_id=inter.user.id,
            user_name=inter.user.display_name,
            die=die,
            pos_before=old_pos,
            pos_after=new_pos,
        )

    asyncio.create_task(update_game_board(inter.client))

    return await inter.followup.send(
        f"🎲 **{inter.user.display_name}** rolled a **{die}** for **{team['slug']}** "
        f"→ now on tile **{new_pos}**\n"
        f"(Use `/post` to post proof & `/complete` when you complete the tile.)"
    )


async def post_command(inter: discord.Interaction, proof: discord.Attachment):
    await inter.response.defer(ephemeral=True)

    membership = get_member(inter.user.id)
    if not membership:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )

    team_name = membership["team_slug"]
    team = get_team(team_name)
    if not team:
        return await inter.followup.send(
            "Your team is missing. Ping an admin.",
            ephemeral=True,
        )

    if not team["pending"]:
        return await inter.followup.send(
            "Can't submit proof if your team hasn't rolled yet.",
            ephemeral=True,
        )

    if proof.content_type != "image/jpeg" and proof.content_type != "image/png":
        return await inter.followup.send(
            "Only png and jpeg are supported.",
            ephemeral=True,
        )

    add_proof(
        team_slug=team_name,
        tile=team["pos"],
        url=proof.url,
        user_id=inter.user.id,
        user_name=inter.user.display_name,
    )

    return await inter.followup.send(
        "🖼️ Proof submitted — thanks!",
        ephemeral=True,
    )


async def complete_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True)

    membership = get_member(inter.user.id)
    if not membership:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )

    team_name = membership["team_slug"]
    team = get_team(team_name)
    role = inter.guild.get_role(team["role_id"])
    if not team:
        return await inter.followup.send(
            "Your team is missing. Ping an admin.",
            ephemeral=True,
        )

    if not team["pending"]:
        return await inter.followup.send(
            "Can't complete if your team hasn't rolled yet.",
            ephemeral=True,
        )

    if not list_proof_urls(team_slug=team_name, tile=team["pos"]):
        return await inter.followup.send(
            "No proof uploaded for this tile yet. "
            "Use `/post` to upload a screenshot first.",
            ephemeral=True,
        )

    clear_pending_flag(team_name)

    await inter.followup.send(
        f"✅ **{inter.user.display_name}** marked **tile {team['pos']} "
        f"complete** for **{team_name}** – you may `/roll` again!",
        ephemeral=True,
    )

    await send_proof_embed(
        guild=inter.guild,
        team_name=team_name,
        submitter=inter.user,
        tile_number=team["pos"],
    )


async def send_proof_embed(
    guild: discord.Guild,
    team_name: str,
    submitter: Union[discord.Member, discord.User],
    tile_number: int,
):
    proofs_channel_id = get_proofs_channel_id()
    channel = guild.get_channel(proofs_channel_id)
    if channel is None:
        raise RuntimeError("Proofs channel not found")

    urls = list_proof_urls(team_slug=team_name, tile=tile_number)
    if not urls:
        return

    team = get_team(team_name)
    role = guild.get_role(team["role_id"]) if team else None
    who = submitter.mention

    for i, url in enumerate(urls, start=1):
        embed = discord.Embed(
            title=f"{team_name} — tile {tile_number} (proof {i}/{len(urls)})",
            description=f"{role.mention if role else team_name} — submitted by {who}",
            colour=discord.Colour.blue(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_image(url=url)
        embed.set_footer(text="OSRS Tile-Race proof")
        await channel.send(embed=embed)
