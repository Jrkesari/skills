#!/usr/bin/env python3
"""Find an Android TV on the network, connect to it over Wi-Fi ADB and drive it.

Usage:
  python tvadb.py find [--scan]        list Android/Google TVs on this network
  python tvadb.py connect IP           connect; waits while the TV shows "Allow USB debugging?"
  python tvadb.py shell IP 'COMMAND'   run one shell command on the TV (reconnects on Wi-Fi drops)
  python tvadb.py screen IP            print the text, switches and bounds the TV is showing
  python tvadb.py update-check IP      open the system-update screen and print what it says
  python tvadb.py reboot IP            restart the TV and wait until it has finished booting
  python tvadb.py disconnect IP

Standard library only. Commands go to adb as an argument list, so no local shell
(PowerShell, cmd, bash) can rewrite their quotes.
"""
import concurrent.futures
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ADB_PORT = 5555      # Android's default port for ADB over the network
CAST_PORT = 8008     # Google Cast's local HTTP port; every Google TV and Android TV with Cast answers on it
UI_DUMP = "/data/local/tmp/fatl_ui.xml"  # the shell user's scratch folder; removed after each read


def find_adb():
    """Path to adb: $ADB, PATH, then the usual Android SDK locations."""
    if os.environ.get("ADB") and os.path.isfile(os.environ["ADB"]):
        return os.environ["ADB"]
    found = shutil.which("adb")
    if found:
        return found
    exe = "adb.exe" if os.name == "nt" else "adb"
    roots = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk"),
             os.path.expanduser("~/Library/Android/sdk"), os.path.expanduser("~/Android/Sdk")]
    for root in filter(None, roots):
        path = os.path.join(root, "platform-tools", exe)
        if os.path.isfile(path):
            return path
    sys.exit("adb not found. Install Android SDK Platform-Tools "
             "(https://developer.android.com/tools/releases/platform-tools), "
             "then set ADB to the adb path or put it on PATH.")


ADB = None


def adb(*args, timeout=120):
    """Run adb with an argument list; returns (exit code, stdout + stderr)."""
    global ADB
    ADB = ADB or find_adb()
    try:
        r = subprocess.run([ADB, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"adb {' '.join(args[:3])} timed out after {timeout}s"


def target(ip):
    return ip if ":" in ip else f"{ip}:{ADB_PORT}"


def state(t):
    """'device', 'unauthorized', 'offline' or None, as `adb devices` reports it."""
    _, out = adb("devices", timeout=15)
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == t:
            return parts[1]
    return None


def connect(ip, wait_auth=120, quiet=False):
    """Connect, reconnecting after a drop; waits up to wait_auth s for the on-screen approval."""
    t = target(ip)
    deadline = time.time() + wait_auth
    told = False
    while True:
        s = state(t)
        if s == "device":
            return t
        if s == "unauthorized" and not told and not quiet:
            print("The TV is asking 'Allow USB debugging?'. Tick 'Always allow from this computer' and press OK.")
            told = True
        if s in (None, "offline"):
            adb("disconnect", t, timeout=15)
            adb("connect", t, timeout=20)
        if time.time() > deadline:
            sys.exit(f"Could not connect to {t} (state: {state(t) or 'not reachable'}). "
                     "Check the TV is on, on the same network, and USB debugging is on.")
        time.sleep(3)


def shell(ip, command, timeout=180, retries=3):
    """Run one shell command on the TV; a dropped Wi-Fi connection is reconnected and retried."""
    t = target(ip)
    out = ""
    for attempt in range(retries):
        connect(ip, wait_auth=60 if attempt else 120, quiet=bool(attempt))
        code, out = adb("-s", t, "shell", command, timeout=timeout)
        # adb's own transport errors, never the remote command's output
        dropped = code != 0 and any(line.startswith(("error:", "adb: ", "adb.exe: "))
                                    for line in out.splitlines()[:3])
        if not dropped:
            return out
        time.sleep(5)
    return out


def probe(ip, port, timeout=1.0):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def cast_name(ip):
    """The name a Google Cast device gives itself, or ''."""
    url = f"http://{ip}:{CAST_PORT}/setup/eureka_info?params=name,device_info"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.load(r).get("name", "")
    except Exception:
        return ""


def local_ipv4():
    """This computer's address on the LAN (a UDP connect sends nothing)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.0.2.1", 9))
        return s.getsockname()[0]


def neighbours():
    """IPv4 addresses in the OS neighbour (ARP) table."""
    cmds = [["arp", "-a"]] if os.name == "nt" else [["ip", "neigh"], ["arp", "-an"]]
    seen = set()
    for cmd in cmds:
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.TimeoutExpired):
            continue
        for token in out.split():
            try:
                addr = ipaddress.IPv4Address(token.strip("()"))
            except ValueError:
                continue
            if addr.is_private and not str(addr).endswith((".255", ".0")):
                seen.add(str(addr))
    return seen


def cmd_find(scan):
    me = local_ipv4()
    net = ipaddress.IPv4Network(f"{me}/24", strict=False)
    hosts = {str(h) for h in net.hosts()} if scan else {a for a in neighbours() if ipaddress.IPv4Address(a) in net}
    hosts.discard(me)
    print(f"This computer: {me}. Checking {len(hosts)} address(es) on {net}{'' if scan else ' from the ARP table'}...")

    def check(ip):
        adb_open, cast_open = probe(ip, ADB_PORT), probe(ip, CAST_PORT)
        return ip, adb_open, cast_open, cast_name(ip) if cast_open else ""

    with concurrent.futures.ThreadPoolExecutor(64) as pool:
        rows = [r for r in pool.map(check, sorted(hosts, key=ipaddress.IPv4Address)) if r[1] or r[2]]
    if not rows:
        print("No Android TV found." + ("" if scan else " Try again with --scan, or read the IP from the TV's network settings."))
        return
    for ip, adb_open, cast_open, name in rows:
        print(f"{ip:15}  adb {'OPEN' if adb_open else 'closed'}  cast {'yes' if cast_open else 'no '}  {name}")
    print("'adb closed' is an Android TV with USB debugging off (see references/connection.md), "
          "or a TV that is not Android at all (LG webOS and Samsung Tizen also answer Cast and have no ADB).")


def screen_nodes(ip):
    """Visible UI nodes as dicts: text, desc, cls, checkable, checked, focused, bounds."""
    xml = shell(ip, f"uiautomator dump {UI_DUMP} >/dev/null 2>&1; cat {UI_DUMP}; rm -f {UI_DUMP}")
    start = xml.find("<?xml")
    if start < 0:
        return []
    root = ET.fromstring(xml[start:xml.rfind(">") + 1])
    nodes = []
    for n in root.iter("node"):
        a = n.attrib
        if a.get("text") or a.get("content-desc") or a.get("checkable") == "true":
            nodes.append({"text": a.get("text", ""), "desc": a.get("content-desc", ""),
                          "cls": a.get("class", "").rsplit(".", 1)[-1], "checkable": a.get("checkable") == "true",
                          "checked": a.get("checked") == "true", "focused": a.get("focused") == "true",
                          "bounds": a.get("bounds", "")})
    return nodes


def cmd_screen(ip):
    top = shell(ip, "dumpsys activity activities | grep -m1 topResumedActivity").strip()
    print(top or "(no resumed activity)")
    for n in screen_nodes(ip):
        flags = "".join([" [switch on]" if n["checkable"] and n["checked"] else
                         " [switch off]" if n["checkable"] else "", " [focused]" if n["focused"] else ""])
        label = n["text"] or n["desc"] or f"<{n['cls']}>"
        print(f"{label[:110]!s:112}{n['bounds']}{flags}")


def cmd_update_check(ip):
    shell(ip, "am start -a android.settings.SYSTEM_UPDATE_SETTINGS")
    time.sleep(10)  # the update screen fetches its status from the network before showing it
    cmd_screen(ip)
    shell(ip, "input keyevent KEYCODE_HOME")


def cmd_reboot(ip, timeout=360):
    t = connect(ip)
    adb("-s", t, "reboot", timeout=30)
    print("Restarting the TV...")
    time.sleep(20)  # the TV drops off the network within a few seconds and boots in ~25-60s
    deadline = time.time() + timeout
    while time.time() < deadline:
        adb("disconnect", t, timeout=15)
        adb("connect", t, timeout=20)
        if state(t) == "device":
            _, done = adb("-s", t, "shell", "getprop sys.boot_completed", timeout=20)
            if done.strip() == "1":
                print(shell(ip, "uptime; getprop persist.sys.boot.reason.history | head -2").strip())
                return
        time.sleep(5)
    sys.exit("The TV did not finish booting within the wait. Ask whether its screen is on; "
             "if it is in standby, press power on the remote.")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, rest = argv[1], argv[2:]
    if cmd == "find":
        cmd_find("--scan" in rest)
    elif cmd == "connect" and rest:
        print(f"Connected to {connect(rest[0])}")
    elif cmd == "shell" and len(rest) >= 2:
        print(shell(rest[0], " ".join(rest[1:])), end="")
    elif cmd == "screen" and rest:
        cmd_screen(rest[0])
    elif cmd == "update-check" and rest:
        cmd_update_check(rest[0])
    elif cmd == "reboot" and rest:
        cmd_reboot(rest[0])
    elif cmd == "disconnect" and rest:
        print(adb("disconnect", target(rest[0]))[1].strip())
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv)
