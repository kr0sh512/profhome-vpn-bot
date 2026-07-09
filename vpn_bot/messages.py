from __future__ import annotations

import secrets
from typing import Any

from .utils import bytes_to_human, format_remaining_days, format_timestamp


def generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def user_display_name(row: dict[str, Any]) -> str:
    parts = [row.get("tg_first_name"), row.get("tg_last_name")]
    name = " ".join(part for part in parts if part)
    username = row.get("tg_username")
    if username:
        username = username if username.startswith("@") else f"@{username}"
    if name and username:
        return f"{name} ({username})"
    return name or username or str(row.get("tg_user_id") or "unknown")


def format_vpn_info(user: dict[str, Any]) -> str:
    links = user.get("links") or []
    subscription_url = user.get("subscription_url")
    lines = [
        "📄 VPN info",
        "",
        f"Username: {user.get('username', 'unknown')}",
        f"Status: {user.get('status', 'unknown')}",
        f"Expires: {format_timestamp(user.get('expire'))}",
        f"Remaining: {format_remaining_days(user.get('expire'))}",
        f"Traffic: {bytes_to_human(user.get('used_traffic'))} / {bytes_to_human(user.get('data_limit'))}",
    ]
    if subscription_url:
        lines.extend(["", "Subscription URL:", str(subscription_url)])
    if links:
        lines.append("")
        lines.append("Config links:")
        lines.extend(str(link) for link in links)
    return "\n".join(lines)


def payment_amount(months: int) -> int:
    if months not in (1, 2, 3):
        raise ValueError("months must be 1, 2 or 3")
    return months * 50
