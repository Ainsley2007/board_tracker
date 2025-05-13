from datetime import datetime, timezone
from typing import List

from db.client import Q, db


proofs_table = db.table("proofs")


def add_proof(
    team_id: str,
    tile: int,
    url: str,
    user_id: int,
    user_name: str,
):
    proofs_table.insert(
        {
            "team_id": team_id,
            "tile": tile,
            "url": url,
            "user_id": user_id,
            "user_name": user_name,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def list_proof_urls(
    team_id: str,
    tile: int,
) -> List[str] | None:

    query = (Q.team_id == team_id) & (Q.tile == tile)

    rows = proofs_table.search(query)
    rows.sort(key=lambda r: r["ts"])  # oldest → newest
    urls = [r["url"] for r in rows]

    return urls


def list_proofs(
    team_id: str,
    tile: int,
):
    query = (Q.team_id == team_id) & (Q.tile == tile)
    rows = proofs_table.search(query)
    rows.sort(key=lambda r: r["ts"])

    return rows
