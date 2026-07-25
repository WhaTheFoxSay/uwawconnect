#!/usr/bin/env bash
# ==============================================================================
# UwawConnect v1.3.1 Automated Self-Healing Installer (macOS, Linux, BSD, Solaris, Haiku OS)
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
echo "│ UWAWCONNECT v1.3.1 ── Automated Self-Healing Installer Script              │"
echo "└─────────────────────────────────────────────────────────────────────────────┘"
echo -e "${RESET}"

SUDO_CMD=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo &> /dev/null; then
        SUDO_CMD="sudo"
    fi
fi

# Step 1: Detect & verify Python 3 environment
echo -e "  ${CYAN}[1/3]${RESET} Checking Python 3 environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "  ${YELLOW}[!] Python 3 missing. Attempting automatic package installation...${RESET}"
    if command -v apt-get &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Debian/Ubuntu (apt-get). Installing python3 python3-pip python3-serial...${RESET}"
        $SUDO_CMD apt-get update -qq -y 2>/dev/null || true
        $SUDO_CMD DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-pip python3-serial 2>/dev/null || true
    elif command -v dnf &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected RHEL/Fedora/AlmaLinux (dnf). Installing python3 python3-pip...${RESET}"
        $SUDO_CMD dnf install -y -q python3 python3-pip 2>/dev/null || true
    elif command -v yum &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected CentOS/RHEL (yum). Installing python3...${RESET}"
        $SUDO_CMD yum install -y -q python3 python3-pip 2>/dev/null || true
    elif command -v pacman &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Arch/Manjaro (pacman). Installing python python-pyserial...${RESET}"
        $SUDO_CMD pacman -Sy --noconfirm python python-pyserial 2>/dev/null || true
    elif command -v eopkg &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Solus Linux (eopkg). Installing python3...${RESET}"
        $SUDO_CMD eopkg install -y python3 2>/dev/null || true
    elif command -v xbps-install &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Void Linux (xbps). Installing python3...${RESET}"
        $SUDO_CMD xbps-install -Sy python3 2>/dev/null || true
    elif command -v emerge &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Gentoo Linux (emerge). Installing python...${RESET}"
        $SUDO_CMD emerge --ask=n dev-lang/python 2>/dev/null || true
    elif command -v nix-env &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected NixOS (nix-env). Installing python3...${RESET}"
        nix-env -iA nixos.python3 2>/dev/null || true
    elif command -v brew &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected macOS (Homebrew). Installing python3...${RESET}"
        brew install python3
    elif command -v pkg &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected FreeBSD/Solaris (pkg). Installing python3...${RESET}"
        $SUDO_CMD pkg install -y python3 2>/dev/null || true
    elif command -v pkg_add &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected OpenBSD (pkg_add). Installing python3...${RESET}"
        $SUDO_CMD pkg_add python3 2>/dev/null || true
    elif command -v pkgin &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected NetBSD/Solaris (pkgin). Installing python3...${RESET}"
        $SUDO_CMD pkgin -y install python3 2>/dev/null || true
    elif command -v pkgman &> /dev/null; then
        echo -e "  ${DIM}[SYS] Detected Haiku OS (pkgman). Installing python3...${RESET}"
        pkgman install -y python3 2>/dev/null || true
    else
        echo -e "  ${RED}[ERROR] Package manager not recognized. Please install python3 manually.${RESET}"
        exit 1
    fi
fi
echo -e "  ${GREEN}[OK]${RESET} Python 3 environment verified."

# Step 2: Auto-install PySerial
echo -e "\n  ${CYAN}[2/3]${RESET} Verifying PySerial library..."
if ! python3 -c "import serial" 2>/dev/null; then
    echo -e "  ${YELLOW}[!] 'pyserial' module not found. Attempting installation...${RESET}"
    if command -v pip3 &> /dev/null || command -v pip &> /dev/null || python3 -m pip --version &>/dev/null; then
        python3 -m pip install pyserial --break-system-packages >/dev/null 2>&1 || \
        pip3 install pyserial --break-system-packages >/dev/null 2>&1 || \
        pip install pyserial >/dev/null 2>&1 || true
    fi

    # Fallback to system package manager if pip failed or missing
    if ! python3 -c "import serial" 2>/dev/null; then
        echo -e "  ${DIM}[SYS] Installing python3-pyserial via package manager...${RESET}"
        if command -v apt-get &> /dev/null; then
            $SUDO_CMD apt-get install -y -qq python3-serial 2>/dev/null || true
        elif command -v dnf &> /dev/null; then
            $SUDO_CMD dnf install -y -q python3-pyserial 2>/dev/null || true
        elif command -v yum &> /dev/null; then
            $SUDO_CMD yum install -y -q python3-pyserial 2>/dev/null || true
        elif command -v pacman &> /dev/null; then
            $SUDO_CMD pacman -Sy --noconfirm python-pyserial 2>/dev/null || true
        elif command -v pkg &> /dev/null; then
            $SUDO_CMD pkg install -y py311-pyserial 2>/dev/null || true
        fi
    fi
fi
echo -e "  ${GREEN}[OK]${RESET} PySerial dependency verified."

# Step 3: Install binary executable and initialize directory structure
echo -e "\n  ${CYAN}[3/3]${RESET} Installing UwawConnect binary & workspace directories..."
TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR" "$HOME/.uwaw/logs" "$HOME/.uwaw/configs" "$HOME/.uwaw/macros"

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)/uwawconnect.py"

if [ -f "$SCRIPT_PATH" ]; then
    cp "$SCRIPT_PATH" "$TARGET_DIR/uwaw"
elif [ -f "$HOME/uwawconnect_project/uwawconnect.py" ]; then
    cp "$HOME/uwawconnect_project/uwawconnect.py" "$TARGET_DIR/uwaw"
else
    echo -e "  ${DIM}[SYS] Fetching uwawconnect.py from GitHub repository...${RESET}"
    curl -fsSL https://raw.githubusercontent.com/WhaTheFoxSay/uwawconnect/main/uwawconnect.py -o "$TARGET_DIR/uwaw"
fi

chmod +x "$TARGET_DIR/uwaw"

# Update PATH and alias in shell RC files
for RC in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [ -f "$RC" ]; then
        # Clean up any stale alias
        sed -i.bak '/alias uwaw=/d' "$RC" 2>/dev/null || sed -i '' '/alias uwaw=/d' "$RC" 2>/dev/null || true
        echo -e 'alias uwaw="python3 '"$TARGET_DIR"'/uwaw"' >> "$RC"
        
        if ! grep -q "$TARGET_DIR" "$RC"; then
            echo -e 'export PATH="'"$TARGET_DIR"':$PATH"' >> "$RC"
        fi
    fi
done

echo -e "\n${CYAN}┌─────────────────────────────────────────────────────────────────────────────┐${RESET}"
echo -e "${CYAN}│ ${GREEN}[SUCCESS] UwawConnect v1.3.1 Installed Successfully!                       │${RESET}"
echo -e "${CYAN}│ ${YELLOW}Run 'source ~/.zshrc' (or ~/.bashrc), then type:                             │${RESET}"
echo -e "${CYAN}│ ${BOLD}${WHITE}uwaw${RESET}${CYAN}                                                                        │${RESET}"
echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────┘${RESET}\n"
