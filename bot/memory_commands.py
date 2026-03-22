"""
TelePort2PI — Memory Commands
Handlers for /memory, /remember, /forget, /clear_memory
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/memory — list all stored memories for this user."""
    memory = context.bot_data.get("memory")
    if memory is None:
        await update.message.reply_text("❌ Memory system is not initialized.")
        return

    user_id = update.effective_user.id
    memories = memory.list_memories(user_id)

    if not memories:
        await update.message.reply_text(
            "🧠 No memories stored yet.\n\n"
            "You can save one by starting a message with:\n"
            "`remember ...`, `save this ...`, or `note that ...`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    lines = "\n".join(f"{i+1}. {m}" for i, m in enumerate(memories))
    text = f"🧠 *Your stored memories ({len(memories)}):*\n\n{lines}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_remember(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/remember <text> — manually save a memory."""
    memory = context.bot_data.get("memory")
    if memory is None:
        await update.message.reply_text("❌ Memory system is not initialized.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/remember <text>`\n\nExample: `/remember I prefer short answers`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    user_id = update.effective_user.id
    text = " ".join(context.args).strip()

    saved = memory.add_memory(user_id, text)
    if saved:
        await update.message.reply_text(f"✅ Remembered: _{text}_", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("ℹ️ This is already in your memory.")


async def cmd_forget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/forget <text> — delete any memory containing the given text."""
    memory = context.bot_data.get("memory")
    if memory is None:
        await update.message.reply_text("❌ Memory system is not initialized.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/forget <text>`\n\nDeletes any memory containing that text.\n"
            "Example: `/forget Telegram bot`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    user_id = update.effective_user.id
    fragment = " ".join(context.args).strip()

    deleted = memory.delete_memory(user_id, fragment)
    if deleted:
        await update.message.reply_text(
            f"🗑️ Deleted memories matching: _{fragment}_",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            f"❓ No memory found matching: _{fragment}_",
            parse_mode=ParseMode.MARKDOWN,
        )


async def cmd_clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/clear_memory — wipe all memories for this user."""
    memory = context.bot_data.get("memory")
    if memory is None:
        await update.message.reply_text("❌ Memory system is not initialized.")
        return

    user_id = update.effective_user.id
    count = memory.clear_memories(user_id)

    if count == 0:
        await update.message.reply_text("🧠 No memories to clear.")
    else:
        await update.message.reply_text(
            f"🗑️ Cleared {count} memor{'y' if count == 1 else 'ies'}."
        )