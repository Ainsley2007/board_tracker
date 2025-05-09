from dataclasses import dataclass
from typing import List

from db import get_team, get_teams


@dataclass(slots=True, frozen=True)
class Team:
    team_id: str
    role_id: int
    name: str
    position: int
    color: int
    pending: bool

    @classmethod
    def from_doc(cls, doc: dict) -> "Team":
        return cls(
            team_id=doc["slug"],
            role_id=int(doc["role_id"]),
            name=doc["name"],
            position=int(doc["pos"]),
            color=int(doc["color"]),
            pending=bool(doc["pending"]),
        )


def fetch_teams() -> List[Team]:
    return [Team.from_doc(doc) for doc in get_teams()]

def fetch_team_by_id(team_id):
    doc = get_team(team_id)
    if doc is None:
        return None
    return Team.from_doc(doc)