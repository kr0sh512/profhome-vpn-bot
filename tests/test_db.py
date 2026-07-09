from pathlib import Path

from vpn_bot.db import Database


def test_invite_is_stored_before_activation_and_can_be_loaded(tmp_path: Path):
    db = Database(tmp_path / "bot.sqlite3")
    db.init()

    db.create_invite(token="abc", admin_id=42, created_at=1000)
    user = db.get_by_token("abc")

    assert user is not None
    assert user["invite_token"] == "abc"
    assert user["invite_created_by_admin_id"] == 42
    assert user["tg_user_id"] is None


def test_activation_stores_telegram_identity_and_marzban_username(tmp_path: Path):
    db = Database(tmp_path / "bot.sqlite3")
    db.init()
    db.create_invite(token="abc", admin_id=42, created_at=1000)

    db.activate_invite(
        token="abc",
        tg_user_id=856850518,
        tg_username="krosh",
        tg_first_name="Dmitry",
        tg_last_name="Gudov",
        tg_phone=None,
        marzban_username="tg856850518",
        activated_at=1100,
    )

    user = db.get_by_tg_user_id(856850518)
    assert user is not None
    assert user["invite_token"] == "abc"
    assert user["marzban_username"] == "tg856850518"
    assert user["tg_first_name"] == "Dmitry"


def test_used_invite_cannot_be_activated_twice(tmp_path: Path):
    db = Database(tmp_path / "bot.sqlite3")
    db.init()
    db.create_invite(token="abc", admin_id=42, created_at=1000)
    db.activate_invite(
        token="abc",
        tg_user_id=1,
        tg_username=None,
        tg_first_name="One",
        tg_last_name=None,
        tg_phone=None,
        marzban_username="tg1",
        activated_at=1100,
    )

    try:
        db.activate_invite(
            token="abc",
            tg_user_id=2,
            tg_username=None,
            tg_first_name="Two",
            tg_last_name=None,
            tg_phone=None,
            marzban_username="tg2",
            activated_at=1200,
        )
    except ValueError as exc:
        assert "уже использована" in str(exc)
    else:
        raise AssertionError("second activation should fail")
