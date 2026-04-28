#!/bin/bash

# TelePort2PI Updater Script
# Updates the app without removing user data (config.py, data/memory.json, etc.)
# Run as regular user: ./update.sh or bash update.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="$HOME/teleport2pi"
BACKUP_DIR="$HOME/teleport2pi_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$INSTALL_DIR/update.log"
SERVICE_NAME="teleport2pi"
DRY_RUN=false

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

error_exit() {
    echo -e "${RED}Error: $1${NC}" | tee -a "$LOG_FILE"
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}Attempting rollback from backup...${NC}" | tee -a "$LOG_FILE"
        rollback
    fi
    exit 1
}

rollback() {
    if [ -d "$BACKUP_DIR" ]; then
        log "Rolling back from backup..."
        cp -r "$BACKUP_DIR/config/config.py" "$INSTALL_DIR/config/" 2>/dev/null || true
        cp -r "$BACKUP_DIR/data/" "$INSTALL_DIR/" 2>/dev/null || true
        log "Rollback complete."
    fi
}

check_dependencies() {
    if ! command -v git &> /dev/null; then
        error_exit "Git is not installed. Please install git and try again."
    fi
    if ! command -v python3 &> /dev/null; then
        error_exit "Python3 is not installed. Please install Python 3.10+ and try again."
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--dry-run]"
            exit 1
            ;;
    esac
done

# Start logging
mkdir -p "$INSTALL_DIR"
touch "$LOG_FILE"
log "Starting TelePort2PI update (Dry run: $DRY_RUN)"

# Pre-update checks
if [ "$EUID" -eq 0 ]; then
    error_exit "Do not run as root. Run as regular user."
fi

if [ ! -d "$INSTALL_DIR" ]; then
    error_exit "TelePort2PI not found in $INSTALL_DIR. Please run the installer first."
fi

if [ ! -d "$INSTALL_DIR/.git" ]; then
    error_exit "Installation directory is not a git repository. Manual update required."
fi

if [ ! -d "$INSTALL_DIR/venv" ]; then
    error_exit "Virtual environment not found. Please reinstall."
fi

check_dependencies

# Check systemd service status
SERVICE_ACTIVE=false
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    SERVICE_ACTIVE=true
    log "Systemd service '$SERVICE_NAME' is active and will be restarted after update."
fi

# Backup user data
log "Creating backup of user data..."
mkdir -p "$BACKUP_DIR"
if [ -f "$INSTALL_DIR/config/config.py" ]; then
    cp "$INSTALL_DIR/config/config.py" "$BACKUP_DIR/config/"
else
    log "Warning: config.py not found. Skipping backup."
fi
if [ -d "$INSTALL_DIR/data" ]; then
    cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/"
else
    log "Warning: data directory not found. Skipping backup."
fi
log "Backup created at $BACKUP_DIR"

if [ "$DRY_RUN" = true ]; then
    log "Dry run complete. No changes made."
    echo -e "${GREEN}Dry run successful. Backup at $BACKUP_DIR${NC}"
    exit 0
fi

# Update code
log "Updating code from repository..."
cd "$INSTALL_DIR"
if ! git pull origin main; then
    error_exit "Git pull failed. Check for conflicts or network issues."
fi
log "Code updated successfully."

# Restore user data
log "Restoring user data..."
if [ -f "$BACKUP_DIR/config/config.py" ]; then
    cp "$BACKUP_DIR/config/config.py" "$INSTALL_DIR/config/"
fi
if [ -d "$BACKUP_DIR/data" ]; then
    cp -r "$BACKUP_DIR/data" "$INSTALL_DIR/"
fi
log "User data restored."

# Update dependencies
log "Updating Python dependencies..."
source "$INSTALL_DIR/venv/bin/activate"
if ! pip install -r "$INSTALL_DIR/requirements.txt"; then
    error_exit "Failed to update dependencies."
fi
deactivate
log "Dependencies updated."

# Restart service if it was active
if [ "$SERVICE_ACTIVE" = true ]; then
    log "Restarting systemd service..."
    if ! sudo systemctl restart "$SERVICE_NAME"; then
        log "Warning: Failed to restart service. You may need to restart manually."
    else
        log "Service restarted."
    fi
fi

# Cleanup
log "Cleaning up backup..."
rm -rf "$BACKUP_DIR"
log "Update complete!"

echo -e "${GREEN}TelePort2PI updated successfully!${NC}"
echo -e "${YELLOW}Check logs at $LOG_FILE${NC}"
if [ "$SERVICE_ACTIVE" = false ]; then
    echo -e "${YELLOW}Service was not running. Start it with: sudo systemctl start $SERVICE_NAME${NC}"
fi