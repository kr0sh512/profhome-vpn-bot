from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    admin_ids: set[int]
    marzban_url: str
    marzban_username: str
    marzban_password: str
    payment_text: str
    database_path: str = "bot.sqlite3"

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        data: dict[str, Any] = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            telegram_bot_token=str(data["telegram_bot_token"]),
            admin_ids={int(item) for item in data.get("admin_ids", [])},
            marzban_url=str(data["marzban_url"]).rstrip("/"),
            marzban_username=str(data["marzban_username"]),
            marzban_password=str(data["marzban_password"]),
            payment_text=str(data["payment_text"]),
            database_path=str(data.get("database_path", "bot.sqlite3")),
        )
