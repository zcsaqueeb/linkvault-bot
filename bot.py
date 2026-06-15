"""
File-to-Link Telegram Bot — Python 3.10+ compatible
"""

import asyncio
import logging
import sys
import os

# ── Load .env first ───────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# ── Fix asyncio for Python 3.10+ ─────────────────────────────────────────────
if sys.version_info >= (3, 10):
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)

# ── Silence noisy Pyrogram / Telegram internal loggers ───────────────────────
for _noisy in (
    "pyrogram.session.auth",
    "pyrogram.session.session",
    "pyrogram.connection.connection",
    "pyrogram.client",
    "pyrogram.dispatcher",
    "pyrogram.sync",
):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

# ── Our logger (clean, minimal) ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from pyrogram import Client, idle
from info import (
    BOT_TOKEN, API_ID, API_HASH,
    LOG_CHANNEL, ADMINS, BOT_NAME,
)
from database.database import Database

# ── Validate config ───────────────────────────────────────────────────────────
_errors = []
if not BOT_TOKEN:   _errors.append("BOT_TOKEN is missing")
if not API_ID:      _errors.append("API_ID is missing or 0")
if not API_HASH:    _errors.append("API_HASH is missing")
if _errors:
    for e in _errors:
        logger.critical("CONFIG ERROR: %s", e)
    sys.exit("\n❌ Fix your .env:\n  " + "\n  ".join(_errors))


class Bot(Client):

    def __init__(self):
        super().__init__(
            name="FileToLinkBot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            sleep_threshold=15,
        )
        self.db = Database()

    async def start(self):
        # Connect DB first
        await self.db.connect()

        await super().start()
        me = await self.get_me()

        print()
        print("━" * 45)
        print(f"  ✅  Bot Online: @{me.username}")
        print(f"  🆔  ID        : {me.id}")
        print(f"  🐍  Python    : {sys.version.split()[0]}")
        print(f"  📦  Pyrogram  : 2.0.106")
        print("━" * 45)
        print()

        # DM admins
        for admin_id in ADMINS:
            try:
                await self.send_message(
                    admin_id,
                    f"✅ **{BOT_NAME} started!**\n"
                    f"▸ @{me.username} | `{me.id}`"
                )
            except Exception:
                pass

        # Post to log channel if set and valid
        if LOG_CHANNEL:
            try:
                await self.send_message(LOG_CHANNEL, f"🤖 **Bot Started** — @{me.username}")
                logger.info("Log channel OK")
            except Exception as e:
                logger.warning(
                    "LOG_CHANNEL error (%s). Make sure the bot is admin in the channel.", e
                )

    async def stop(self):
        print("\n🛑 Bot stopped.")
        await super().stop()


async def main():
    bot = Bot()
    await bot.start()
    await idle()
    await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
