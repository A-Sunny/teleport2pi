"""
TelePort2PI — Main Bot
Entry point: initializes the Telegram bot and wires up all handlers.

Usage:
    python -m bot.bot
    or from project root:
    python bot/bot.py
"""

import logging
import os
import sys
import time
from collections import defaultdict

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Add the bot/ directory itself to path so sibling modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))
# Add project root so config/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ollama_client import OllamaClient, OllamaConnectionError, OllamaTimeoutError
from commands import (
    cmd_start,
    cmd_help,
    cmd_reset,
    cmd_status,
    cmd_model,
    cmd_models,
    cmd_setmodel,
    cmd_summarize,
    cmd_translate,
    cmd_code,
    cmd_explain,
    _split_message,
)

# ------------------------------------------------------------------
# Load Config  (use importlib so we always load OUR config.py, not a system module)
# ------------------------------------------------------------------
import importlib.util as _ilu

_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "config.py"))
if not os.path.exists(_config_path):
    print(
        "ERROR: config/config.py not found.\n"
        "Copy config/config.example.py to config/config.py and fill in your values."
    )
    sys.exit(1)

_spec = _ilu.spec_from_file_location("config", _config_path)
config = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(config)

# ------------------------------------------------------------------
# Logging Setup
# ------------------------------------------------------------------
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE),
    ],
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Rate Limiter (in-memory, per user)
# ------------------------------------------------------------------
_rate_tracker: dict[int, list[float]] = defaultdict(list)


def _is_rate_limited(user_id: int) -> bool:
    """Return True if the user has exceeded RATE_LIMIT_PER_MINUTE."""
    now = time.time()
    window = 60.0
    timestamps = _rate_tracker[user_id]
    # Remove timestamps older than 1 minute
    _rate_tracker[user_id] = [t for t in timestamps if now - t < window]
    if len(_rate_tracker[user_id]) >= config.RATE_LIMIT_PER_MINUTE:
        return True
    _rate_tracker[user_id].append(now)
    return False


# ------------------------------------------------------------------
# Auth Guard
# ------------------------------------------------------------------
def _is_authorized(user_id: int) -> bool:
    """Return True if the user is in the whitelist (or whitelist is empty = open)."""
    if not config.ALLOWED_USER_IDS:
        return True  # Open access if no whitelist configured
    return user_id in config.ALLOWED_USER_IDS


# ------------------------------------------------------------------
# Message Handler — Main Chat Loop
# ------------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle plain text messages (i.e. conversation with the AI).
    Maintains per-user conversation history.
    """
    user = update.effective_user
    user_id = user.id
    user_text = update.message.text.strip()

    # Auth check
    if not _is_authorized(user_id):
        logger.warning("Unauthorized access attempt by user %d (%s)", user_id, user.username)
        await update.message.reply_text("⛔ Sorry, you're not authorized to use this bot.")
        return

    # Rate limit check
    if _is_rate_limited(user_id):
        await update.message.reply_text(
            f"⏳ Slow down! You can send up to {config.RATE_LIMIT_PER_MINUTE} messages per minute."
        )
        return

    if not user_text:
        return

    logger.info("Message from user %d: %s", user_id, user_text[:80])

    # Initialize user session if needed
    if "history" not in context.user_data:
        context.user_data["history"] = []
    if "model" not in context.user_data:
        context.user_data["model"] = config.DEFAULT_MODEL

    model = context.user_data["model"]
    history: list[dict] = context.user_data["history"]

    # Build messages list: system prompt + history + new message
    messages = []
    if config.SYSTEM_PROMPT:
        messages.append({"role": "system", "content": config.SYSTEM_PROMPT})
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    # Show typing indicator
    await update.message.chat.send_action("typing")

    ollama: OllamaClient = context.bot_data["ollama"]

    try:
        response = ollama.chat(messages=messages, model=model)
    except OllamaConnectionError as e:
        await update.message.reply_text(
            f"❌ *Ollama not reachable.*\n\n{e}\n\nCheck that Ollama is running on your Pi.",
            parse_mode="Markdown",
        )
        return
    except OllamaTimeoutError as e:
        await update.message.reply_text(
            f"⏳ *Ollama timed out.*\n\n{e}\n\nThe model may still be loading — try again in a moment.",
            parse_mode="Markdown",
        )
        return
    except Exception as e:
        logger.exception("Unexpected error handling message from user %d", user_id)
        await update.message.reply_text(f"❌ Unexpected error: {e}")
        return

    # Append this turn to history (trim if needed)
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response})

    # Trim history to MAX_HISTORY_TURNS (each turn = 2 messages)
    max_messages = config.MAX_HISTORY_TURNS * 2
    if len(history) > max_messages:
        context.user_data["history"] = history[-max_messages:]

    # Send response (split if > 4000 chars)
    for chunk in _split_message(response):
        await update.message.reply_text(chunk)

    logger.info(
        "Responded to user %d (model=%s, history=%d msgs)",
        user_id,
        model,
        len(context.user_data["history"]),
    )


# ------------------------------------------------------------------
# Unknown Command Handler
# ------------------------------------------------------------------
async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch-all for unrecognized commands."""
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see what I can do."
    )


# ------------------------------------------------------------------
# Error Handler
# ------------------------------------------------------------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors raised by telegram handlers."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# ------------------------------------------------------------------
# Bootstrap
# ------------------------------------------------------------------
def main() -> None:
    logger.info("Starting TelePort2PI...")

    # Verify Ollama is reachable before starting
    ollama = OllamaClient(
        base_url=config.OLLAMA_BASE_URL,
        default_model=config.DEFAULT_MODEL,
        request_timeout=config.OLLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    if not ollama.is_available():
        logger.warning(
            "⚠️  Ollama not reachable at %s — starting anyway, "
            "but AI responses will fail until Ollama is running.",
            config.OLLAMA_BASE_URL,
        )
    else:
        logger.info("✅ Ollama is running at %s", config.OLLAMA_BASE_URL)

    # Build the Application
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Store shared objects in bot_data (available to all handlers)
    app.bot_data["ollama"] = ollama
    app.bot_data["default_model"] = config.DEFAULT_MODEL
    app.bot_data["system_prompt"] = config.SYSTEM_PROMPT

    # Register command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("model", cmd_model))
    app.add_handler(CommandHandler("models", cmd_models))
    app.add_handler(CommandHandler("setmodel", cmd_setmodel))
    app.add_handler(CommandHandler("summarize", cmd_summarize))
    app.add_handler(CommandHandler("translate", cmd_translate))
    app.add_handler(CommandHandler("code", cmd_code))
    app.add_handler(CommandHandler("explain", cmd_explain))

    # Plain text message handler (the main chat loop)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Unknown commands
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("TelePort2PI is online. Waiting for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()