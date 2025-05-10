from __future__ import annotations

from pathlib import Path

from tinydb import Query, TinyDB

from config import DB_PATH


db = TinyDB(Path(DB_PATH))

Q = Query()
