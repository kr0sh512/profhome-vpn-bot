from __future__ import annotations

import math
import time
from datetime import datetime, timezone

SECONDS_PER_DAY = 24 * 60 * 60
DAYS_PER_MONTH = 30
SECONDS_PER_MONTH = DAYS_PER_MONTH * SECONDS_PER_DAY
GIB = 1024 * 1024 * 1024
TRIAL_DAYS = 3
TRIAL_TRAFFIC_BYTES = 10 * GIB
PAID_TRAFFIC_BYTES = 50 * GIB


def now_ts() -> int:
    return int(time.time())


def format_marzban_username(tg_user_id: int) -> str:
    return f"tg{tg_user_id}"


def add_days_from_base(*, current_expire: int | None, days: int, now: int | None = None) -> int:
    current = now_ts() if now is None else now
    base = current_expire if current_expire and current_expire > current else current
    return int(base + days * SECONDS_PER_DAY)


def calculate_reset_expire(*, expire: int | None, now: int | None = None) -> tuple[int, int]:
    current = now_ts() if now is None else now
    if not expire or expire <= current:
        return current, 0
    remaining = expire - current
    full_months = math.floor(remaining / SECONDS_PER_MONTH)
    return int(current + full_months * SECONDS_PER_MONTH), full_months


def build_marzban_note(
    *,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
    phone: str | None,
) -> str:
    lines: list[str] = []
    if first_name:
        lines.append(f"First name: {first_name}")
    if last_name:
        lines.append(f"Last name: {last_name}")
    if username:
        normalized = username if username.startswith("@") else f"@{username}"
        lines.append(f"Username: {normalized}")
    if phone:
        lines.append(f"Phone: {phone}")
    return "\n".join(lines)


def bytes_to_human(value: int | None) -> str:
    if value is None:
        return "unlimited"
    if value == 0:
        return "unlimited"
    return f"{value / GIB:.2f} GB"


def format_timestamp(ts: int | None) -> str:
    if not ts:
        return "unlimited"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def format_remaining_days(expire: int | None, *, now: int | None = None) -> str:
    if not expire:
        return "unlimited"
    current = now_ts() if now is None else now
    if expire <= current:
        return "expired"
    days = (expire - current) / SECONDS_PER_DAY
    return f"{days:.1f} days"
