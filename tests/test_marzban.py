from vpn_bot.marzban import MarzbanClient
from vpn_bot.utils import GIB


def test_build_trial_user_payload_matches_required_proxy_inbound_and_limits():
    payload = MarzbanClient.build_trial_user_payload(
        tg_user_id=856850518,
        first_name="Dmitry",
        last_name="Gudov",
        tg_username="krosh",
        phone="+79990000000",
        now=1_700_000_000,
    )

    assert payload["username"] == "tg856850518"
    assert payload["proxies"] == {"vless": {"flow": "xtls-rprx-vision"}}
    assert payload["inbounds"] == {"vless": ["VLESS TCP REALITY"]}
    assert payload["expire"] == 1_700_000_000 + 3 * 24 * 60 * 60
    assert payload["data_limit"] == 10 * GIB
    assert payload["data_limit_reset_strategy"] == "month"
    assert payload["status"] == "active"
    assert "Phone: +79990000000" in payload["note"]
    assert "856850518" not in payload["note"]
