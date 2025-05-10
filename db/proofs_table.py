from datetime import datetime, timezone
from typing import List
from tinydb import Query

from db import db


proofs_table = db.table("proofs")
Q = Query()


def add_proof(
    team_slug: str,
    tile: int,
    url: str,
    user_id: int,
    user_name: str,
):
    proofs_table.insert(
        {
            "team_slug": team_slug,
            "tile": tile,
            "url": url,
            "user_id": user_id,
            "user_name": user_name,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def list_proof_urls(
    team_slug: str,
    tile: int,
) -> List[str] | None:

    query = (Q.team_slug == team_slug) & (Q.tile == tile)

    rows = proofs_table.search(query)
    rows.sort(key=lambda r: r["ts"])  # oldest → newest
    urls = [r["url"] for r in rows]

    return urls
