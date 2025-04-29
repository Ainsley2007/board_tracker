from __future__ import annotations

"""Configuration loader (reads .env file at project root)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from .env into process env – overrides not set in shell
load_dotenv(dotenv_path=Path(__file__).with_suffix(".env").resolve().parent / ".env")

DISCORD_TOKEN: str | None = os.getenv("DISCORD_TOKEN")
DB_PATH: Path = Path(os.getenv("DB_PATH", "assets/state.json"))
