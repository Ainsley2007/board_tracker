from datetime import datetime, timezone
import io
import asyncio, secrets
from typing import List, Union

import aiohttp
import discord

from db.db import (
    add_proof,
    clear_pending_flag,
    get_member,
    get_proofs_channel_id,
    list_proof_urls,
    log_roll,
    update_team_position,
)
from game_state import update_game_board
from services.member_service import fetch_member
from services.team_service import fetch_team_by_id
from tiles import get_tile

# ───────────────────────────── Dice roll lock ────────────────────────────────
team_locks: dict[str, asyncio.Lock] = {}


def get_team_lock(slug: str) -> asyncio.Lock:
    lock = team_locks.get(slug)
    if lock is None:
        lock = team_locks[slug] = asyncio.Lock()
    return lock


async def roll_dice_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=False)

    membership = get_member(inter.user.id)
    if not membership:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )

    team_name = membership["team_slug"]
    team = fetch_team_by_id(team_name)
    if not team:
        return await inter.followup.send(
            "Internal error: your team is missing. Ping an admin.",
            ephemeral=True,
        )

    lock = get_team_lock(team_name)

    async with lock:
        if team.pending:
            return await inter.followup.send(
                "Your team already rolled. Complete the tile first!",
                ephemeral=True,
            )

        die = secrets.randbelow(6) + 1
        old_pos = team.position
        new_pos = team.position + die

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

    role = inter.guild.get_role(team.role_id)
    tile_info = get_tile(new_pos)

    team_colour = discord.Colour(team.color) if team.color else discord.Colour.gold()

    embed = discord.Embed(
        title=f"🎲 {inter.user.global_name} rolled a {str(die)}",
        colour=team_colour,
        timestamp=datetime.now(timezone.utc),
    )

    embed.add_field(name="**Team**", value=role.mention, inline=False)
    embed.add_field(name="**Tile**", value=tile_info["id"], inline=False)
    embed.add_field(
        name="**Description**", value=tile_info["description"], inline=False
    )

    if url := tile_info.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    embed.set_footer(text="Use /post to upload proof, then /complete")

    return await inter.followup.send(embed=embed, ephemeral=False)


async def info_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True)

    member = fetch_member(inter.user.id)
    if not member:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )

    team = fetch_team_by_id(member.team_id)
    if not team:
        return await inter.followup.send(
            "Your team is missing. Ping an admin.",
            ephemeral=True,
        )

    tile = get_tile(team.position)

    embed = discord.Embed(title=tile.get("name"))
    embed.add_field(name="**Tile**", value=tile.get("id"), inline=False)
    embed.add_field(name="**Description**", value=tile.get("description"), inline=False)

    if url := tile.get("url"):
        embed.add_field(name="More info", value=f"<{url}>", inline=False)

    return await inter.followup.send(embed=embed)


async def post_command(inter: discord.Interaction, proof: discord.Attachment):
    await inter.response.defer(ephemeral=True)

    member = fetch_member(inter.user.id)
    if not member:
        return await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )

    team = fetch_team_by_id(member.team_id)
    if not team:
        return await inter.followup.send(
            "Your team is missing. Ping an admin.",
            ephemeral=True,
        )

    if not team.pending:
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
        team_slug=member.team_id,
        tile=team.position,
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
    team = fetch_team_by_id(team_name)
    if not team:
        return await inter.followup.send(
            "Your team is missing. Ping an admin.",
            ephemeral=True,
        )

    if not team.pending:
        return await inter.followup.send(
            "Can't complete if your team hasn't rolled yet.",
            ephemeral=True,
        )

    if not list_proof_urls(team_slug=team_name, tile=team.position):
        return await inter.followup.send(
            "No proof uploaded for this tile yet. "
            "Use `/post` to upload a screenshot first.",
            ephemeral=True,
        )

    clear_pending_flag(team_name)

    await inter.followup.send(
        f"✅ **{inter.user.display_name}** marked **tile {team.position} "
        f"complete** for **{team_name}** – you may `/roll` again!",
        ephemeral=True,
    )

    await send_proof_embed(
        guild=inter.guild,
        team_name=team_name,
        submitter=inter.user,
        tile_number=team.position,
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

    team = fetch_team_by_id(team_name)
    role = guild.get_role(team.role_id) if team else None
    who = submitter.mention

    header = f"{role.mention if role else team_name} — submitted by {submitter.mention}"
    return await send_proofs_as_attachments(channel, urls, header=header)

    embeds: list[discord.Embed] = []
    info_embed = discord.Embed(
        title=f"{team_name} — tile {tile_number}",
        description=f"{role.mention if role else team_name} — submitted by {who}",
        colour=discord.Colour.blue(),
        timestamp=datetime.now(timezone.utc),
    )
    info_embed.set_footer(text="OSRS Tile-Race proof")

    embeds.append(info_embed)

    for i, url in enumerate(urls, start=1):
        embed = discord.Embed(
            title=f"(proof {i}/{len(urls)})",
        )
        embed.set_image(url=url)
        embeds.append(embed)

    await channel.send(embeds=embeds)


async def send_proofs_as_attachments(
    channel: discord.TextChannel, urls: List[str], header: str = ""
) -> None:
    async with aiohttp.ClientSession() as session:
        files = []
        for i, url in enumerate(urls[:10], 1):
            async with session.get(url) as resp:
                data = await resp.read()

            # Use BytesIO so nothing is written to disk
            fp = io.BytesIO(data)
            fp.seek(0)
            # Guess a filename extension from the URL (Discord likes it)
            ext = url.rsplit(".", 1)[-1][:4] or "png"
            filename = f"proof_{i}.{ext}"
            files.append(discord.File(fp, filename=filename))

        await channel.send(content=header, files=files)
