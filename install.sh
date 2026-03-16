#!/usr/bin/env bash
# ============================================================
# TelePort2PI — One-Line Installer
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/teleport2pi/main/install.sh)
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
 _____    _     _____           _   ____  ____  ___ 
|_   _|__| | __|  __ \ ___  __| |_|___ \|  _ \|_ _|
  | |/ _ \ |/ /| |_) / _ \/ _  __|  __) | |_) || | 
  | |  __/   < |  __/ (_) | |_| |_ / __/|  __/ | | 
  |_|\___|_|\_\|_|   \___/ \__,_(_)_____|_|   |___|

  Self-Hosted AI Gateway: Telegram → Raspberry Pi
EOF
echo -e "${RESET}"

# ── Config ───────────────────────────────────────────────────
INSTALL_DIR="$HOME/teleport2pi"
REPO_URL="https://github.com/YOUR_USERNAME/teleport2pi.git"
VENV_DIR="$INSTALL_DIR/.venv"
PYTHON="python3"

# ── Step 1: System check ─────────────────────────────────────
header "Step 1/6 — Checking system requirements"

command -v python3 >/dev/null 2>&1 || error "Python 3 is not installed. Run: sudo apt install python3"
command -v pip3 >/dev/null 2>&1    || error "pip3 is not installed. Run: sudo apt install python3-pip"
command -v git >/dev/null 2>&1     || error "git is not installed. Run: sudo apt install git"

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python version: $PY_VERSION"

# Check python3-venv is available
if ! python3 -m venv --help >/dev/null 2>&1; then
    warn "python3-venv not found. Installing..."
    sudo apt-get install -y python3-venv || error "Failed to install python3-venv"
fi

success "System requirements met"

# ── Step 2: Clone or update repo ─────────────────────────────
header "Step 2/6 — Downloading TelePort2PI"

if [ -d "$INSTALL_DIR/.git" ]; then
    warn "Existing installation found at $INSTALL_DIR — updating..."
    git -C "$INSTALL_DIR" pull || error "Git pull failed"
    success "Updated to latest version"
elif [ -d "$INSTALL_DIR" ]; then
    warn "$INSTALL_DIR exists but is not a git repo — installing into it"
    git clone "$REPO_URL" "$INSTALL_DIR" || error "Git clone failed. Check your internet connection."
    success "Downloaded TelePort2PI"
else
    git clone "$REPO_URL" "$INSTALL_DIR" || error "Git clone failed. Check your internet connection."
    success "Downloaded to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# ── Step 3: Virtual environment ──────────────────────────────
header "Step 3/6 — Setting up Python virtual environment"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created at $VENV_DIR"
else
    success "Virtual environment already exists — skipping"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip silently
pip install --upgrade pip --quiet
success "pip upgraded"

# ── Step 4: Install dependencies ─────────────────────────────
header "Step 4/6 — Installing dependencies"

pip install -r requirements.txt --quiet || error "Failed to install requirements"
success "All dependencies installed"

# ── Step 5: Config setup ─────────────────────────────────────
header "Step 5/6 — Configuration"

CONFIG_FILE="$INSTALL_DIR/config/config.py"

if [ -f "$CONFIG_FILE" ]; then
    warn "config.py already exists — skipping (your settings are safe)"
else
    cp "$INSTALL_DIR/config/config.example.py" "$CONFIG_FILE"
    success "Created config/config.py from template"
fi

# Interactive config prompts
echo ""
echo -e "${BOLD}Let's configure TelePort2PI:${RESET}"
echo -e "(Press Enter to skip and edit config/config.py manually later)\n"

# Telegram Bot Token
read -p "  Telegram Bot Token (from @BotFather): " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
    sed -i "s|YOUR_TELEGRAM_BOT_TOKEN_HERE|$BOT_TOKEN|g" "$CONFIG_FILE"
    success "Bot token saved"
fi

# Telegram User ID
read -p "  Your Telegram User ID (from @userinfobot): " USER_ID
if [ -n "$USER_ID" ]; then
    sed -i "s|ALLOWED_USER_IDS = \[\]|ALLOWED_USER_IDS = [$USER_ID]|g" "$CONFIG_FILE"
    success "User ID saved"
fi

# Default model
read -p "  Default Ollama model [qwen2.5:1.5b]: " MODEL
MODEL=${MODEL:-qwen2.5:1.5b}
sed -i "s|DEFAULT_MODEL = \"llama3.2\"|DEFAULT_MODEL = \"$MODEL\"|g" "$CONFIG_FILE"
# Also update AVAILABLE_MODELS to include it at top
sed -i "s|\"llama3.2\",|\"$MODEL\",|g" "$CONFIG_FILE"
success "Default model set to: $MODEL"

# ── Step 6: Ollama check ─────────────────────────────────────
header "Step 6/6 — Checking Ollama"

if command -v ollama >/dev/null 2>&1; then
    success "Ollama is installed"
    if ollama list 2>/dev/null | grep -q "$MODEL"; then
        success "Model '$MODEL' is already pulled"
    else
        warn "Model '$MODEL' not found locally."
        read -p "  Pull it now? This may take a while. [Y/n]: " PULL
        PULL=${PULL:-Y}
        if [[ "$PULL" =~ ^[Yy]$ ]]; then
            ollama pull "$MODEL" || warn "Pull failed — run 'ollama pull $MODEL' manually"
        fi
    fi
else
    warn "Ollama is not installed."
    read -p "  Install Ollama now? [Y/n]: " INSTALL_OLLAMA
    INSTALL_OLLAMA=${INSTALL_OLLAMA:-Y}
    if [[ "$INSTALL_OLLAMA" =~ ^[Yy]$ ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
        success "Ollama installed"
        info "Pulling model '$MODEL'..."
        ollama pull "$MODEL" || warn "Pull failed — run 'ollama pull $MODEL' manually"
    else
        warn "Skipping Ollama install. Make sure it's running before starting TelePort2PI."
    fi
fi

# ── Create launcher script ────────────────────────────────────
cat > "$INSTALL_DIR/start.sh" << LAUNCHER
#!/usr/bin/env bash
cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
python bot/bot.py
LAUNCHER
chmod +x "$INSTALL_DIR/start.sh"
success "Created start.sh launcher"

# ── Optional: systemd service ────────────────────────────────
echo ""
read -p "  Install as a system service (auto-start on boot)? [Y/n]: " INSTALL_SERVICE
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
    success "Service installed and enabled (starts on boot)"
    info "Control with: sudo systemctl start|stop|status teleport2pi"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  TelePort2PI installed successfully!${RESET}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}Start manually:${RESET}   bash $INSTALL_DIR/start.sh"
if [[ "$INSTALL_SERVICE" =~ ^[Yy]$ ]]; then
echo -e "  ${BOLD}Start service:${RESET}    sudo systemctl start teleport2pi"
echo -e "  ${BOLD}View logs:${RESET}        sudo journalctl -u teleport2pi -f"
fi
echo -e "  ${BOLD}Edit config:${RESET}      nano $INSTALL_DIR/config/config.py"
echo ""
echo -e "  ${CYAN}Make sure Ollama is running:  ollama serve${RESET}"
echo ""