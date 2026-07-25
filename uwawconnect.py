#!/usr/bin/env python3
"""
UwawConnect v1.0 - Professional Terminal Serial Console Interface
Architecture: Cross-Platform (macOS, Linux, Windows POSIX/Win32)
Branding: Wownet High-Performance Operations
"""

import sys
import os
import glob
import time

# Cross-platform terminal raw mode imports
IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    import msvcrt
else:
    import termios
    import tty
    import select

# Professional ANSI Color Tokens
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
WHITE = "\033[1;37m"

HEADER_BOX = f"""{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐
│ {WHITE}{BOLD}UWAWCONNECT v1.0{RESET}{CYAN} ── Serial Console System                              │
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
            '/dev/cu.usbserial*',
            '/dev/tty.usbserial*',
            '/dev/cu.usbmodem*',
            '/dev/tty.usbmodem*',
            '/dev/cu.SLAB*',
            '/dev/cu.wch*'
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
            print(f"  {CYAN}[U]{RESET} Uninstall UwawConnect")
            print(f"  {CYAN}[Q]{RESET} Quit Application")
            print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
            print(f"\n  {YELLOW}[>] Press key [M / U / Q]: {RESET}", end="", flush=True)
            choice = get_key().upper()
            print(choice)
            if choice == 'Q' or choice == '\x03':
                print_goodbye()
                sys.exit(0)
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
            print(f"  {CYAN}[U]{RESET} {DIM}Uninstall UwawConnect...{RESET}")
            print(f"  {CYAN}[Q]{RESET} {DIM}Quit Application{RESET}")
            print(f"  {DIM}───────────────────────────────────────────────────────────────{RESET}")
            
            print(f"\n  {YELLOW}[>] Press Key [1-{len(ports)} / M / U / Q]: {RESET}", end="", flush=True)
            choice = get_key().upper()
            print(choice)
            if choice == 'Q' or choice == '\x03':
                print_goodbye()
                sys.exit(0)
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
    status_bar = f"{CYAN}┌── SYSTEM SESSION ACTIVE ───────────────────────────────────────────────────┐\n│ DEVICE: {WHITE}{port:<22}{CYAN} │ SPEED: {YELLOW}{baud:<7} bps{CYAN} │ MODE: {GREEN}8N1 RAW{CYAN} │\n│ CONTROLS: {RED}[Ctrl+C]{CYAN} Exit  │ {YELLOW}[Ctrl+R]{CYAN} Change Baudrate / Return to Menu         │\n└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n"
    print(status_bar)
    sys.stdout.write(f"{DIM}[SYS] Line ready. Press ENTER to wake target CLI prompt...{RESET}\n\n")
    sys.stdout.flush()

    action = 'QUIT'

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
                    elif ch == b'\x12': # Ctrl+R
                        action = 'RESTART'
                        break
                    ser.write(ch)

                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    if data:
                        has_received_data = True
                        last_recv_time = time.time()
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()

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
            ser.close()
            print(f"\n{CYAN}───────────────────────────────────────────────────────────────────────────────{RESET}")
            print(f"  {GREEN}[SYS] UwawConnect session ended for {port}.{RESET}")
            print(f"{CYAN}───────────────────────────────────────────────────────────────────────────────{RESET}\n")

    else:
        # POSIX (macOS & Linux)
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
                    elif ch == '\x12':  # Ctrl+R
                        action = 'RESTART'
                        break
                    ser.write(ch.encode('utf-8', errors='ignore'))

                if ser in rlist:
                    data = ser.read(2048)
                    if data:
                        has_received_data = True
                        last_recv_time = time.time()
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()

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
            ser.close()
            print(f"\n{CYAN}───────────────────────────────────────────────────────────────────────────────{RESET}")
            print(f"  {GREEN}[SYS] UwawConnect session ended for {port}.{RESET}")
            print(f"{CYAN}───────────────────────────────────────────────────────────────────────────────{RESET}\n")

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
