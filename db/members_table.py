from tinydb import Query
from db import db


members_table = db.table("members")
Q = Query()


def get_team_members(slug: str):
    return members_table.search(Q.team_slug == slug)


def get_member(user_id):
    return members_table.get(Q.user_id == user_id)


def add_member(user_id: int, user_name, team_slug: str):
    if not teams_table.contains(Q.slug == team_slug):
        raise ValueError("Team does not exist")

    if members_table.contains(Q.user_id == int(user_id)):
        raise ValueError("User is already in a team")

    members_table.insert(
        {
            "user_id": int(user_id),
            "user_name": user_name,
            "team_slug": team_slug,
        }
    )

def remove_members_by_team_id(team_id):
    members_table.remove(Q.team_slug == team_id)

def remove_member(user_id: int):
    if not members_table.contains(Q.user_id == int(user_id)):
        raise ValueError("User is not in a team")

    removed_members = members_table.remove(Q.user_id == int(user_id))
    if not removed_members:
        raise ValueError("The member was not removed")
