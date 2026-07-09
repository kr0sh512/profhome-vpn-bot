from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_token TEXT NOT NULL UNIQUE,
                    invite_created_at INTEGER NOT NULL,
                    invite_created_by_admin_id INTEGER NOT NULL,
                    tg_user_id INTEGER UNIQUE,
                    tg_username TEXT,
                    tg_first_name TEXT,
                    tg_last_name TEXT,
                    tg_phone TEXT,
                    marzban_username TEXT UNIQUE,
                    activated_at INTEGER
                )
                """
            )
            conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def create_invite(self, *, token: str, admin_id: int, created_at: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (invite_token, invite_created_at, invite_created_by_admin_id)
                VALUES (?, ?, ?)
                """,
                (token, created_at, admin_id),
            )
            conn.commit()

    def get_by_token(self, token: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE invite_token = ?", (token,)).fetchone()
        return self._row_to_dict(row)

    def get_by_tg_user_id(self, tg_user_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE tg_user_id = ?", (tg_user_id,)).fetchone()
        return self._row_to_dict(row)

    def activate_invite(
        self,
        *,
        token: str,
        tg_user_id: int,
        tg_username: str | None,
        tg_first_name: str | None,
        tg_last_name: str | None,
        tg_phone: str | None,
        marzban_username: str,
        activated_at: int,
    ) -> None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE invite_token = ?", (token,)).fetchone()
            if row is None:
                raise ValueError("invite token not found")
            if row["tg_user_id"] is not None:
                raise ValueError("invite token already used")
            conn.execute(
                """
                UPDATE users
                SET tg_user_id = ?,
                    tg_username = ?,
                    tg_first_name = ?,
                    tg_last_name = ?,
                    tg_phone = ?,
                    marzban_username = ?,
                    activated_at = ?
                WHERE invite_token = ?
                """,
                (
                    tg_user_id,
                    tg_username,
                    tg_first_name,
                    tg_last_name,
                    tg_phone,
                    marzban_username,
                    activated_at,
                    token,
                ),
            )
            conn.commit()

    def update_phone(self, *, tg_user_id: int, phone: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE users SET tg_phone = ? WHERE tg_user_id = ?", (phone, tg_user_id))
            conn.commit()
