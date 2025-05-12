from __future__ import annotations
from dataclasses import dataclass
from typing import List

from db import teams_table as tt
from db import members_table as mt


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
    return [Member.from_doc(doc) for doc in mt.get_team_members(team_slug)]


def fetch_member(user_id: int) -> Member | None:
    if member_doc := mt.get_member(user_id):
        return Member.from_doc(member_doc)
    return None


def add_member(user_id: int, user_name: str, team_id: str):
    if tt.get_team(team_id) is None:
        raise ValueError("The team you're trying to add this user to doesn't exist")

    if fetch_member(user_id) is not None:
        raise ValueError("User is already in a team")

    mt.add_member(user_id, user_name, team_id)


def remove_member(user_id: int):
    if fetch_member(user_id) is None:
        raise ValueError("User is not in a team")

    mt.remove_member(user_id)
