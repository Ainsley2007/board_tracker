from services.member_service import fetch_member, Member
from services.team_service import fetch_team_by_id, Team


async def get_member(inter) -> Member:
    m = fetch_member(inter.user.id)
    if not m:
        await inter.followup.send(
            "You're not on a team. Ask an admin to add you.", ephemeral=True
        )
    return m


async def get_team(inter, member) -> Team:
    t = fetch_team_by_id(member.team_id)
    if not t:
        await inter.followup.send(
            "Internal error: your team is missing. Ping an admin.", ephemeral=True
        )
    return t
