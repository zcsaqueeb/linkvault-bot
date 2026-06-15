"""
/start, /help, /about — available to ALL users.
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from info import BOT_NAME, DB_CHANNEL, BOT_USERNAME
from utils import check_force_sub, humanbytes

logger = logging.getLogger(__name__)


def _main_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❓ How to Use", callback_data="help"),
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("👨‍💻 Support", callback_data="support"),
        ],
    ])


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user = message.from_user
    db = client.db  # type: ignore[attr-defined]

    # Safely register user (db may be in-memory or mongo — always works now)
    try:
        await db.add_user(user.id, user.first_name or "", user.username or "")
    except Exception as e:
        logger.warning("Could not save user %s: %s", user.id, e)

    # ── Deep-link: /start <file_uid> ─────────────────────────────────────────
    args = message.command
    if len(args) > 1:
        file_uid = args[1]

        if not await check_force_sub(client, message):
            return

        try:
            file_meta = await db.get_file(file_uid)
        except Exception:
            file_meta = None

        if not file_meta:
            await message.reply(
                "❌ **File not found.**\n"
                "It may have been deleted. Contact the uploader for a new link."
            )
            return

        try:
            msg = await client.get_messages(DB_CHANNEL, int(file_meta["msg_id"]))
            caption = (
                f"📁 **{file_meta.get('file_name', 'File')}**\n"
                f"💾 Size: {humanbytes(file_meta.get('file_size', 0))}\n"
                f"📂 Type: `{file_meta.get('mime_type', 'unknown')}`"
            )
            await msg.copy(message.chat.id, caption=caption)
        except Exception as e:
            logger.error("File delivery error for %s: %s", file_uid, e)
            await message.reply(
                "❌ **Could not retrieve the file.**\n"
                "The storage channel may be misconfigured. Contact @support."
            )
        return

    # ── Normal /start ─────────────────────────────────────────────────────────
    await message.reply(
        f"👋 Hello **{user.first_name}**!\n\n"
        f"Welcome to **{BOT_NAME}**.\n\n"
        "📤 Send me any file — document, video, audio, photo — "
        "and I'll give you a permanent Telegram share link.\n\n"
        "▸ The link works for anyone, even without the bot.\n"
        "▸ Files are stored privately and never expire.",
        reply_markup=_main_buttons(),
    )


# ── Callback: Help ────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^help$"))
async def help_callback(client, cq):
    await cq.answer()
    await cq.message.edit_text(
        "**📖 How to Use**\n\n"
        "1️⃣ Send any file to this bot\n"
        "2️⃣ Get a permanent share link instantly\n"
        "3️⃣ Share the link — anyone can download!\n\n"
        "**📋 Commands**\n"
        "▸ /start — welcome screen\n"
        "▸ /help — this menu\n"
        "▸ /about — bot information\n"
        "▸ /ping — check bot speed\n"
        "▸ /id — get your Telegram ID\n\n"
        "**📁 Supported Files**\n"
        "Documents · Videos · Audio · Photos · Voice · Stickers · GIFs",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="home")]
        ]),
    )


# ── Callback: About ───────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^about$"))
async def about_callback(client, cq):
    import sys
    await cq.answer()
    await cq.message.edit_text(
        f"**ℹ️ About {BOT_NAME}**\n\n"
        "▸ **Version:** 2.0\n"
        f"▸ **Python:** {sys.version.split()[0]}\n"
        "▸ **Framework:** Pyrogram 2.0.106\n\n"
        "📝 Files are stored in a private Telegram channel and delivered "
        "via deep-link. No third-party servers or external storage.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="home")]
        ]),
    )


# ── Callback: Support (all users) ────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^support$"))
async def support_callback(client, cq):
    await cq.answer()
    await cq.message.edit_text(
        "**👨‍💻 Support**\n\n"
        "Having trouble? Here's how to get help:\n\n"
        "▸ Make sure you're sending a supported file type\n"
        "▸ Files must be under Telegram's size limit (2 GB)\n"
        "▸ If a link doesn't work, ask the uploader to re-send\n\n"
        "For direct support, contact the bot admin.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="home")]
        ]),
    )


# ── Callback: Home ────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^home$"))
async def home_callback(client, cq):
    await cq.answer()
    user = cq.from_user
    await cq.message.edit_text(
        f"👋 Hello **{user.first_name}**!\n\n"
        f"Welcome to **{BOT_NAME}**.\n\n"
        "📤 Send me any file — document, video, audio, photo — "
        "and I'll give you a permanent Telegram share link.\n\n"
        "▸ The link works for anyone, even without the bot.\n"
        "▸ Files are stored privately and never expire.",
        reply_markup=_main_buttons(),
    )


# ── Text commands ─────────────────────────────────────────────────────────────

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    await message.reply(
        "**📖 Commands & Help**\n\n"
        "**👤 For Everyone:**\n"
        "▸ /start — welcome screen\n"
        "▸ /help — this message\n"
        "▸ /about — bot info\n"
        "▸ /ping — latency check\n"
        "▸ /id — your Telegram user ID\n\n"
        "**🔧 Admins Only:**\n"
        "▸ /stats — user & file counts\n"
        "▸ /users — total users\n"
        "▸ /broadcast — message all users (reply-based)\n"
        "▸ /ban <id> — ban a user\n"
        "▸ /unban <id> — unban a user\n"
        "▸ /delete <file_id> — remove a file link\n\n"
        "**📁 Supported file types:**\n"
        "Documents, Videos, Audio, Photos, Voice, GIFs, Stickers",
        reply_markup=_main_buttons(),
    )


@Client.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    import sys
    await message.reply(
        f"**ℹ️ {BOT_NAME}**\n\n"
        "▸ **Version:** 2.0\n"
        f"▸ **Python:** {sys.version.split()[0]}\n"
        "▸ **Framework:** Pyrogram 2.0.106\n\n"
        "Generates permanent Telegram links for any file. "
        "Files are stored in a private channel — no external servers.",
    )
