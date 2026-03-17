from datetime import datetime, timezone

from db.client import db


pet_proofs_table = db.table("pet_proofs")


def add_pet_proof(
    team_id: str,
    url: str,
    user_id: int,
    user_name: str,
):
    pet_proofs_table.insert(
        {
            "team_id": team_id,
            "url": url,
            "user_id": user_id,
            "user_name": user_name,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    )
