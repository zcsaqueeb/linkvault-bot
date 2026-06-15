"""
Admin-only commands: /stats, /users, /ban, /unban, /broadcast.
"""

import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from info import ADMINS
from utils import is_admin, broadcast_message

logger = logging.getLogger(__name__)

admin_filter = filters.create(lambda _, __, m: m.from_user and is_admin(m.from_user.id))


@Client.on_message(filters.command("stats") & admin_filter & filters.private)
async def stats_command(client: Client, message: Message):
    db = client.db  # type: ignore[attr-defined]
    total_users = await db.total_users_count()
    total_files = await db.total_files_count()

    await message.reply(
        "📊 **Bot Statistics**\n\n"
        f"👤 Total Users: `{total_users}`\n"
        f"📁 Total Files: `{total_files}`\n"
    )


@Client.on_message(filters.command("users") & admin_filter & filters.private)
async def users_command(client: Client, message: Message):
    db = client.db  # type: ignore[attr-defined]
    count = await db.total_users_count()
    await message.reply(f"👤 **Total registered users:** `{count}`")


@Client.on_message(filters.command("ban") & admin_filter & filters.private)
async def ban_command(client: Client, message: Message):
    db = client.db  # type: ignore[attr-defined]
    args = message.command

    target_id: int | None = None

    # Support reply-to or explicit user ID
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(args) > 1 and args[1].lstrip("-").isdigit():
        target_id = int(args[1])

    if not target_id:
        await message.reply("Usage: `/ban <user_id>` or reply to a user's message.")
        return

    if target_id in ADMINS:
        await message.reply("⛔ Cannot ban an admin.")
        return

    success = await db.ban_user(target_id)
    if success:
        await message.reply(f"✅ User `{target_id}` has been **banned**.")
        try:
            await client.send_message(target_id, "🚫 You have been banned from this bot.")
        except Exception:
            pass
    else:
        await message.reply(f"❌ User `{target_id}` not found in database.")


@Client.on_message(filters.command("unban") & admin_filter & filters.private)
async def unban_command(client: Client, message: Message):
    db = client.db  # type: ignore[attr-defined]
    args = message.command

    target_id: int | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
    elif len(args) > 1 and args[1].lstrip("-").isdigit():
        target_id = int(args[1])

    if not target_id:
        await message.reply("Usage: `/unban <user_id>` or reply to a user's message.")
        return

    success = await db.unban_user(target_id)
    if success:
        await message.reply(f"✅ User `{target_id}` has been **unbanned**.")
        try:
            await client.send_message(target_id, "✅ You have been unbanned. You can use the bot again.")
        except Exception:
            pass
    else:
        await message.reply(f"❌ User `{target_id}` not found in database.")


@Client.on_message(filters.command("broadcast") & admin_filter & filters.private)
async def broadcast_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply(
            "📢 **Broadcast Usage**\n\n"
            "Reply to any message with /broadcast to send it to all users."
        )
        return

    confirm = await message.reply("📡 Broadcasting… please wait.")

    success, failed, total = await broadcast_message(client, message.reply_to_message)

    await confirm.edit(
        f"✅ **Broadcast Complete**\n\n"
        f"▸ Total: `{total}`\n"
        f"▸ Success: `{success}`\n"
        f"▸ Failed: `{failed}`"
    )


@Client.on_message(filters.command("addadmin") & admin_filter & filters.private)
async def add_admin(client: Client, message: Message):
    args = message.command
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Usage: `/addadmin <user_id>`\n\n"
                            "⚠️ This only adds them for the current session. "
                            "Add the ID to ADMINS env var for persistence.")
        return
    uid = int(args[1])
    if uid not in ADMINS:
        ADMINS.append(uid)
        await message.reply(f"✅ `{uid}` added as admin (session only).")
    else:
        await message.reply(f"ℹ️ `{uid}` is already an admin.")
