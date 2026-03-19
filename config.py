from __future__ import annotations

"""Configuration loader (reads .env file at project root)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env into process env – overrides not set in shell
load_dotenv(dotenv_path=Path(__file__).with_suffix(".env").resolve().parent / ".env")

DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
DB_PATH: Path = Path(os.getenv("DB_PATH", "assets/state.json"))


def _parse_admin_user_ids() -> frozenset[int]:
    raw = os.getenv("ADMIN_USER_ID", "").strip()
    if not raw:
        return frozenset()
    out: list[int] = []
    for part in raw.split(","):
        p = part.strip()
        if p.isdigit():
            out.append(int(p))
    return frozenset(out)


ADMIN_USER_IDS: frozenset[int] = _parse_admin_user_ids()
