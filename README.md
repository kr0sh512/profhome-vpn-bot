# Marzban Telegram VPN Bot

Python Telegram bot for issuing one-time VPN invite links and managing Marzban users.

## Features

- Admin-only one-time invite links.
- SQLite database with one table: `users`.
- New users are created in Marzban as `tg{telegram_user_id}`.
- Trial users: 3 days, 10 GB.
- Paid extensions:
  - 1 month / 30 days — 50 ₽
  - 2 months / 60 days — 100 ₽
  - 3 months / 90 days — 150 ₽
- Payment proof is trusted automatically and forwarded to every admin.
- Paid users get 50 GB after payment.
- Traffic reset restores 50 GB and floors remaining time to whole 30-day months after an explicit confirmation.

## Marzban API requirements

On the Marzban panel enable API docs if needed:

```env
DOCS=True
```

Then the panel exposes Swagger at:

```text
https://your-panel.example/docs
```

The bot uses:

- `POST /api/admin/token`
- `POST /api/user`
- `GET /api/user/{username}`
- `PUT /api/user/{username}`
- `POST /api/user/{username}/reset`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.toml config.toml
```

Edit `config.toml`.

## Run

```bash
python bot.py --config config.toml
```

## Admin usage

Start the bot from an admin Telegram account, then use:

```text
/new_user
```

or the `➕ New invite` button.

The bot returns a one-time link:

```text
https://t.me/<bot_username>?start=<token>
```

Send it to the user.

## User flow

1. User opens the invite link.
2. Bot creates Marzban user `tg{telegram_user_id}` with:

```json
{
  "proxies": {"vless": {"flow": "xtls-rprx-vision"}},
  "inbounds": {"vless": ["VLESS TCP REALITY"]},
  "expire": "now + 3 days",
  "data_limit": "10 GiB",
  "data_limit_reset_strategy": "no_reset",
  "status": "active"
}
```

3. User can view VPN info, extend, or reset traffic.

## Notes

The bot does not store VPN state locally. Expiration, traffic, status, subscription URL, and links are fetched from Marzban whenever shown.
