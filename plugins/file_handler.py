"""
File handler — receives files, stores to DB channel, returns a share link.
"""

import logging
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from info import DB_CHANNEL, BOT_USERNAME, URL, STREAM_MODE
from utils import check_force_sub, humanbytes, is_admin

logger = logging.getLogger(__name__)

FILE_TYPES = (
    "document", "video", "audio", "photo",
    "voice", "video_note", "animation", "sticker"
)


def _get_file_info(message: Message) -> dict | None:
    for ftype in FILE_TYPES:
        obj = getattr(message, ftype, None)
        if not obj:
            continue
        return {
            "type": ftype,
            "file_id": getattr(obj, "file_id", None),
            "file_name": getattr(obj, "file_name", None) or ftype.capitalize(),
            "file_size": getattr(obj, "file_size", 0) or 0,
            "mime_type": getattr(obj, "mime_type", "application/octet-stream") or ftype,
        }
    return None


@Client.on_message(
    filters.private & (
        filters.document | filters.video | filters.audio |
        filters.voice | filters.video_note | filters.animation |
        filters.sticker | filters.photo
    )
)
async def file_receive_handler(client: Client, message: Message):
    db = client.db  # type: ignore[attr-defined]

    if not await check_force_sub(client, message):
        return

    info = _get_file_info(message)
    if not info:
        return

    if not DB_CHANNEL:
        await message.reply(
            "⚠️ **Bot not configured.**\n"
            "The admin hasn't set a `DB_CHANNEL` yet."
        )
        return

    processing = await message.reply("⏳ Saving your file…")

    try:
        fwd = await message.copy(DB_CHANNEL)
    except Exception as e:
        logger.error("Forward to DB channel failed: %s", e)
        await processing.edit(
            "❌ **Storage Error**\n\n"
            "Could not save the file. This usually means:\n"
            "▸ The bot is not an **admin** in the storage channel\n"
            "▸ The `DB_CHANNEL` ID in `.env` is wrong\n\n"
            "Contact the bot admin to fix this."
        )
        return

    file_uid = uuid.uuid4().hex[:12]

    try:
        await db.save_file(file_uid, {
            "file_id": info["file_id"],
            "file_name": info["file_name"],
            "file_size": info["file_size"],
            "mime_type": info["mime_type"],
            "type": info["type"],
            "msg_id": fwd.id,
            "uploader_id": message.from_user.id,
        })
    except Exception as e:
        logger.error("DB save error: %s", e)
        await processing.edit("❌ Database error. Please try again.")
        return

    bot_username = BOT_USERNAME or (await client.get_me()).username
    tg_link = f"https://t.me/{bot_username}?start={file_uid}"

    stream_link = None
    if URL and STREAM_MODE and info["type"] == "video":
        stream_link = f"{URL}/stream/{file_uid}"

    button_rows = [[InlineKeyboardButton("🔗 Share Link", url=tg_link)]]
    if stream_link:
        button_rows.append([InlineKeyboardButton("▶️ Stream Online", url=stream_link)])

    await processing.edit(
        f"✅ **File saved!**\n\n"
        f"📁 **Name:** `{info['file_name']}`\n"
        f"💾 **Size:** {humanbytes(info['file_size'])}\n"
        f"📂 **Type:** `{info['mime_type']}`\n\n"
        f"🔗 **Your Link:**\n`{tg_link}`\n\n"
        "Anyone can use this link to download the file!",
        reply_markup=InlineKeyboardMarkup(button_rows),
        disable_web_page_preview=True,
    )


@Client.on_message(filters.command("delete") & filters.private)
async def delete_file(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply("⛔ This command is for admins only.")
        return
    db = client.db  # type: ignore[attr-defined]
    args = message.command
    if len(args) < 2:
        await message.reply("Usage: `/delete <file_id>`", parse_mode="markdown")
        return
    file_uid = args[1]
    deleted = await db.delete_file(file_uid)
    if deleted:
        await message.reply(f"✅ File `{file_uid}` removed from database.")
    else:
        await message.reply(f"❌ File `{file_uid}` not found.")
