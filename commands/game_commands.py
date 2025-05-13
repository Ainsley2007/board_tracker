from datetime import datetime, timezone
import io
import asyncio
from typing import List, Union

import aiohttp
import discord

from db.meta_table import get_proofs_channel_id
from db.proofs_table import add_proof, list_proof_urls, list_proofs

from db.teams_table import clear_pending_flag
from game_state import update_game_board
from services.member_service import fetch_member
from services.team_service import fetch_team_by_id
from tiles import get_tile


async def info_command(inter: discord.Interaction, tile_id: int):
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

    if tile_id is not None:
        tile = get_tile(tile_id)
    else:
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
        team_id=member.team_id,
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
            "Can't complete if your team hasn't rolled yet.",
            ephemeral=True,
        )

    if not list_proof_urls(team_id=member.team_id, tile=team.position):
        return await inter.followup.send(
            "No proof uploaded for this tile yet. "
            "Use `/post` to upload a screenshot first.",
            ephemeral=True,
        )

    clear_pending_flag(member.team_id)

    await inter.followup.send(
        f"✅ **{inter.user.display_name}** marked **tile {team.position} "
        f"complete** for **{team.name}** - you may `/roll` again!",
        ephemeral=True,
    )

    asyncio.create_task(update_game_board(inter.client))

    await send_proof_embed(
        inter=inter,
        team_id=team.team_id,
        tile_number=team.position,
    )


async def send_proof_embed(
    inter: discord.Interaction,
    team_id: str,
    tile_number: int,
):
    proofs_channel_id = get_proofs_channel_id()
    channel = inter.guild.get_channel(proofs_channel_id)
    if channel is None:
        raise RuntimeError("Proofs channel not found")

    proofs = list_proofs(team_id=team_id, tile=tile_number)
    if not proofs:
        return

    team = fetch_team_by_id(team_id)
    role = inter.guild.get_role(team.role_id) if team else None

    embeds: list[discord.Embed] = []
    info_embed = discord.Embed(
        title=f"{team.name} — tile {tile_number}",
        description=f"{role.mention if role else team.name}",
        colour=team.color,
    )
    info_embed.set_footer(text="OSRS Tile-Race proof")

    embeds.append(info_embed)

    for i, proof in enumerate(proofs, start=1):
        submitter = await inter.guild.fetch_member(proof["user_id"])
        embed = discord.Embed(
            title=f"(proof {i}/{len(proofs)})",
            timestamp=datetime.fromisoformat(proof["ts"]),
            color=team.color,
        )
        embed.add_field(name="Submitted by", value=submitter.mention)
        embed.set_image(url=proof["url"])
        embeds.append(embed)

    await channel.send(embeds=embeds)


async def send_proofs_as_attachments(
    channel: discord.TextChannel,
    urls: List[str],
    header: str = "",
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
