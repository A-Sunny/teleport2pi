# TelePort2PI 🤖

**A self-hosted AI gateway from Telegram to Raspberry Pi**

Chat with local AI models running on your Raspberry Pi — from anywhere in the world, via Telegram. Your data never leaves your home.

---

## Install (one line)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/a-sunny/teleport2pi/main/install.sh)
```

The installer will:
- Clone the repo & create a Python virtual environment
- Install all dependencies
- Walk you through config (bot token, user ID, model)
- Detect existing Ollama models or install Ollama fresh
- Optionally set up a systemd service (auto-start on boot)

---

## Uninstall

```bash
bash ~/teleport2pi/uninstall.sh
```

Or if the folder is already removed:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/a-sunny/teleport2pi/main/uninstall.sh)
```

The uninstaller will:
- Stop and remove the systemd service
- Optionally back up your `config.py` (bot token & user ID) before deleting
- Remove the installation directory
- Optionally remove Ollama and all AI models (defaults to **No**)

---

## Update

```bash
bash ~/teleport2pi/update.sh
```

The updater will:
- Backup your user data (`config.py`, `data/memory.json`)
- Pull the latest code from GitHub
- Update Python dependencies
- Restart the service if running
- Preserve all your settings and conversation history

---

## Features

- 💬 **Full AI chat** with conversation history
- 🔒 **Private** — all inference runs locally via [Ollama](https://ollama.com)
- 🌍 **Remote access** via Telegram (no VPN or port forwarding needed)
- 🔄 **Multi-model** — switch between LLaMA, Mistral, Phi, Qwen, and more
- 🛡️ **Secure** — user whitelist + rate limiting built in
- ⚡ **Lightweight** — minimal Python, no heavy frameworks

---

## Requirements

| Component | Requirement |
|-----------|-------------|
| Hardware | Raspberry Pi 5 (8GB recommended) |
| OS | Raspberry Pi OS (64-bit) |
| Python | 3.10+ |
| AI Runtime | [Ollama](https://ollama.com) |
| Interface | Telegram bot token (via [@BotFather](https://t.me/BotFather)) |

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/reset` | Clear conversation history |
| `/status` | Show Ollama status and current model |
| `/model` | Show active model |
| `/models` | List installed models |
| `/setmodel <name>` | Switch to a different model |
| `/summarize <text>` | Summarize text |
| `/translate <lang> <text>` | Translate text |
| `/code <task>` | Generate code |
| `/explain <topic>` | Explain a concept simply |

Or just **send any message** to chat directly with the AI.

---

## Managing the Service

```bash
# Start
sudo systemctl start teleport2pi

# Stop
sudo systemctl stop teleport2pi

# Restart
sudo systemctl restart teleport2pi

# Check status
sudo systemctl status teleport2pi

# View live logs
sudo journalctl -u teleport2pi -f
```

---

## Project Structure

```
teleport2pi/
├── bot/
│   ├── bot.py            # Entry point, auth, rate limiting, chat loop
│   ├── commands.py       # All /command handlers
│   └── ollama_client.py  # Ollama REST API client
├── config/
│   └── config.example.py # Configuration template
├── docs/
│   └── architecture.md   # System design diagram
├── logs/                 # Created automatically at runtime
├── install.sh            # One-line installer
├── uninstall.sh          # Uninstaller
├── update.sh             # Updater (preserves user data)
├── start.sh              # Manual start script (created by installer)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Security

- Access restricted to `ALLOWED_USER_IDS` in config
- Rate limiting prevents abuse
- Long-polling means **no inbound ports required**
- All AI computation stays local

---

## License

MIT