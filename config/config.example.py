# ============================================================
# TelePort2PI — Configuration File
# Copy this to config.py and fill in your values.
# NEVER commit config.py to version control.
# ============================================================

# ----------------------------------------------------------
# Telegram Bot Configuration
# Get your token from @BotFather on Telegram
# ----------------------------------------------------------
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Allowed Telegram user IDs (whitelist for security)
# Find your user ID by messaging @userinfobot on Telegram
# Example: ALLOWED_USER_IDS = [123456789, 987654321]
ALLOWED_USER_IDS = []

# ----------------------------------------------------------
# Ollama Configuration
# ----------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"

# Default model to use on startup
# Must be a model you have pulled via: ollama pull <model>
DEFAULT_MODEL = "qwen2.5:1.5b"

# How long to wait for Ollama to respond (in seconds)
# Increase this if your model takes longer than ~2 minutes to generate.
OLLAMA_REQUEST_TIMEOUT_SECONDS = 300

# Available models users can switch between
AVAILABLE_MODELS = [
    "qwen2.5:1.5b",
    "qwen2.5",
    "llama3.2",
    "mistral",
    "phi3",
    "deepseek-r1",
]

# ----------------------------------------------------------
# Rate Limiting
# ----------------------------------------------------------
# Max number of requests per user per minute
RATE_LIMIT_PER_MINUTE = 10

# ----------------------------------------------------------
# Session Management
# ----------------------------------------------------------
# Max conversation history turns to keep per user (pairs of user+assistant)
MAX_HISTORY_TURNS = 10

# Session timeout in seconds (0 = never expire)
SESSION_TIMEOUT_SECONDS = 3600  # 1 hour

# ----------------------------------------------------------
# Logging
# ----------------------------------------------------------
LOG_LEVEL = "INFO"  # DEBUG | INFO | WARNING | ERROR
LOG_FILE = "logs/teleport2pi.log"

# ----------------------------------------------------------
# Optional: System Prompt
# Sets the AI's persona/behavior for all users
# ----------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a helpful, concise AI assistant running locally on a Raspberry Pi. "
    "Answer clearly and directly. If you don't know something, say so."
)