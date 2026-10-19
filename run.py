#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     👑 MEGA AUTOMATION HUB — 3-IN-1 LAUNCHER                     ║
║     Windows & Linux uchun avtomatik bo'sh port tanlovchi         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import socket
import argparse
import subprocess
import webbrowser
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

if sys.platform == "win32":
    os.system("color")


def find_python():
    """Python interpreterini topish."""
    candidates = [
        os.path.join(DIR, "venv", "bin", "python3"),
        os.path.join(DIR, "venv", "bin", "python"),
        "/home/shohjaxon/tg-account-manager/venv/bin/python3",
        "/home/shohjaxon/tg-account-manager/venv/bin/python",
        os.path.join(DIR, "venv", "Scripts", "python.exe"),
        sys.executable,
        "python3",
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c):
            return c
    return sys.executable


def is_port_in_use(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_free_port(preferred=8010, host="127.0.0.1", max_scan=50):
    if not is_port_in_use(preferred, host):
        return preferred, False

    for offset in range(1, max_scan):
        candidate = preferred + offset
        if not is_port_in_use(candidate, host):
            return candidate, True

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1], True


def main():
    parser = argparse.ArgumentParser(description="Mega Automation Hub (3-in-1)")
    parser.add_argument("--port", type=int, default=None, help="Port (default: 8010)")
    parser.add_argument("--no-browser", action="store_true", help="Brauzerni ochmaslik")
    args = parser.parse_args()

    preferred_port = args.port or 8010

    # Port band bo'lsa va allaqachon ishlab turgan bo'lsa
    if is_port_in_use(preferred_port):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{preferred_port}/", timeout=1.2) as resp:
                data = resp.read(300).decode("utf-8", errors="ignore")
                if "MEGA AUTOMATION HUB" in data or "3-in-1" in data:
                    url = f"http://127.0.0.1:{preferred_port}/"
                    print(f"\n{GREEN}[✓] Mega Automation Hub allaqachon ishlab turibdi!{RESET}")
                    print(f"{CYAN}🌐 Web UI: {BOLD}{url}{RESET}\n")
                    if not args.no_browser:
                        webbrowser.open(url)
                    sys.exit(0)
        except Exception:
            pass

    port, was_shifted = find_free_port(preferred_port)
    python_bin = find_python()
    url = f"http://127.0.0.1:{port}/"

    print(f"\n{CYAN}╔══════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}║     👑 MEGA AUTOMATION HUB — 3-IN-1 CONTROL CENTER               ║{RESET}")
    print(f"{CYAN}╚══════════════════════════════════════════════════════════════════╝{RESET}")
    print(f" {DIM}Tizim:{RESET} {sys.platform.upper()} · {DIM}Python:{RESET} {python_bin}")
    if was_shifted:
        print(f" {YELLOW}⚠️  Port {preferred_port} band edi. Yangi bo'sh port tanlandi: {BOLD}{port}{RESET}")
    else:
        print(f" {GREEN}✓  Port: {BOLD}{port}{RESET} {GREEN}(bo'sh va tayyor){RESET}")

    print(f" {CYAN}🌐 Web URL:{RESET}       {BOLD}{url}{RESET}")
    print(f" {DIM}📱 TG Manager:{RESET}    http://127.0.0.1:8009/tgm/")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────{RESET}\n")

    env = dict(os.environ)
    env["PORT"] = str(port)

    cmd = [python_bin, "main.py"]
    kwargs = {"cwd": DIR, "env": env}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(cmd, **kwargs)

    server_ready = False
    for _ in range(30):
        time.sleep(0.5)
        if is_port_in_use(port):
            server_ready = True
            break
        if proc.poll() is not None:
            break

    if not server_ready:
        print(f"{RED}❌ Server ishga tushmadi!{RESET}")
        try:
            proc.kill()
        except Exception:
            pass
        sys.exit(1)

    print(f"{GREEN}✅ Hub muvaffaqiyatli ishlayapti! Brauzer ochilmoqda...{RESET}")
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print(f"\n{DIM}To'xtatish uchun: Ctrl + C bosing.{RESET}\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}To'xtatilmoqda...{RESET}")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print(f"{GREEN}To'xtatildi.{RESET}")


if __name__ == "__main__":
    main()
