# ⚡ UwawConnect v1.0

> **Next-Generation Cross-Platform Serial Terminal Console Interface**  
> Built for Network Engineers, Sysadmins, and Infrastructure Operations.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ UWAWCONNECT v1.0 ── Serial Console System                              │
│ Wownet Infrastructure Operating Console Interface                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **🌐 Cross-Platform (macOS, Linux, Windows)**: Seamlessly operates on macOS (Intel/Apple Silicon), Linux (Ubuntu, Debian, RHEL, Arch, Alpine, Raspberry Pi OS), and Windows 10/11 (`COM1`..`COM64`).
- **🌀 High-Tech UNIX Cyberpunk UI**: Built with ANSI Unicode box-drawing frames and real-time ASCII spinners. Zero clunky emojis, 100% clean POSIX indicators (`[OK]`, `[SYS]`, `[ERROR]`).
- **⚡ Instant Keypress Navigation**: Select menu items (`1`, `2`, `M`, `B`, `Q`, `U`) instantly without needing to press the Enter key.
- **🔍 Auto-Hardware Bus Scanning**: Automatically discovers connected USB-to-Serial console cables (FTDI, Prolific, CP2102, CH340, USB ACM).
- **⚠️ Intelligent Baudrate Misconfiguration Warning**: Detects silent serial lines and provides actionable technical troubleshooting.
- **🔄 Hotkey Session Switching**: Press `Ctrl + R` inside an active console session to instantly return to the setup menu and switch baudrates or ports.
- **🛠️ Self-Healing Automated Installer**: Automatically installs Python 3, `pip3`, and `pyserial` dependencies via `apt-get`, `dnf`, `yum`, `brew`, or `winget`.
- **🗑️ Built-in One-Click Uninstaller**: Select `[U]` in the menu to cleanly uninstall the app and remove shell aliases with a friendly farewell banner (`See You Next Time :)`).

---

## 🚀 One-Line Installation

### 🍏 macOS & 🐧 Linux

Run this command in your terminal:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/WhaTheFoxSay/uwawconnect/main/install.sh)
```

Or execute locally:
```bash
bash install.sh
```

Then reload your shell (`source ~/.zshrc` or `source ~/.bashrc`) and run:
```bash
uwaw
```

---

### 🪟 Windows (Command Prompt / PowerShell)

Download the repository and run:
```cmd
install.bat
```

Then open a new Command Prompt or PowerShell window and type:
```cmd
uwaw
```

---

## 🎮 Usage Guide

### Launching the App
Simply type `uwaw` in any terminal:
```bash
uwaw
```

Or pass direct port and speed parameters:
```bash
# macOS / Linux
uwaw /dev/cu.usbserial-1410 115200

# Windows
uwaw COM3 9600
```

### In-Session Hotkeys
| Hotkey | Action |
| :--- | :--- |
| `Ctrl + C` | Instantly exit session / quit app |
| `Ctrl + R` | Return to setup menu (change baudrate or port) |
| `Enter` | Send newline character to wake up target CLI prompt |

---

## 📋 System Requirements

| Requirement | Specification |
| :--- | :--- |
| **OS** | macOS 10.13+, Linux (Kernel 3.10+), Windows 10/11 |
| **Python** | Python 3.6+ (Auto-installed if missing) |
| **Dependencies** | `pyserial` (Auto-installed if missing) |
| **Resource Usage** | `< 15 MB RAM`, `< 0.1% CPU` |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Created with ❤️ for Wownet Infrastructure Management.
