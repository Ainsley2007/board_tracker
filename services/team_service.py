from dataclasses import dataclass
from typing import List

from discord import Colour

from db import teams_table as tt
from db import members_table as mt


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


def create_team(name: str, team_id: str, role_id: int, role_colour: Colour):
    if tt.get_team(team_id) is not None:
        raise ValueError(f"Team **{name}** already exists")

    tt.add_team(name, team_id, role_id, role_colour.value)

    doc = tt.get_team(team_id)
    return Team.from_doc(doc)

def remove_team(team_id):
    if tt.get_team(team_id) is None:
        raise ValueError(f"Team doesn't exist")
    
    mt.remove_members_by_team_id(team_id)
    tt.remove_team(team_id)


def fetch_teams() -> List[Team]:
    return [Team.from_doc(doc) for doc in tt.get_teams()]


def fetch_team_by_id(team_id):
    doc = tt.get_team(team_id)
    if doc is None:
        return None
    return Team.from_doc(doc)
