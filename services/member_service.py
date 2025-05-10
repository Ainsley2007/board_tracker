from __future__ import annotations
from dataclasses import dataclass
from typing import List

from db.members_table import get_member, get_team_members
from db.teams_table import get_team


@dataclass(slots=True, frozen=True)
class Member:
    user_id: int
    name: str
    team_id: str

    @classmethod
    def from_doc(cls, doc: dict) -> "Member":
        return cls(
            user_id=int(doc["user_id"]),
            name=doc["user_name"],
            team_id=doc["team_slug"],
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


def fetch_team_members(team_slug: str) -> List[Member]:
    return [Member.from_doc(doc) for doc in get_team_members(team_slug)]


def fetch_member(user_id: int) -> Member | None:
    if member_doc := get_member(user_id):
        return None

    return Member.from_doc(member_doc)


def add_member(user_id: int, user_name, team_id: str):
    if team := get_team(team_id):
        return None
    add_member(user_id, user_name, team_id)
