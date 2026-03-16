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
- Optionally pull your Ollama model
- Optionally set up a systemd service (auto-start on boot)

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

## Quick Start

### 1. Install Ollama on your Pi

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2   # or any model you prefer
```

### 2. Clone this repo

```bash
git clone https://github.com/yourname/teleport2pi.git
cd teleport2pi
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure

```bash
cp config/config.example.py config/config.py
nano config/config.py
```

Fill in:
- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `ALLOWED_USER_IDS` — your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))
- `DEFAULT_MODEL` — model name matching what you pulled in Ollama

### 5. Run

```bash
python bot/bot.py
```

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
| `/setmodel <n>` | Switch to a different model |
| `/summarize <text>` | Summarize text |
| `/translate <lang> <text>` | Translate text |
| `/code <task>` | Generate code |
| `/explain <topic>` | Explain a concept simply |

Or just **send any message** to chat directly with the AI.

---

## Run as a Service (auto-start on boot)

Create a systemd service so TelePort2PI starts automatically:

```bash
sudo nano /etc/systemd/system/teleport2pi.service
```

```ini
[Unit]
Description=TelePort2PI Telegram AI Bot
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/teleport2pi
ExecStart=/usr/bin/python3 bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable teleport2pi
sudo systemctl start teleport2pi
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
│   └── config.py # Configuration template
├── docs/
│   └── architecture.md   # System design diagram
├── logs/                 # Created automatically at runtime
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
