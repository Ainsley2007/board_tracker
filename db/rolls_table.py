from datetime import datetime, timezone
from db.client import db, Q

rolls_table = db.table("rolls")


def log_roll(
    *,
    team_id: str,
    user_id: int,
    user_name: str,
    die: int,
    pos_before: int,
    pos_after: int,
):
    rolls_table.insert(
        {
            "team_id": team_id,
            "user_id": user_id,
            "user_name": user_name,
            "die": die,
            "pos_before": pos_before,
            "pos_after": pos_after,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )


def last_roll(team_id: str) -> dict | None:
    rows = rolls_table.search(Q.team_id == team_id)
    return max(rows, key=lambda r: r["ts"]) if rows else None


def count_return_landings(team_id: str, return_tile_id: int) -> int:
    """
    Return how many times `team_id` has landed on the RETURN tile with id `return_tile_id`.
    """
    rows = rolls_table.search(Q.team_id == team_id)
    # pos_before + die is the tile they landed on
    return sum(1 for r in rows if r["pos_before"] + r["die"] == return_tile_id)
