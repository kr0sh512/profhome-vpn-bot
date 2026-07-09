from datetime import datetime, timezone

from vpn_bot.utils import (
    GIB,
    add_days_from_base,
    bytes_to_human,
    build_marzban_note,
    calculate_reset_expire,
    format_marzban_username,
)


def test_format_marzban_username_uses_tg_prefix():
    assert format_marzban_username(856850518) == "tg856850518"


def test_build_marzban_note_omits_telegram_id_and_missing_phone():
    note = build_marzban_note(
        first_name="Dmitry",
        last_name="Gudov",
        username="dima",
        phone=None,
    )

    assert "First name: Dmitry" in note
    assert "Last name: Gudov" in note
    assert "Username: @dima" in note
    assert "Phone:" not in note
    assert "856" not in note


def test_add_days_from_future_expiration_extends_from_future_timestamp():
    now = 1_700_000_000
    future = now + 2 * 24 * 60 * 60

    assert add_days_from_base(current_expire=future, days=30, now=now) == future + 30 * 24 * 60 * 60


def test_add_days_from_expired_account_extends_from_now():
    now = 1_700_000_000
    expired = now - 10

    assert add_days_from_base(current_expire=expired, days=30, now=now) == now + 30 * 24 * 60 * 60


def test_calculate_reset_expire_floors_remaining_time_to_whole_30_day_months():
    now = 1_700_000_000
    expire = now + (1 * 30 + 12) * 24 * 60 * 60

    new_expire, full_months = calculate_reset_expire(expire=expire, now=now)

    assert full_months == 1
    assert new_expire == now + 30 * 24 * 60 * 60


def test_calculate_reset_expire_discards_partial_month_when_less_than_one_month_left():
    now = 1_700_000_000
    expire = now + 12 * 24 * 60 * 60

    new_expire, full_months = calculate_reset_expire(expire=expire, now=now)

    assert full_months == 0
    assert new_expire == now


def test_bytes_to_human_formats_gib():
    assert bytes_to_human(50 * GIB) == "50.00 GB"
