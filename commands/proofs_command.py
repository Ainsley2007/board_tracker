from datetime import datetime

import discord

from commands.common import get_member, get_team
from db.proofs_table import list_proofs


async def proofs_command(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True)

    if not (member := await get_member(inter)):
        return
    if not (team := await get_team(inter, member)):
        return

    if not team.pending:
        return await inter.followup.send(
            "Your team needs to `/roll` for a new tile",
            ephemeral=True,
        )

    if not (proofs := list_proofs(team_id=team.team_id, tile=team.position)):
        return await inter.followup.send(
            "No proofs uploaded yet for your team's current tile",
            ephemeral=True,
        )

    # build all embeds
    embeds: list[discord.Embed] = []
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

    for i in range(0, len(embeds), 10):
        batch = embeds[i : i + 10]
        await inter.followup.send(embeds=batch, ephemeral=True)
