#!/usr/bin/env bash
# ============================================================
# TelePort2PI — Uninstaller
# Usage:
#   bash ~/teleport2pi/uninstall.sh
#   or:
#   bash <(curl -fsSL https://raw.githubusercontent.com/a-sunny/teleport2pi/main/uninstall.sh)
# ============================================================

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
echo -e "${BOLD}${RED}"
cat << 'BANNER'

  _______   _      _____           _   ___  _____ _____ 
 |__   __| | |    |  __ \         | | |__ \|  __ \_   _|
    | | ___| | ___| |__) |__  _ __| |_   ) | |__) || |  
    | |/ _ \ |/ _ \  ___/ _ \| '__| __| / /|  ___/ | |  
    | |  __/ |  __/ |  | (_) | |  | |_ / /_| |    _| |_ 
    |_|\___|_|\___|_|   \___/|_|   \__|____|_|   |_____|

  Uninstaller
BANNER
echo -e "${RESET}"

INSTALL_DIR="$HOME/teleport2pi"
SERVICE_FILE="/etc/systemd/system/teleport2pi.service"

# ── Confirm ───────────────────────────────────────────────────
echo -e "${BOLD}${RED}WARNING: This will completely remove TelePort2PI.${RESET}"
echo -e "  Installation directory: ${BOLD}$INSTALL_DIR${RESET}"
echo ""
read -p "  Are you sure you want to uninstall? [y/N]: " CONFIRM
CONFIRM=${CONFIRM:-N}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo ""
    info "Uninstall cancelled. Nothing was changed."
    exit 0
fi

echo ""

# ── Step 1: Stop and remove systemd service ───────────────────
header "Step 1/3 — Removing system service"

if [ -f "$SERVICE_FILE" ]; then
    info "Stopping teleport2pi service..."
    sudo systemctl stop teleport2pi 2>/dev/null || true

    info "Disabling teleport2pi service..."
    sudo systemctl disable teleport2pi 2>/dev/null || true

    info "Removing service file..."
    sudo rm -f "$SERVICE_FILE"

    sudo systemctl daemon-reload
    success "Service removed"
else
    info "No systemd service found — skipping"
fi

# ── Step 2: Remove installation directory ─────────────────────
header "Step 2/3 — Removing installation files"

if [ -d "$INSTALL_DIR" ]; then
    # Ask about config separately — user might want to keep their token/settings
    echo ""
    read -p "  Keep your config.py (bot token, user ID)? [Y/n]: " KEEP_CONFIG
    KEEP_CONFIG=${KEEP_CONFIG:-Y}

    if [[ "$KEEP_CONFIG" =~ ^[Yy]$ ]] && [ -f "$INSTALL_DIR/config/config.py" ]; then
        CONFIG_BACKUP="$HOME/teleport2pi_config_backup.py"
        cp "$INSTALL_DIR/config/config.py" "$CONFIG_BACKUP"
        info "Config backed up to: $CONFIG_BACKUP"
    fi

    # Ask about memory backup
    MEMORY_FILE="$INSTALL_DIR/data/memory.json"
    if [ -f "$MEMORY_FILE" ]; then
        echo ""
        read -p "  Keep your memory data (stored memories)? [Y/n]: " KEEP_MEMORY
        KEEP_MEMORY=${KEEP_MEMORY:-Y}

        if [[ "$KEEP_MEMORY" =~ ^[Yy]$ ]]; then
            MEMORY_BACKUP="$HOME/teleport2pi_memory_backup.json"
            cp "$MEMORY_FILE" "$MEMORY_BACKUP"
            info "Memory backed up to: $MEMORY_BACKUP"
        fi
    fi

    rm -rf "$INSTALL_DIR"
    success "Removed $INSTALL_DIR"
else
    warn "Installation directory not found: $INSTALL_DIR"
fi

# ── Step 3: Optional — remove Ollama ──────────────────────────
header "Step 3/3 — Ollama (optional)"

if command -v ollama >/dev/null 2>&1; then
    echo ""
    read -p "  Remove Ollama too? (this also deletes all your AI models) [y/N]: " REMOVE_OLLAMA
    REMOVE_OLLAMA=${REMOVE_OLLAMA:-N}

    if [[ "$REMOVE_OLLAMA" =~ ^[Yy]$ ]]; then
        info "Stopping Ollama service..."
        sudo systemctl stop ollama 2>/dev/null || true
        sudo systemctl disable ollama 2>/dev/null || true

        info "Removing Ollama binary..."
        sudo rm -f /usr/local/bin/ollama

        info "Removing Ollama models and data..."
        rm -rf "$HOME/.ollama"
        sudo rm -rf /usr/share/ollama
        sudo rm -f /etc/systemd/system/ollama.service
        sudo systemctl daemon-reload

        success "Ollama removed"
    else
        info "Ollama kept — your models are safe"
    fi
else
    info "Ollama not found — skipping"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}  TelePort2PI has been uninstalled.${RESET}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
if [[ "$KEEP_CONFIG" =~ ^[Yy]$ ]] && [ -f "$HOME/teleport2pi_config_backup.py" ]; then
echo -e "  ${BOLD}Config backup:${RESET}  $HOME/teleport2pi_config_backup.py"
fi
if [[ "${KEEP_MEMORY:-N}" =~ ^[Yy]$ ]] && [ -f "$HOME/teleport2pi_memory_backup.json" ]; then
echo -e "  ${BOLD}Memory backup:${RESET}  $HOME/teleport2pi_memory_backup.json"
fi
echo -e "  ${CYAN}To reinstall anytime:${RESET}"
echo -e "  bash <(curl -fsSL https://raw.githubusercontent.com/a-sunny/teleport2pi/main/install.sh)"
echo ""