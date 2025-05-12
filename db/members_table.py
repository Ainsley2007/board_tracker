from db.client import db, Q


members_table = db.table("members")


def get_team_members(slug: str):
    return members_table.search(Q.team_slug == slug)


def get_member(user_id: int):
    return members_table.get(Q.user_id == user_id)


def add_member(user_id: int, user_name, team_slug: str):
    members_table.insert(
        {
            "user_id": int(user_id),
            "user_name": user_name,
            "team_slug": team_slug,
        }
    )


def remove_members_by_team_id(team_id: str):
    members_table.remove(Q.team_slug == team_id)


def remove_member(user_id: int):
    members_table.remove(Q.user_id == user_id)
