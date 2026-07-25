#!/usr/bin/env python3
"""
UwawConnect v1.1.2 - Professional Terminal Serial Console Interface
Architecture: Cross-Platform (macOS, Linux, BSD, Solaris, Haiku, Windows POSIX/Win32)
Branding: Wownet High-Performance Operations
License: GNU General Public License v3.0 (GPL-3.0)
Copyright (C) 2026 Wownet Infrastructure Operations & Contributors
"""

import sys
import os
import glob
import time
import re
import json
import urllib.request

# Cross-platform terminal raw mode imports
IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty
    import select

# Version & Governance Constants
__version__ = "1.3.0"
__release_channel__ = "stable"

REPO_OWNER = "WhaTheFoxSay"
REPO_NAME = "uwawconnect"
GITHUB_API_RELEASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/uwawconnect.py"

# Vendor Detection Signatures (Regex match patterns against incoming serial output)
VENDOR_SIGNATURES = [
    ("MikroTik RouterOS", [r"RouterOS", r"MikroTik", r"\[[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+\]"]),
    ("Cisco IOS / XE", [r"Cisco IOS", r"Cisco Nexus", r"Cisco Systems", r"User Access Verification", r"Line con0 is now available"]),
    ("Juniper JunOS", [r"JUNOS", r"Juniper Networks", r"root@[a-zA-Z0-9_-]+>", r"%-"]),
    ("Fortinet FortiOS", [r"FortiGate", r"FortiOS", r"Welcome to FortiGate"]),
    ("Huawei VRP", [r"Huawei Versatile Routing Platform", r"<HUAWEI>", r"<[a-zA-Z0-9_-]+>"]),
    ("VyOS Router", [r"VyOS", r"vyos@[a-zA-Z0-9_-]+:"]),
    ("Linux OS", [r"Linux", r"Ubuntu", r"Debian", r"AlmaLinux", r"RHEL", r"Alpine", r"Raspbian"])
]

# Vendor Diagnostic Cheat-Sheet Command Presets
VENDOR_CHEATSHEETS = {
    "Cisco IOS / XE": [
        ("Show IP Interface Brief", "show ip interface brief"),
        ("Show Running Configuration", "show running-config"),
        ("Show Hardware & System Version", "show version"),
        ("Show IP Routing Table", "show ip route"),
        ("Show Connected CDP Neighbors", "show cdp neighbors"),
    ],
    "MikroTik RouterOS": [
        ("Print IP Interfaces & Addresses", "/ip address print"),
        ("Print Full System Export (Compact)", "/export compact"),
        ("Print CPU & System Resources", "/system resource print"),
        ("Print Active Interface Status", "/interface print"),
        ("Print IP Routing Table", "/ip route print"),
    ],
    "Juniper JunOS": [
        ("Show Interfaces Terse", "show interfaces terse"),
        ("Show Configuration System", "show configuration"),
        ("Show IP Routing Table", "show route"),
        ("Show System Information", "show system information"),
        ("Show LLDP Neighbors", "show lldp neighbors"),
    ],
    "Fortinet FortiOS": [
        ("Get System Status", "get system status"),
        ("Show System Interface", "show system interface"),
        ("Get Routing Table", "get router info routing-table all"),
        ("Get Hardware Performance", "get system performance status"),
    ],
    "Huawei VRP": [
        ("Display IP Interface Brief", "display ip interface brief"),
        ("Display Current Configuration", "display current-configuration"),
        ("Display Version Info", "display version"),
        ("Display IP Routing Table", "display ip routing-table"),
    ],
    "Linux OS": [
        ("Show Network Interfaces & IPs", "ip a"),
        ("Show IP Routing Table", "ip route"),
        ("Show System Resource Usage", "free -h && df -h"),
        ("Show Kernel Messages (Dmesg)", "dmesg -T | tail -n 20"),
    ],
    "General / Standard": [
        ("Show IP Interface Summary", "show ip interface brief"),
        ("Show System Status / Version", "show version"),
        ("Show Running Configuration", "show running-config"),
        ("Print IP Addresses (Linux/MikroTik)", "ip a"),
    ]
}

# Directory Setup
UWAW_BASE_DIR = os.path.expanduser("~/.uwaw")
LOGS_DIR = os.path.join(UWAW_BASE_DIR, "logs")
CONFIGS_DIR = os.path.join(UWAW_BASE_DIR, "configs")
MACROS_DIR = os.path.join(UWAW_BASE_DIR, "macros")

def ensure_uwaw_directories():
    """Ensures ~/.uwaw log, config, and macro directories exist with default templates."""
    for d in [LOGS_DIR, CONFIGS_DIR, MACROS_DIR]:
        os.makedirs(d, exist_ok=True)
    
    sample_cisco = os.path.join(MACROS_DIR, "cisco_initial_setup.txt")
    if not os.path.exists(sample_cisco):
        try:
            with open(sample_cisco, "w") as f:
                f.write("# Cisco IOS Initial Setup Macro Template\n")
                f.write("enable\n")
                f.write("configure terminal\n")
                f.write("no ip domain-lookup\n")
                f.write("line con 0\n")
                f.write(" logging synchronous\n")
                f.write(" exec-timeout 0 0\n")
                f.write("exit\n")
                f.write("end\n")
        except Exception:
            pass

    sample_mikrotik = os.path.join(MACROS_DIR, "mikrotik_initial_setup.txt")
    if not os.path.exists(sample_mikrotik):
        try:
            with open(sample_mikrotik, "w") as f:
                f.write("# MikroTik RouterOS Initial Setup Macro Template\n")
                f.write("/system identity set name=UwawRouter\n")
                f.write("/ip service disable telnet,ftp,www\n")
        except Exception:
            pass

    sample_linux = os.path.join(MACROS_DIR, "linux_quick_diag.txt")
    if not os.path.exists(sample_linux):
        try:
            with open(sample_linux, "w") as f:
                f.write("# Linux Quick Diagnostic Macro Template\n")
                f.write("uname -a\n")
                f.write("ip a\n")
                f.write("uptime\n")
                f.write("df -h\n")
        except Exception:
            pass

# Universal High-Contrast ANSI Color Tokens (Compatible with Light & Dark Terminals)
CYAN = "\033[36m"        # Frame Cyan
MAGENTA = "\033[35m"     # Accent Magenta
GREEN = "\033[32m"       # Success/Mode Dark Green
YELLOW = "\033[33m"      # Highlight Amber Yellow
RED = "\033[31m"         # Exit/Alert Red
BOLD = "\033[1m"         # Bold Foreground
DIM = "\033[0m"          # Standard Text
RESET = "\033[0m"        # Standard Reset
WHITE = "\033[1m"        # Crisp Bold Text (Adapts to Light & Dark terminal)
BG = ""

HEADER_BOX = f"""{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐
│ {WHITE}UWAWCONNECT v{__version__}{RESET}{CYAN} ── Serial Console System ({GREEN}{__release_channel__.upper()}{CYAN})                 │
│ Wownet Infrastructure Operating Console Interface                           │
└─────────────────────────────────────────────────────────────────────────────┘{RESET}"""

def strip_ansi_codes(text):
    """Removes ANSI formatting escape sequences from raw string."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def grab_running_config(ser, detected_vendor, port):
    """Auto-sends vendor config export command and captures output into ~/.uwaw/configs/."""
    ensure_uwaw_directories()
    cmd_map = {
        "Cisco IOS / XE": "show running-config",
        "MikroTik RouterOS": "/export compact",
        "Juniper JunOS": "show configuration",
        "Fortinet FortiOS": "show system interface",
        "Huawei VRP": "display current-configuration",
        "VyOS Router": "show configuration",
        "Linux OS": "ip a && ip route"
    }
    cmd = cmd_map.get(detected_vendor, "show running-config")
    clean_port = os.path.basename(port).replace('/', '_')
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(CONFIGS_DIR, f"config_{clean_port}_{timestamp}.cfg")

    sys.stdout.write(f"\r\n  {YELLOW}[SYS CONFIG GRABBER] Requesting config via '{cmd}'...{RESET}\r\n")
    sys.stdout.flush()
    ser.write((cmd + "\r").encode('utf-8'))

    time.sleep(0.5)
    captured = ""
    start_time = time.time()
    while time.time() - start_time < 3.5:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            if data:
                text = data.decode('utf-8', errors='ignore')
                captured += text
                if "--More--" in text or "---(more" in text:
                    ser.write(b" ")
        time.sleep(0.1)

    clean_content = strip_ansi_codes(captured)
    try:
        with open(file_path, "w") as f:
            f.write(f"# UwawConnect Config Export - Device: {port} | Vendor: {detected_vendor} | Date: {time.ctime()}\n")
            f.write(clean_content)
        sys.stdout.write(f"  {GREEN}[SYS SUCCESS] Config saved to: {file_path}{RESET}\r\n")
    except Exception as e:
        sys.stdout.write(f"  {RED}[ERROR] Failed to save config file: {e}{RESET}\r\n")
    sys.stdout.flush()

def render_macro_overlay():
    """Lists files in ~/.uwaw/macros/ and injects chosen macro line-by-line to serial line."""
    def make_box_line(content, width=79):
        vlen = len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content))
        pad = max(0, width - 2 - vlen)
        return f"{CYAN}│{RESET}{content}{' '*pad}{CYAN}│{RESET}"

    ensure_uwaw_directories()
    macro_files = sorted([f for f in os.listdir(MACROS_DIR) if os.path.isfile(os.path.join(MACROS_DIR, f))])
    if not macro_files:
        sys.stdout.write(f"\r\n  {YELLOW}[SYS] No macro files found in {MACROS_DIR}{RESET}\r\n")
        return None

    l1 = f"{CYAN}┌── AUTOMATION MACRO PLAYBOOKS [{BOLD}~/.uwaw/macros/{RESET}{CYAN}] ─────────────────────────┐{RESET}"
    l2_c = f" Select macro playbook [1-{len(macro_files)}] to execute, or [Q/ESC] to cancel:"
    l_sep = f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}"

    print(f"\r\n\n{l1}")
    print(make_box_line(l2_c))
    print(l_sep)
    for idx, fname in enumerate(macro_files, 1):
        row_c = f" [{idx}] {fname:<68}"
        print(make_box_line(row_c))
    print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}")
    print(f"  {YELLOW}[>] Select Macro [1-{len(macro_files)} / Q]: {RESET}", end="", flush=True)

    choice = get_key()
    print(choice)
    if choice.isdigit() and 1 <= int(choice) <= len(macro_files):
        target_file = os.path.join(MACROS_DIR, macro_files[int(choice) - 1])
        try:
            with open(target_file, "r") as f:
                lines = f.readlines()
            sys.stdout.write(f"\r\n  {GREEN}[SYS MACRO] Executing {macro_files[int(choice)-1]} ({len(lines)} lines)...{RESET}\r\n")
            sys.stdout.flush()
            return [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]
        except Exception as e:
            sys.stdout.write(f"\r\n  {RED}[ERROR] Failed to read macro: {e}{RESET}\r\n")
    return None

def trigger_break_signal(ser):
    """Sends hardware UART Break signal and displays ROMMON / Password Recovery Reference."""
    def make_box_line(content, width=79):
        vlen = len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content))
        pad = max(0, width - 2 - vlen)
        return f"{CYAN}│{RESET}{content}{' '*pad}{CYAN}│{RESET}"

    sys.stdout.write(f"\r\n  {YELLOW}[SYS HARDWARE BREAK] Sending UART Break Signal (0.25s pulse)...{RESET}\r\n")
    sys.stdout.flush()
    try:
        ser.send_break(0.25)
    except Exception:
        try:
            ser.break_condition = True
            time.sleep(0.25)
            ser.break_condition = False
        except Exception as e:
            sys.stdout.write(f"  {RED}[ERROR] Hardware Break failed: {e}{RESET}\r\n")

    b1 = f"{CYAN}┌── ROUTER & SWITCH PASSWORD RECOVERY QUICK REFERENCE ────────────────────────┐{RESET}"
    b2_c = f" CISCO IOS ROMMON: {YELLOW}confreg 0x2142{RESET} -> {YELLOW}reset{RESET} (Bypasses startup-config)"
    b3_c = f" JUNIPER JUNOS:   {YELLOW}boot -s{RESET} -> {YELLOW}recovery{RESET} -> {YELLOW}set system root-authentication{RESET}"
    b4_c = f" MIKROTIK:        Hold Reset Button on Boot until User LED flashes"
    b5 = f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}"

    print(f"\r\n{b1}\n{make_box_line(b2_c)}\n{make_box_line(b3_c)}\n{make_box_line(b4_c)}\n{b5}\n")
    sys.stdout.flush()

HEADER_BOX = f"""{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐
│ {WHITE}{BOLD}UWAWCONNECT v{__version__}{RESET}{CYAN} ── Serial Console System ({GREEN}{__release_channel__.upper()}{CYAN})                 │
│ {DIM}Wownet Infrastructure Operating Console Interface{RESET}{CYAN}                     │
└─────────────────────────────────────────────────────────────────────────────┘{RESET}"""

BAUD_RATES = [115200, 9600, 57600, 38400, 19200, 4800]

def print_goodbye():
    print(f"\n{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{CYAN}│ {GREEN}[SYS] UwawConnect Session Terminated.                                       {CYAN}│{RESET}")
    print(f"{CYAN}│ {YELLOW}See You Next Time :)                                                        {CYAN}│{RESET}")
    print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

def print_uninstall_goodbye():
    print(f"\n{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{CYAN}│ {GREEN}[SYS] UwawConnect Has Been Successfully Uninstalled.                          {CYAN}│{RESET}")
    print(f"{CYAN}│ {YELLOW}Thank You for Using UwawConnect! Hope to See You Again Soon :)               {CYAN}│{RESET}")
    print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

def get_key():
    """Reads a single keypress without waiting for Enter across Windows, Mac, Linux."""
    if IS_WINDOWS:
        ch = msvcrt.getch()
        try:
            return ch.decode('utf-8', errors='ignore')
        except Exception:
            return ''
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def animated_loading(text, duration=0.4):
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    idx = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r  {CYAN}[{spinners[idx % len(spinners)]}]{RESET} {WHITE}{text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.04)
        idx += 1
    sys.stdout.write(f"\r  {GREEN}[OK]{RESET} {WHITE}{text}{RESET}\n")
    sys.stdout.flush()

def find_serial_ports():
    ports = []
    if IS_WINDOWS:
        try:
            import serial.tools.list_ports
            ports = [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            for i in range(1, 32):
                ports.append(f"COM{i}")
    else:
        patterns = [
            # macOS (Darwin BSD)
            '/dev/cu.usbserial*',
            '/dev/tty.usbserial*',
            '/dev/cu.usbmodem*',
            '/dev/tty.usbmodem*',
            '/dev/cu.SLAB*',
            '/dev/cu.wch*',
            # Linux (Standard & USB ACM)
            '/dev/ttyUSB*',
            '/dev/ttyACM*',
            # BSD (FreeBSD, OpenBSD, NetBSD)
            '/dev/cuaU*',
            '/dev/cuau*',
            '/dev/ttyU*',
            # Solaris / Illumos / SmartOS
            '/dev/term/*',
            # Haiku OS
            '/dev/ports/*'
        ]
        for pattern in patterns:
            ports.extend(glob.glob(pattern))
    return sorted(list(set(ports)))

def clear_screen():
    os.system('cls' if IS_WINDOWS else 'clear')

def print_banner():
    clear_screen()
    print(HEADER_BOX)

def perform_uninstall():
    print_banner()
    print(f"\n  {RED}{BOLD}UNINSTALL UWAWCONNECT{RESET}")
    print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
    confirm = input(f"\n  {YELLOW}[?] Are you sure you want to uninstall UwawConnect? [y/N]: {RESET}").strip().lower()
    if confirm != 'y':
        print(f"\n  {GREEN}[SYS] Uninstall cancelled.{RESET}")
        time.sleep(0.8)
        return False
    
    animated_loading("Removing binaries and executable paths...", 0.4)
    if IS_WINDOWS:
        win_path = os.path.expanduser('~\\AppData\\Local\\Microsoft\\WindowsApps\\uwaw.cmd')
        if os.path.exists(win_path):
            try:
                os.remove(win_path)
            except Exception:
                pass
    else:
        target_files = [
            os.path.expanduser('~/bin/uwaw'),
            os.path.expanduser('~/.local/bin/uwaw'),
            os.path.expanduser('~/uwawconnect'),
            '/usr/local/bin/uwaw'
        ]
        for tf in target_files:
            if os.path.exists(tf):
                try:
                    os.remove(tf)
                except Exception:
                    pass

        rc_files = [os.path.expanduser('~/.zshrc'), os.path.expanduser('~/.bashrc')]
        for rc in rc_files:
            if os.path.exists(rc):
                try:
                    with open(rc, 'r') as f:
                        lines = f.readlines()
                    new_lines = [l for l in lines if 'alias uwaw=' not in l and 'uwawconnect' not in l]
                    with open(rc, 'w') as f:
                        f.writelines(new_lines)
                except Exception:
                    pass

    print_uninstall_goodbye()
    sys.exit(0)

def detect_vendor(accumulated_text):
    """Inspects text buffer for vendor signatures and returns detected vendor string or None."""
    for vendor_name, patterns in VENDOR_SIGNATURES:
        for pat in patterns:
            if re.search(pat, accumulated_text, re.IGNORECASE):
                return vendor_name
    return None

def format_bytes(n_bytes):
    """Formats byte counts into human-readable strings (e.g. 1.2 KB, 3.4 MB)."""
    if n_bytes < 1024:
        return f"{n_bytes} B"
    elif n_bytes < 1024 * 1024:
        return f"{n_bytes / 1024:.1f} KB"
    else:
        return f"{n_bytes / (1024 * 1024):.1f} MB"

def render_cheatsheet_overlay(detected_vendor=None):
    """
    Renders ANSI box overlay displaying vendor-specific command shortcuts.
    Allows user to select 1-N or press ESC/Q to return.
    Returns the selected command string (or None).
    """
    def make_box_line(content, width=79):
        vlen = len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content))
        pad = max(0, width - 2 - vlen)
        return f"{CYAN}│{RESET}{content}{' '*pad}{CYAN}│{RESET}"

    vendor_key = (detected_vendor if (detected_vendor in VENDOR_CHEATSHEETS) else "General / Standard").upper()
    commands = VENDOR_CHEATSHEETS.get(detected_vendor, VENDOR_CHEATSHEETS["General / Standard"])

    dash_cnt = max(0, 79 - 33 - len(vendor_key))
    l1 = f"{CYAN}┌── VENDOR QUICK CHEAT-SHEET [{BOLD}{vendor_key}{RESET}{CYAN}] {'─'*dash_cnt}┐{RESET}"
    l2_c = f" Press key [1-{len(commands)}] to auto-inject command, or [Q/ESC] to cancel:"
    l_sep = f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}"

    print(f"\r\n\n{l1}")
    print(make_box_line(l2_c))
    print(l_sep)
    for idx, (label, cmd) in enumerate(commands, 1):
        row_c = f" [{idx}] {label:<35} -> {cmd:<25}"
        print(make_box_line(row_c))
    print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}")
    print(f"  {YELLOW}[>] Select Command [1-{len(commands)} / Q]: {RESET}", end="", flush=True)

    choice = get_key()
    print(choice)
    if choice.isdigit() and 1 <= int(choice) <= len(commands):
        selected_label, selected_cmd = commands[int(choice) - 1]
        sys.stdout.write(f"\r\n  {GREEN}[SYS] Injecting: {selected_cmd}{RESET}\r\n")
        sys.stdout.flush()
        return selected_cmd + "\r"
    return None

def parse_version_tuple(v_str):
    """
    Parses version strings like 'v1.1.2a', '1.0.0', 'v1.2.0-hotfix1' into comparable tuples.
    Returns (major, minor, patch, suffix).
    """
    cleaned = str(v_str).strip().lstrip('vV')
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(.*)$', cleaned)
    if match:
        major, minor, patch, suffix = match.groups()
        return (int(major), int(minor), int(patch), suffix)
    return (0, 0, 0, cleaned)

def is_newer_version(latest_ver, current_ver):
    return parse_version_tuple(latest_ver) > parse_version_tuple(current_ver)

def check_for_updates():
    print_banner()
    print(f"\n  {BOLD}CHECK FOR UPDATES{RESET}")
    print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
    animated_loading("Connecting to GitHub release server...", 0.5)

    latest_version = None
    release_notes = ""
    download_url = GITHUB_RAW_URL

    req = urllib.request.Request(
        GITHUB_API_RELEASE_URL,
        headers={"User-Agent": f"UwawConnect/{__version__}"}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get("tag_name", "").lstrip('v')
                release_notes = data.get("body", "No release notes provided.")
    except Exception:
        # Fallback: check raw python file version constant
        try:
            raw_req = urllib.request.Request(
                GITHUB_RAW_URL,
                headers={"User-Agent": f"UwawConnect/{__version__}"}
            )
            with urllib.request.urlopen(raw_req, timeout=5) as raw_resp:
                if raw_resp.status == 200:
                    content = raw_resp.read().decode('utf-8')
                    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        latest_version = match.group(1)
        except Exception:
            pass

    if not latest_version:
        print(f"\n  {RED}[!] Unable to reach update server (offline or repository un-released).{RESET}")
        print(f"  {DIM}Working in offline mode. Current version: v{__version__}{RESET}\n")
        input(f"  {YELLOW}Press ENTER to return to main menu...{RESET}")
        return

    if is_newer_version(latest_version, __version__):
        print(f"\n  {GREEN}[+] New Update Available!{RESET}")
        print(f"  {DIM}Current Installed Version:{RESET} v{__version__}")
        print(f"  {GREEN}{BOLD}Latest Remote Release:{RESET}    v{latest_version}")
        if release_notes:
            print(f"\n  {BOLD}Release Notes:{RESET}")
            for line in release_notes.strip().splitlines()[:8]:
                print(f"    {DIM}{line}{RESET}")
        
        print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
        confirm = input(f"\n  {YELLOW}[?] Install update now (in-place)? [Y/n]: {RESET}").strip().lower()
        if confirm in ('', 'y', 'yes'):
            animated_loading(f"Downloading UwawConnect v{latest_version}...", 0.6)
            try:
                raw_req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": f"UwawConnect/{__version__}"}
                )
                with urllib.request.urlopen(raw_req, timeout=10) as resp:
                    new_code = resp.read().decode('utf-8')
                
                target_path = os.path.abspath(sys.argv[0])
                backup_path = target_path + ".bak"

                # Backup existing script
                with open(target_path, 'r', encoding='utf-8') as f:
                    old_code = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(old_code)

                # Overwrite script
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(new_code)

                print(f"\n  {GREEN}[OK] Update completed successfully!{RESET}")
                print(f"  {DIM}[SYS] Safety backup saved to {backup_path}{RESET}")
                print(f"  {CYAN}[SYS] Restarting UwawConnect v{latest_version}...{RESET}\n")
                time.sleep(1.2)
                
                # Re-exec process
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                print(f"\n  {RED}[ERROR] Update failed:{RESET} {e}")
                input(f"\n  {YELLOW}Press ENTER to return to main menu...{RESET}")
    else:
        print(f"\n  {GREEN}[OK] UwawConnect is up to date!{RESET}")
        print(f"  {DIM}You are running the latest version (v{__version__}).{RESET}\n")
        input(f"  {YELLOW}Press ENTER to return to main menu...{RESET}")

def setup_menu():
    while True:
        print_banner()
        animated_loading("Scanning hardware bus for active serial interfaces...", 0.4)
        
        ports = find_serial_ports()
        print()
        print(f"  {BOLD}PORT SELECTION{RESET}")
        print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
        
        default_manual = "COM3" if IS_WINDOWS else "/dev/cu.usbserial-1410"

        if not ports:
            print(f"  {RED}[!] No serial interfaces automatically detected.{RESET}")
            print(f"  {CYAN}[M]{RESET} Specify Custom Device Path...")
            print(f"  {CYAN}[C]{RESET} Check for Updates (v{__version__})...")
            print(f"  {CYAN}[U]{RESET} Uninstall UwawConnect")
            print(f"  {CYAN}[Q]{RESET} Quit Application")
            print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
            print(f"\n  {YELLOW}[>] Press key [M / C / U / Q]: {RESET}", end="", flush=True)
            choice = get_key().upper()
            print(choice)
            if choice == 'Q' or choice == '\x03':
                print_goodbye()
                sys.exit(0)
            elif choice == 'C':
                check_for_updates()
                continue
            elif choice == 'U':
                perform_uninstall()
                continue
            elif choice == 'M':
                selected_port = input(f"\n  {YELLOW}[>] Enter serial device path [{default_manual}]: {RESET}").strip()
                if not selected_port:
                    selected_port = default_manual
            else:
                continue
        else:
            for idx, port in enumerate(ports, 1):
                print(f"  {CYAN}[{idx}]{RESET} {WHITE}{port}{RESET}")
            print(f"  {CYAN}[M]{RESET} {DIM}Specify Custom Device Path...{RESET}")
            print(f"  {CYAN}[C]{RESET} {DIM}Check for Updates (v{__version__})...{RESET}")
            print(f"  {CYAN}[U]{RESET} {DIM}Uninstall UwawConnect...{RESET}")
            print(f"  {CYAN}[Q]{RESET} {DIM}Quit Application{RESET}")
            print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
            
            print(f"\n  {YELLOW}[>] Press Key [1-{len(ports)} / M / C / U / Q]: {RESET}", end="", flush=True)
            choice = get_key().upper()
            print(choice)
            if choice == 'Q' or choice == '\x03':
                print_goodbye()
                sys.exit(0)
            elif choice == 'C':
                check_for_updates()
                continue
            elif choice == 'U':
                perform_uninstall()
                continue
            elif choice == 'M':
                selected_port = input(f"\n  {YELLOW}[>] Enter custom device path: {RESET}").strip()
            elif choice.isdigit() and 1 <= int(choice) <= len(ports):
                selected_port = ports[int(choice) - 1]
            else:
                selected_port = ports[0]

        # Baudrate Selection
        print()
        animated_loading("Configuring serial line parameters...", 0.3)
        print(f"\n  {BOLD}BAUDRATE PRESETS{RESET}")
        print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
        for idx, baud in enumerate(BAUD_RATES, 1):
            info = " (MikroTik / Default)" if baud == 115200 else (" (Cisco / Hardware Standard)" if baud == 9600 else "")
            print(f"  {CYAN}[{idx}]{RESET} {YELLOW}{baud}{RESET} bps{DIM}{info}{RESET}")
        print(f"  {CYAN}[C]{RESET} {DIM}Specify Custom Speed...{RESET}")
        print(f"  {CYAN}[B]{RESET} {DIM}Back to Port Selection{RESET}")
        print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
        
        print(f"\n  {YELLOW}[>] Press Key [1-{len(BAUD_RATES)} / C / B]: {RESET}", end="", flush=True)
        b_choice = get_key().upper()
        print(b_choice)
        if b_choice == 'B':
            continue
        elif b_choice == 'C':
            try:
                selected_baud = int(input(f"\n  {YELLOW}[>] Enter custom baudrate (press Enter): {RESET}").strip())
            except ValueError:
                selected_baud = 115200
        elif b_choice.isdigit() and 1 <= int(b_choice) <= len(BAUD_RATES):
            selected_baud = BAUD_RATES[int(b_choice) - 1]
        else:
            selected_baud = 115200

        return selected_port, selected_baud

def run_session(port, baud):
    try:
        import serial
    except ImportError:
        os.system("pip3 install pyserial --break-system-packages >/dev/null 2>&1")
        import serial

    ensure_uwaw_directories()
    print_banner()
    animated_loading(f"Releasing port lock for {port}...", 0.3)
    if not IS_WINDOWS:
        os.system("killall -9 minicom screen 2>/dev/null")
    
    animated_loading(f"Initializing UART connection at {baud} 8N1...", 0.4)
    time.sleep(0.1)

    try:
        ser = serial.Serial(port, baud, timeout=0.05)
    except Exception as e:
        print(f"\n  {RED}[ERROR] Failed to open {port}:{RESET} {e}")
        input(f"\n  {YELLOW}Press ENTER to return to setup menu...{RESET}")
        return 'RESTART'

    clear_screen()
    def make_box_line(content, width=79):
        vlen = len(re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', content))
        pad = max(0, width - 2 - vlen)
        return f"{CYAN}│{RESET}{content}{' '*pad}{CYAN}│{RESET}"

    l1 = f"{CYAN}┌── SYSTEM SESSION ACTIVE ────────────────────────────────────────────────────┐{RESET}"
    l2_c = f" DEVICE: {WHITE}{port:<20}{RESET} {CYAN}│{RESET} SPEED: {YELLOW}{baud:<6}{RESET} bps {CYAN}│{RESET} MODE: {GREEN}8N1 RAW{RESET}"
    l3_c = f" HOTKEYS: {YELLOW}[Ctrl+A]{RESET} Cheat {CYAN}│{RESET} {YELLOW}[Ctrl+L]{RESET} Log {CYAN}│{RESET} {YELLOW}[Ctrl+B]{RESET} Backup {CYAN}│{RESET} {YELLOW}[Ctrl+P]{RESET} Playbook"
    l4_c = f" CONTROL: {YELLOW}[Ctrl+F]{RESET} Break {CYAN}│{RESET} {YELLOW}[Ctrl+R]{CYAN} Menu {CYAN}│{RESET} {RED}[Ctrl+C]{RESET} Exit Session"
    l5 = f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}"

    status_bar = f"{l1}\n{make_box_line(l2_c)}\n{make_box_line(l3_c)}\n{make_box_line(l4_c)}\n{l5}\n"
    print(status_bar)
    sys.stdout.write(f"{DIM}[SYS] Line ready. Press ENTER to wake target CLI prompt...{RESET}\n\n")
    sys.stdout.flush()

    action = 'QUIT'

    rx_bytes_total = 0
    tx_bytes_total = 0
    rx_buffer_text = ""
    detected_vendor = None

    is_logging = False
    log_file_handle = None
    log_file_path = None

    def toggle_logging():
        nonlocal is_logging, log_file_handle, log_file_path
        if not is_logging:
            clean_port = os.path.basename(port).replace('/', '_')
            ts = time.strftime("%Y%m%d_%H%M%S")
            log_file_path = os.path.join(LOGS_DIR, f"session_{clean_port}_{ts}.log")
            try:
                log_file_handle = open(log_file_path, "a", encoding="utf-8", errors="ignore")
                log_file_handle.write(f"=== UwawConnect Session Log Started: {time.ctime()} ===\n")
                log_file_handle.flush()
                is_logging = True
                sys.stdout.write(f"\r\n  {GREEN}[SYS LOGGING ENABLED]{RESET} {WHITE}{log_file_path}{RESET}\r\n")
            except Exception as e:
                sys.stdout.write(f"\r\n  {RED}[ERROR] Failed to start logging: {e}{RESET}\r\n")
        else:
            if log_file_handle:
                log_file_handle.write(f"\n=== UwawConnect Session Log Ended: {time.ctime()} ===\n")
                log_file_handle.close()
                log_file_handle = None
            is_logging = False
            sys.stdout.write(f"\r\n  {YELLOW}[SYS LOGGING DISABLED]{RESET}\r\n")
        sys.stdout.flush()

    if IS_WINDOWS:
        last_recv_time = time.time()
        has_received_data = False
        warning_printed = False
        try:
            while True:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in (b'\x03', b'\x1d'): # Ctrl+C or Ctrl+]
                        action = 'QUIT'
                        break
                    elif ch == b'\x12': # Ctrl+R Menu
                        action = 'RESTART'
                        break
                    elif ch == b'\x01': # Ctrl+A CheatSheet
                        cmd = render_cheatsheet_overlay(detected_vendor)
                        if cmd:
                            ser.write(cmd.encode('utf-8'))
                            tx_bytes_total += len(cmd)
                        continue
                    elif ch == b'\x02': # Ctrl+B Backup Config
                        grab_running_config(ser, detected_vendor, port)
                        continue
                    elif ch == b'\x06': # Ctrl+F Break Signal
                        trigger_break_signal(ser)
                        continue
                    elif ch == b'\x0c': # Ctrl+L Toggle Log
                        toggle_logging()
                        continue
                    elif ch == b'\x10': # Ctrl+P Playbook / Macro
                        macro_cmds = render_macro_overlay()
                        if macro_cmds:
                            for mline in macro_cmds:
                                ser.write((mline + "\r").encode('utf-8'))
                                tx_bytes_total += len(mline) + 1
                                time.sleep(0.3)
                        continue
                    elif ch == b'\x14': # Ctrl+T Theme Switcher
                        render_theme_overlay()
                        continue

                    ser.write(ch)
                    tx_bytes_total += len(ch)

                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    if data:
                        has_received_data = True
                        last_recv_time = time.time()
                        rx_bytes_total += len(data)
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()

                        text = data.decode('utf-8', errors='ignore')
                        if is_logging and log_file_handle:
                            log_file_handle.write(strip_ansi_codes(text))
                            log_file_handle.flush()

                        if detected_vendor is None:
                            rx_buffer_text += text
                            if len(rx_buffer_text) > 4096:
                                rx_buffer_text = rx_buffer_text[-4096:]
                            v = detect_vendor(rx_buffer_text)
                            if v:
                                detected_vendor = v
                                sys.stdout.write(f"\r\n  {GREEN}[SYS VENDOR DETECTED]{RESET} {WHITE}{BOLD}{detected_vendor}{RESET}\r\n")
                                sys.stdout.flush()

                if not has_received_data and not warning_printed and (time.time() - last_recv_time > 6.0):
                    sys.stdout.write(f"\r\n\r\n{YELLOW}[SYS WARNING] No data received from target device after 6s.{RESET}\r\n")
                    sys.stdout.write(f"{DIM}[SYS ADVICE] 1. Press ENTER 1-2x to trigger the device CLI login prompt.{RESET}\r\n")
                    sys.stdout.write(f"{DIM}[SYS ADVICE] 2. If output is silent or garbled, the baudrate ({baud}) may be incorrect.{RESET}\r\n")
                    sys.stdout.write(f"{CYAN}[SYS ADVICE] Press [Ctrl+R] to change baudrate or switch port instantly.{RESET}\r\n\r\n")
                    sys.stdout.flush()
                    warning_printed = True
                time.sleep(0.01)
        except KeyboardInterrupt:
            action = 'QUIT'
        finally:
            if is_logging and log_file_handle:
                log_file_handle.close()
            ser.close()
            vendor_disp = detected_vendor if detected_vendor else "Generic / Unknown"
            log_disp = os.path.basename(log_file_path) if is_logging and log_file_path else "Disabled"
            print(f"\n{CYAN}┌── SESSION STATISTICS SUMMARY ──────────────────────────────────────────────┐{RESET}")
            print(f"{CYAN}│ {WHITE}DEVICE:{RESET} {port:<23} │ {WHITE}VENDOR:{RESET} {GREEN}{vendor_disp:<28}{CYAN}│{RESET}")
            print(f"{CYAN}│ {WHITE}RECEIVED (RX):{RESET} {YELLOW}{format_bytes(rx_bytes_total):<15}{CYAN} │ {WHITE}TRANSMITTED (TX):{RESET} {YELLOW}{format_bytes(tx_bytes_total):<19}{CYAN}│{RESET}")
            print(f"{CYAN}│ {WHITE}LOGGING:{RESET} {GREEN}{log_disp:<64}{CYAN}│{RESET}")
            print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

    else:
        # POSIX (macOS & Linux & BSD & Solaris & Haiku)
        old_settings = termios.tcgetattr(sys.stdin)
        last_recv_time = time.time()
        has_received_data = False
        warning_printed = False

        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                rlist, _, _ = select.select([sys.stdin, ser], [], [], 0.05)
                
                if sys.stdin in rlist:
                    ch = sys.stdin.read(1)
                    if ch == '\x03':  # Ctrl+C
                        action = 'QUIT'
                        break
                    elif ch == '\x12':  # Ctrl+R Menu
                        action = 'RESTART'
                        break
                    elif ch == '\x01':  # Ctrl+A CheatSheet
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            cmd = render_cheatsheet_overlay(detected_vendor)
                        finally:
                            tty.setraw(sys.stdin.fileno())
                        if cmd:
                            ser.write(cmd.encode('utf-8'))
                            tx_bytes_total += len(cmd)
                        continue
                    elif ch == '\x02':  # Ctrl+B Backup Config
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            grab_running_config(ser, detected_vendor, port)
                        finally:
                            tty.setraw(sys.stdin.fileno())
                        continue
                    elif ch == '\x06':  # Ctrl+F Break Signal
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            trigger_break_signal(ser)
                        finally:
                            tty.setraw(sys.stdin.fileno())
                        continue
                    elif ch == '\x0c':  # Ctrl+L Toggle Log
                        toggle_logging()
                        continue
                    elif ch == '\x10':  # Ctrl+P Playbook / Macro
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            macro_cmds = render_macro_overlay()
                        finally:
                            tty.setraw(sys.stdin.fileno())
                        if macro_cmds:
                            for mline in macro_cmds:
                                ser.write((mline + "\r").encode('utf-8'))
                                tx_bytes_total += len(mline) + 1
                                time.sleep(0.3)
                        continue
                    elif ch == '\x14':  # Ctrl+T Theme Switcher
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        try:
                            render_theme_overlay()
                        finally:
                            tty.setraw(sys.stdin.fileno())
                        continue

                    ser.write(ch.encode('utf-8', errors='ignore'))
                    tx_bytes_total += len(ch)

                if ser in rlist:
                    data = ser.read(2048)
                    if data:
                        has_received_data = True
                        last_recv_time = time.time()
                        rx_bytes_total += len(data)
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()

                        text = data.decode('utf-8', errors='ignore')
                        if is_logging and log_file_handle:
                            log_file_handle.write(strip_ansi_codes(text))
                            log_file_handle.flush()

                        if detected_vendor is None:
                            rx_buffer_text += text
                            if len(rx_buffer_text) > 4096:
                                rx_buffer_text = rx_buffer_text[-4096:]
                            v = detect_vendor(rx_buffer_text)
                            if v:
                                detected_vendor = v
                                sys.stdout.write(f"\r\n  {GREEN}[SYS VENDOR DETECTED]{RESET} {WHITE}{BOLD}{detected_vendor}{RESET}\r\n")
                                sys.stdout.flush()

                if not has_received_data and not warning_printed and (time.time() - last_recv_time > 6.0):
                    sys.stdout.write(f"\r\n\r\n{YELLOW}[SYS WARNING] No data received from target device after 6s.{RESET}\r\n")
                    sys.stdout.write(f"{DIM}[SYS ADVICE] 1. Press ENTER 1-2x to trigger the device CLI login prompt.{RESET}\r\n")
                    sys.stdout.write(f"{DIM}[SYS ADVICE] 2. If output is silent or garbled, the baudrate ({baud}) may be incorrect.{RESET}\r\n")
                    sys.stdout.write(f"{CYAN}[SYS ADVICE] Press [Ctrl+R] to change baudrate or switch port instantly.{RESET}\r\n\r\n")
                    sys.stdout.flush()
                    warning_printed = True

        except KeyboardInterrupt:
            action = 'QUIT'
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            if is_logging and log_file_handle:
                log_file_handle.close()
            ser.close()
            vendor_disp = detected_vendor if detected_vendor else "Generic / Unknown"
            log_disp = os.path.basename(log_file_path) if is_logging and log_file_path else "Disabled"
            print(f"\n{CYAN}┌── SESSION STATISTICS SUMMARY ──────────────────────────────────────────────┐{RESET}")
            print(f"{CYAN}│ {WHITE}DEVICE:{RESET} {port:<23} │ {WHITE}VENDOR:{RESET} {GREEN}{vendor_disp:<28}{CYAN}│{RESET}")
            print(f"{CYAN}│ {WHITE}RECEIVED (RX):{RESET} {YELLOW}{format_bytes(rx_bytes_total):<15}{CYAN} │ {WHITE}TRANSMITTED (TX):{RESET} {YELLOW}{format_bytes(tx_bytes_total):<19}{CYAN}│{RESET}")
            print(f"{CYAN}│ {WHITE}LOGGING:{RESET} {GREEN}{log_disp:<64}{CYAN}│{RESET}")
            print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

    return action

def main():
    while True:
        if len(sys.argv) >= 2:
            port = sys.argv[1]
            baud = int(sys.argv[2]) if len(sys.argv) >= 3 else 115200
            sys.argv = [] # Clear after first run
        else:
            port, baud = setup_menu()

        result = run_session(port, baud)
        if result == 'QUIT':
            print_goodbye()
            break

if __name__ == '__main__':
    main()
