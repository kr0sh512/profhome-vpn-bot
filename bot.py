from __future__ import annotations

import argparse
import asyncio
import logging

from aiogram import Bot

from vpn_bot.config import Config
from vpn_bot.db import Database
from vpn_bot.handlers import BotApp, build_dispatcher
from vpn_bot.marzban import MarzbanClient


async def run(config_path: str) -> None:
    config = Config.load(config_path)
    logging.basicConfig(level=logging.INFO)

    db = Database(config.database_path)
    db.init()

    bot = Bot(config.telegram_bot_token)
    marzban = MarzbanClient(
        base_url=config.marzban_url,
        username=config.marzban_username,
        password=config.marzban_password,
    )
    app = BotApp(config=config, db=db, marzban=marzban)
    dp = build_dispatcher(app)

    try:
        await dp.start_polling(bot)
    finally:
        await marzban.close()
        await bot.session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram bot for Marzban VPN panel")
    parser.add_argument("-c", "--config", default="config.toml", help="Path to config TOML file")
    args = parser.parse_args()
    asyncio.run(run(args.config))


if __name__ == "__main__":
    main()
