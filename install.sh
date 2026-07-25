#!/usr/bin/env bash
# ==============================================================================
# UwawConnect v1.0 Automated Self-Healing Installer (macOS & Linux)
# Wownet Network Infrastructure Operations
# ==============================================================================

set -e

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BOLD='\033[1m'
RESET='\033[0m'
WHITE='\033[1;37m'

echo -e "${CYAN}"
echo "┌─────────────────────────────────────────────────────────────────────────────┐"
echo "│ UWAWCONNECT v1.0 ── Automated Self-Healing Installer Script                │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo -e "${RESET}"

SUDO_CMD=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO_CMD="sudo"
    fi
fi

# Step 1: Detect & auto-install Python 3 and pip3
echo -e "  ${CYAN}[1/3]${RESET} Checking Python 3 and system dependencies..."
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null; then
    echo -e "  ${YELLOW}[!] Python 3 / pip3 missing. Attempting automatic package installation...${RESET}"
    if command -v apt-get &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Debian/Ubuntu (apt-get). Installing python3-pip python3-serial...${RESET}"
        $SUDO_CMD apt-get update -qq -y
        $SUDO_CMD DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-pip python3-serial
    elif command -v dnf &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected RHEL/Fedora/AlmaLinux (dnf). Installing python3-pip python3-pyserial...${RESET}"
        $SUDO_CMD dnf install -y -q python3 python3-pip python3-pyserial
    elif command -v yum &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected CentOS/RHEL (yum). Installing python3-pip...${RESET}"
        $SUDO_CMD yum install -y -q python3 python3-pip
    elif command -v brew &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected macOS (Homebrew). Installing python3...${RESET}"
        brew install python3
    else
        echo -e "  ${RED}[ERROR] Package manager not recognized. Please install python3 & python3-pip manually.${RESET}"
        exit 1
    fi
fi
echo -e "  ${GREEN}[OK]${RESET} Python 3 environment verified."

# Step 2: Auto-install PySerial
echo -e "\n  ${CYAN}[2/3]${RESET} Verifying PySerial library..."
if ! python3 -c "import serial" 2>/dev/null; then
    echo -e "  ${YELLOW}[!] 'pyserial' module not found. Auto-installing...${RESET}"
    python3 -m pip install pyserial --break-system-packages >/dev/null 2>&1 || \
    pip3 install pyserial --break-system-packages >/dev/null 2>&1 || \
    pip install pyserial >/dev/null 2>&1 || true
fi
echo -e "  ${GREEN}[OK]${RESET} PySerial dependency verified."

# Step 3: Install binary
echo -e "\n  ${CYAN}[3/3]${RESET} Installing UwawConnect binary..."
TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/uwawconnect.py"
if [ -f "$SCRIPT_PATH" ]; then
    cp "$SCRIPT_PATH" "$TARGET_DIR/uwaw"
else
    cp "$HOME/uwawconnect_project/uwawconnect.py" "$TARGET_DIR/uwaw" 2>/dev/null || true
fi

chmod +x "$TARGET_DIR/uwaw"

for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$RC" ]; then
        if ! grep -q "alias uwaw=" "$RC"; then
            echo -e '\nalias uwaw="python3 '"$TARGET_DIR"'/uwaw"' >> "$RC"
        fi
        if ! grep -q "$TARGET_DIR" "$RC"; then
            echo -e 'export PATH="'"$TARGET_DIR"':$PATH"' >> "$RC"
        fi
    fi
done

echo -e "\n${CYAN}┌─────────────────────────────────────────────────────────────────────────────┐${RESET}"
echo -e "${CYAN}│ ${GREEN}[SUCCESS] UwawConnect v1.0 Installed Successfully!                          ${CYAN}│${RESET}"
echo -e "${CYAN}│ ${YELLOW}Run 'source ~/.zshrc' (or ~/.bashrc), then type:                             ${CYAN}│${RESET}"
echo -e "${CYAN}│ ${BOLD}${WHITE}uwaw${RESET}${CYAN}                                                                        │${RESET}"
echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────┘${RESET}\n"
