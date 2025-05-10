from datetime import datetime, timezone
from tinydb import Query
from db import db


rolls_table = db.table("rolls")
Q = Query()


def log_roll(
    *,
    team_slug: str,
    user_id: int,
    user_name: str,
    die: int,
    pos_before: int,
    pos_after: int,
):
    rolls_table.insert(
        {
            "team_slug": team_slug,
            "user_id": user_id,
            "user_name": user_name,
            "die": die,
            "pos_before": pos_before,
            "pos_after": pos_after,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def last_roll(team_slug: str) -> dict | None:
    rows = rolls_table.search(Q.team_slug == team_slug)
    return max(rows, key=lambda r: r["ts"]) if rows else None
