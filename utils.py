"""Utility helpers shared across plugins."""

import asyncio
import logging
from typing import Union

from pyrogram import Client
from pyrogram.types import Message

from info import FORCE_SUB_CHANNEL, ADMINS

logger = logging.getLogger(__name__)


def humanbytes(size: int) -> str:
    """Convert bytes to a human-readable string."""
    if not size:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def is_admin(user_id: int) -> bool:
    return user_id in ADMINS


async def check_force_sub(client: Client, message: Message) -> bool:
    """
    Return True if the user is subscribed to FORCE_SUB_CHANNEL
    (or force-sub is disabled).  Sends a prompt and returns False if not.
    """
    if not FORCE_SUB_CHANNEL:
        return True

    user_id = message.from_user.id
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except Exception:
        pass

    try:
        invite = await client.create_chat_invite_link(FORCE_SUB_CHANNEL)
        link = invite.invite_link
    except Exception:
        link = f"https://t.me/c/{str(FORCE_SUB_CHANNEL).lstrip('-100')}"

    await message.reply(
        "⚠️ **Join Required**\n\n"
        "You must join our channel to use this bot.\n\n"
        f"👉 [Join Channel]({link})\n\n"
        "After joining, send your command again.",
        disable_web_page_preview=True,
    )
    return False


async def broadcast_message(client: Client, message: Message) -> tuple[int, int, int]:
    """
    Broadcast a message to all users.
    Returns (success_count, failed_count, total).
    """
    from bot import Bot
    db = client.db  # type: ignore[attr-defined]

    success = failed = 0
    async for user in db.get_all_users():
        uid = user["_id"]
        try:
            await message.copy(uid)
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # flood-control friendly

    return success, failed, success + failed
