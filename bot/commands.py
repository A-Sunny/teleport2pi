"""
TelePort2PI — Command Handlers
All Telegram bot /command handlers live here.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from ollama_client import OllamaClient, OllamaConnectionError, OllamaTimeoutError

logger = logging.getLogger(__name__)


# ======================================================================
# Core Commands
# ======================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome message."""
    user = update.effective_user
    text = (
        f"👋 *Welcome to TelePort2PI*, {user.first_name}!\n\n"
        "I'm your private AI assistant running locally on a Raspberry Pi.\n"
        "Your conversations never leave your home network.\n\n"
        "Just send me any message to start chatting, or use /help to see all commands."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — list all commands."""
    text = (
        "🤖 *TelePort2PI — Command Reference*\n\n"
        "*Basic*\n"
        "`/start` — Welcome message\n"
        "`/help` — Show this menu\n"
        "`/reset` — Clear your conversation history\n"
        "`/status` — Check system status\n\n"
        "*Model Management*\n"
        "`/model` — Show current model\n"
        "`/models` — List available models\n"
        "`/setmodel <name>` — Switch to a different model\n\n"
        "*AI Shortcuts*\n"
        "`/summarize <text>` — Summarize text\n"
        "`/translate <lang> <text>` — Translate text\n"
        "`/code <task>` — Generate code\n"
        "`/explain <topic>` — Explain a concept simply\n\n"
        "*Memory*\n"
        "`/memory` — Show your stored memories\n"
        "`/remember <text>` — Manually save a memory\n"
        "`/forget <text>` — Delete memories matching text\n"
        "`/clear_memory` — Wipe all your memories\n\n"
        "_Tip: You can also just send any message to chat directly._\n"
        "_To save something naturally, start with: `remember ...` or `note that ...`_"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset — clear the user's conversation history."""
    user_id = update.effective_user.id
    if "history" in context.user_data:
        context.user_data["history"] = []
    await update.message.reply_text(
        "🔄 Conversation history cleared. Starting fresh!"
    )
    logger.info("History reset for user %d", user_id)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status — show Ollama availability and current model."""
    ollama: OllamaClient = context.bot_data["ollama"]
    current_model = context.user_data.get("model", context.bot_data["default_model"])

    if ollama.is_available():
        try:
            available = ollama.list_models()
            model_count = len(available)
            status_line = "✅ Ollama is running"
        except Exception:
            status_line = "⚠️ Ollama reachable but couldn't list models"
            model_count = "?"
    else:
        status_line = "❌ Ollama is not reachable"
        model_count = 0

    history_len = len(context.user_data.get("history", []))

    text = (
        f"*TelePort2PI Status*\n\n"
        f"{status_line}\n"
        f"🧠 Current model: `{current_model}`\n"
        f"📦 Models installed: `{model_count}`\n"
        f"💬 Messages in session: `{history_len}`"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ======================================================================
# Model Commands
# ======================================================================

async def cmd_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /model — show currently active model."""
    current = context.user_data.get("model", context.bot_data["default_model"])
    await update.message.reply_text(
        f"🧠 Current model: `{current}`\n\nUse /models to see all available models.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_models(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /models — list all models available in Ollama."""
    ollama: OllamaClient = context.bot_data["ollama"]
    current = context.user_data.get("model", context.bot_data["default_model"])

    try:
        models = ollama.list_models()
    except OllamaConnectionError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    if not models:
        await update.message.reply_text(
            "No models found. Pull one with:\n`ollama pull llama3.2`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    lines = []
    for m in models:
        marker = "👉 " if m == current else "   "
        lines.append(f"{marker}`{m}`")

    text = (
        "*Available Models:*\n\n"
        + "\n".join(lines)
        + "\n\nUse `/setmodel <name>` to switch."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_setmodel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /setmodel <name> — switch the user's active model."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/setmodel <model_name>`\n\nExample: `/setmodel mistral`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    model_name = context.args[0].strip()
    ollama: OllamaClient = context.bot_data["ollama"]

    try:
        exists = ollama.model_exists(model_name)
    except OllamaConnectionError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    if not exists:
        await update.message.reply_text(
            f"❌ Model `{model_name}` not found locally.\n\n"
            f"Pull it first with:\n`ollama pull {model_name}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    context.user_data["model"] = model_name
    # Clear history when switching models
    context.user_data["history"] = []
    await update.message.reply_text(
        f"✅ Switched to `{model_name}`.\nConversation history cleared.",
        parse_mode=ParseMode.MARKDOWN,
    )
    logger.info(
        "User %d switched to model %s",
        update.effective_user.id,
        model_name,
    )


# ======================================================================
# AI Shortcut Commands
# ======================================================================

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /summarize <text> — summarize provided text."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/summarize <text to summarize>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    text_to_summarize = " ".join(context.args)
    prompt = f"Please summarize the following text concisely:\n\n{text_to_summarize}"
    await _run_single_prompt(update, context, prompt)


async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /translate <language> <text> — translate text to target language."""
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/translate <language> <text>`\n\nExample: `/translate French Hello, how are you?`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    target_lang = context.args[0]
    text_to_translate = " ".join(context.args[1:])
    prompt = f"Translate the following text to {target_lang}. Return only the translation:\n\n{text_to_translate}"
    await _run_single_prompt(update, context, prompt)


async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /code <task> — generate code for a given task."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/code <description of what you need>`\n\nExample: `/code Python function to read a CSV file`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    task = " ".join(context.args)
    prompt = f"Write clean, well-commented code for the following task:\n\n{task}"
    await _run_single_prompt(update, context, prompt)


async def cmd_explain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /explain <topic> — explain a concept in simple terms."""
    if not context.args:
        await update.message.reply_text(
            "Usage: `/explain <topic>`\n\nExample: `/explain how DNS works`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    topic = " ".join(context.args)
    prompt = f"Explain '{topic}' in simple, easy-to-understand terms. Use an analogy if helpful."
    await _run_single_prompt(update, context, prompt)


# ======================================================================
# Shared Helper
# ======================================================================

async def _run_single_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str,
) -> None:
    """
    Send a one-off prompt to Ollama (no conversation history).
    Shows a typing indicator while waiting.
    """
    ollama: OllamaClient = context.bot_data["ollama"]
    model = context.user_data.get("model", context.bot_data["default_model"])
    system_prompt = context.bot_data.get("system_prompt", "")

    await update.message.chat.send_action("typing")

    try:
        response = ollama.generate(prompt=prompt, model=model, system=system_prompt)
        # Telegram message limit is 4096 chars; split if needed
        for chunk in _split_message(response):
            await update.message.reply_text(chunk)
    except OllamaConnectionError as e:
        await update.message.reply_text(f"❌ Connection error: {e}")
    except OllamaTimeoutError as e:
        await update.message.reply_text(f"⏳ Timeout: {e}")
    except Exception as e:
        logger.exception("Unexpected error in _run_single_prompt")
        await update.message.reply_text(f"❌ Unexpected error: {e}")


def _split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split a long message into chunks that fit Telegram's limit."""
    if len(text) <= max_length:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:max_length])
        text = text[max_length:]
    return chunks