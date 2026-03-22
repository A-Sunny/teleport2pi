#!/usr/bin/env bash
# ============================================================
# TelePort2PI — One-Line Installer
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/a-sunny/teleport2pi/main/install.sh)
# ============================================================

set -e

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "${CYAN}[•]${RESET} $1"; }
success() { echo -e "${GREEN}[✓]${RESET} $1"; }
warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
error()   { echo -e "${RED}[✗]${RESET} $1"; exit 1; }
header()  { echo -e "\n${BOLD}${CYAN}$1${RESET}\n"; }

# ── Banner ───────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
cat << 'EOF'

  _______   _      _____           _   ___  _____ _____ 
 |__   __| | |    |  __ \         | | |__ \|  __ \_   _|
    | | ___| | ___| |__) |__  _ __| |_   ) | |__) || |  
    | |/ _ \ |/ _ \  ___/ _ \| '__| __| / /|  ___/ | |  
    | |  __/ |  __/ |  | (_) | |  | |_ / /_| |    _| |_ 
    |_|\___|_|\___|_|   \___/|_|   \__|____|_|   |_____|
                                                        
                                                        

  Self-Hosted AI Gateway: Telegram → Raspberry Pi
EOF
echo -e "${RESET}"

# ── Paths ─────────────────────────────────────────────────────
INSTALL_DIR="$HOME/teleport2pi"
REPO_URL="https://github.com/a-sunny/teleport2pi.git"
VENV_DIR="$INSTALL_DIR/.venv"

# ── Step 1: System check ──────────────────────────────────────
header "Step 1/6 — Checking system requirements"

command -v python3 >/dev/null 2>&1 || error "Python 3 not found. Run: sudo apt install python3"
command -v pip3    >/dev/null 2>&1 || error "pip3 not found. Run: sudo apt install python3-pip"
command -v git     >/dev/null 2>&1 || error "git not found. Run: sudo apt install git"

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python version: $PY_VERSION"

if ! python3 -m venv --help >/dev/null 2>&1; then
    warn "python3-venv not found. Installing..."
    sudo apt-get install -y python3-venv || error "Failed to install python3-venv"
fi

success "System requirements met"

# ── Step 2: Clone or update repo ──────────────────────────────
header "Step 2/6 — Downloading TelePort2PI"

if [ -d "$INSTALL_DIR/.git" ]; then
    warn "Existing installation found — updating..."

    # Preserve memory data across updates
    MEMORY_FILE="$INSTALL_DIR/data/memory.json"
    MEMORY_BACKUP="/tmp/teleport2pi_memory_backup.json"
    if [ -f "$MEMORY_FILE" ]; then
        cp "$MEMORY_FILE" "$MEMORY_BACKUP"
        info "Memory backed up before update"
    fi

    git -C "$INSTALL_DIR" pull || error "Git pull failed"

    # Restore memory after pull
    if [ -f "$MEMORY_BACKUP" ]; then
        mkdir -p "$INSTALL_DIR/data"
        cp "$MEMORY_BACKUP" "$MEMORY_FILE"
        rm -f "$MEMORY_BACKUP"
        success "Memory restored after update"
    fi

    success "Updated to latest version"
else
    git clone "$REPO_URL" "$INSTALL_DIR" || error "Git clone failed. Check your internet connection."
    success "Downloaded to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Step 3: Virtual environment ───────────────────────────────
header "Step 3/6 — Setting up Python virtual environment"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created"
else
    success "Virtual environment already exists — skipping"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
success "pip upgraded"

# ── Step 4: Install dependencies ──────────────────────────────
header "Step 4/6 — Installing dependencies"

pip install -r requirements.txt --quiet || error "Failed to install requirements"
success "All dependencies installed"

# ── Step 5: Configuration ─────────────────────────────────────
header "Step 5/6 — Configuration"

CONFIG_FILE="$INSTALL_DIR/config/config.py"

# Always copy fresh from example so placeholders are always predictable
cp "$INSTALL_DIR/config/config.example.py" "$CONFIG_FILE"
success "Created config/config.py from template"

echo ""
echo -e "${BOLD}Let's configure TelePort2PI:${RESET}"
echo ""

# ── Bot Token ─────────────────────────────────────────────────
while true; do
    read -p "  Telegram Bot Token (from @BotFather): " BOT_TOKEN
    if [ -n "$BOT_TOKEN" ]; then break; fi
    warn "Bot token is required. Get it from @BotFather on Telegram."
done

python3 -c "
import re
with open('$CONFIG_FILE') as f:
    c = f.read()
c = re.sub(r'TELEGRAM_BOT_TOKEN\s*=\s*\".*?\"', 'TELEGRAM_BOT_TOKEN = \"$BOT_TOKEN\"', c)
with open('$CONFIG_FILE', 'w') as f:
    f.write(c)
"
success "Bot token saved"

# ── User ID ───────────────────────────────────────────────────
while true; do
    read -p "  Your Telegram User ID (from @userinfobot): " USER_ID
    if [[ "$USER_ID" =~ ^[0-9]+$ ]]; then break; fi
    warn "User ID must be a number. Message @userinfobot on Telegram to find yours."
done

python3 -c "
import re
with open('$CONFIG_FILE') as f:
    c = f.read()
c = re.sub(r'ALLOWED_USER_IDS\s*=\s*\[.*?\]', 'ALLOWED_USER_IDS = [$USER_ID]', c)
with open('$CONFIG_FILE', 'w') as f:
    f.write(c)
"
success "User ID saved"

# ── Step 6: Ollama & Model ────────────────────────────────────
header "Step 6/6 — Ollama & Model Setup"

if command -v ollama >/dev/null 2>&1; then
    success "Ollama is already installed"

    PULLED_MODELS=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | grep -v '^$' || true)

    if [ -n "$PULLED_MODELS" ]; then
        echo ""
        echo -e "  ${BOLD}Models already on your system:${RESET}"
        i=1
        declare -a MODEL_ARRAY
        while IFS= read -r m; do
            echo "    [$i] $m"
            MODEL_ARRAY+=("$m")
            ((i++))
        done <<< "$PULLED_MODELS"
        echo "    [$i] Enter a different model name"
        echo ""

        read -p "  Pick a model number [1]: " MODEL_CHOICE
        MODEL_CHOICE=${MODEL_CHOICE:-1}

        if [[ "$MODEL_CHOICE" =~ ^[0-9]+$ ]] && [ "$MODEL_CHOICE" -le "${#MODEL_ARRAY[@]}" ]; then
            MODEL="${MODEL_ARRAY[$((MODEL_CHOICE-1))]}"
            success "Using existing model: $MODEL"
        else
            read -p "  Enter model name (e.g. qwen2.5:1.5b): " MODEL
            MODEL=${MODEL:-qwen2.5:1.5b}
            if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
                warn "Model '$MODEL' not found locally."
                read -p "  Pull it now? [Y/n]: " PULL
                PULL=${PULL:-Y}
                if [[ "$PULL" =~ ^[Yy]$ ]]; then
                    ollama pull "$MODEL" || warn "Pull failed — run: ollama pull $MODEL"
                fi
            fi
        fi
    else
        warn "Ollama is installed but no models are pulled yet."
        read -p "  Enter a model to pull [qwen2.5:1.5b]: " MODEL
        MODEL=${MODEL:-qwen2.5:1.5b}
        info "Pulling '$MODEL'... this may take a while."
        ollama pull "$MODEL" || warn "Pull failed — run: ollama pull $MODEL"
    fi

else
    warn "Ollama is not installed."
    read -p "  Install Ollama now? [Y/n]: " INSTALL_OLLAMA
    INSTALL_OLLAMA=${INSTALL_OLLAMA:-Y}
    if [[ "$INSTALL_OLLAMA" =~ ^[Yy]$ ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
        success "Ollama installed"
        read -p "  Enter a model to pull [qwen2.5:1.5b]: " MODEL
        MODEL=${MODEL:-qwen2.5:1.5b}
        info "Pulling '$MODEL'... this may take a while."
        ollama pull "$MODEL" || warn "Pull failed — run: ollama pull $MODEL"
    else
        MODEL="qwen2.5:1.5b"
        warn "Skipping Ollama. Make sure it's running before starting TelePort2PI."
    fi
fi

# Save chosen model to config using Python (safe for colons in names like qwen2.5:1.5b)
python3 -c "
import re
with open('$CONFIG_FILE') as f:
    c = f.read()
c = re.sub(r'DEFAULT_MODEL\s*=\s*\".*?\"', 'DEFAULT_MODEL = \"$MODEL\"', c)
with open('$CONFIG_FILE', 'w') as f:
    f.write(c)
"
success "Default model set to: $MODEL"

# ── Create logs dir and launcher script ───────────────────────
mkdir -p "$INSTALL_DIR/logs"

cat > "$INSTALL_DIR/start.sh" << LAUNCHER
#!/usr/bin/env bash
cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
python bot/bot.py
LAUNCHER
chmod +x "$INSTALL_DIR/start.sh"
success "Created start.sh launcher"

# ── Systemd service (auto-start on boot) ──────────────────────
echo ""
read -p "  Auto-start TelePort2PI on boot? (recommended) [Y/n]: " INSTALL_SERVICE
INSTALL_SERVICE=${INSTALL_SERVICE:-Y}

if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
    SERVICE_FILE="/etc/systemd/system/teleport2pi.service"
    sudo tee "$SERVICE_FILE" > /dev/null << SERVICE
[Unit]
Description=TelePort2PI Telegram AI Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python bot/bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

    sudo systemctl daemon-reload
    sudo systemctl enable teleport2pi
    sudo systemctl start teleport2pi
    success "Service installed, enabled, and started!"
    info "Useful commands:"
    info "  sudo systemctl stop teleport2pi"
    info "  sudo systemctl restart teleport2pi"
    info "  sudo systemctl status teleport2pi"
    info "  sudo journalctl -u teleport2pi -f"
else
    warn "Auto-start skipped. Start manually with: bash $INSTALL_DIR/start.sh"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  TelePort2PI is ready!${RESET}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}Start manually:${RESET}    bash $INSTALL_DIR/start.sh"
if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
echo -e "  ${BOLD}Service control:${RESET}   sudo systemctl start|stop|restart teleport2pi"
echo -e "  ${BOLD}View logs:${RESET}         sudo journalctl -u teleport2pi -f"
fi
echo -e "  ${BOLD}Edit config:${RESET}       nano $INSTALL_DIR/config/config.py"
echo ""
echo -e "  ${CYAN}Open Telegram and send /start to your bot!${RESET}"
echo ""