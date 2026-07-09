from __future__ import annotations

import secrets
from typing import Any

from .utils import bytes_to_human, format_remaining_days, format_timestamp

STATUS_LABELS = {
    "active": "активен",
    "disabled": "отключён",
    "limited": "лимит исчерпан",
    "expired": "истёк",
    "on_hold": "на удержании",
}


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
    return name or username or str(row.get("tg_user_id") or "неизвестно")


def format_vpn_info(user: dict[str, Any]) -> str:
    links = user.get("links") or []
    subscription_url = user.get("subscription_url")
    status = user.get("status", "неизвестно")
    status_text = STATUS_LABELS.get(status, status)
    lines = [
        "📄 Информация о VPN",
        "",
        f"Пользователь: {user.get('username', 'неизвестно')}",
        f"Статус: {status_text}",
        f"Действует до: {format_timestamp(user.get('expire'))}",
        f"Осталось: {format_remaining_days(user.get('expire'))}",
        f"Трафик: {bytes_to_human(user.get('used_traffic'))} / {bytes_to_human(user.get('data_limit'))}",
    ]
    if subscription_url:
        lines.extend(["", "Ссылка подписки:", str(subscription_url)])
    if links:
        lines.append("")
        lines.append("Ссылки конфигурации:")
        lines.extend(str(link) for link in links)
    return "\n".join(lines)


def payment_amount(months: int) -> int:
    if months not in (1, 2, 3):
        raise ValueError("months must be 1, 2 or 3")
    return months * 50
