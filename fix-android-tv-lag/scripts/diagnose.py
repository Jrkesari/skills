#!/usr/bin/env python3
"""Read-only health check of an Android TV over ADB: why it restarted, why it lags, whether anything is damaged.

Usage:
  python diagnose.py IP [--out DIR] [--compare BASELINE.json]

Writes DIR/diag-<time>.json (default DIR: ~/.fix-android-tv-lag/<model>/) and prints a summary.
With --compare, also prints the change against an earlier report. Changes nothing on the TV.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packages import REVIEWED, is_protected, is_unreviewed_vendor  # noqa: E402
from tvadb import connect, shell  # noqa: E402

SETTINGS = [("secure", k) for k in ("screensaver_enabled", "screensaver_activate_on_sleep",
                                    "screensaver_activate_on_dock", "screensaver_components")] + \
           [("global", k) for k in ("window_animation_scale", "transition_animation_scale",
                                    "animator_duration_scale", "hdmi_control_enabled", "stay_on_while_plugged_in")]
PROPS = ["ro.product.manufacturer", "ro.product.model", "ro.product.device", "ro.build.version.release",
         "ro.build.display.id", "ro.build.date", "ro.build.version.security_patch", "ro.soc.model",
         "ro.boot.hardware", "persist.sys.timezone", "sys.boot.reason", "sys.boot.reason.last",
         "persist.sys.boot.reason.history", "ro.boot.verifiedbootstate", "ro.boot.veritymode",
         "ro.boot.vbmeta.device_state"]
# Lines in a disk-check log that mean real damage, as opposed to the tidying every unclean shutdown causes.
FSCK_SERIOUS = ("UNEXPECTED INCONSISTENCY", "illegal block", "Unattached inode", "deleted/unused inode",
                "Duplicate or bad block", "Multiply-claimed", "has corrupt", "Bad magic number",
                "I/O error", "short read", "Error reading block")
FSCK_ROUTINE = ("could be shorter", "QUOTA WARNING", "Update quota info", "Free blocks count wrong",
                "Free inodes count wrong", "orphan", "recovering journal")
# e2fsck exit codes (man e2fsck): 0 clean, 1 errors corrected, 2 corrected and reboot needed, 4+ not fixed.
FSCK_EXIT = {"0": "clean", "1": "errors found and corrected", "2": "errors corrected, reboot needed",
             "4": "ERRORS LEFT UNCORRECTED", "8": "fsck could not run", "12": "fsck cancelled"}
KMSG_FLAGS = ("Kernel panic", "Internal error", "Unable to handle kernel", "Oops", "BUG:", "watchdog",
              "Restarting system", "Power down", "thermal")
CRASH_TAGS = ("system_server_crash", "system_server_watchdog", "SYSTEM_TOMBSTONE", "system_app_crash",
              "data_app_crash", "system_app_anr", "data_app_anr", "SYSTEM_LAST_KMSG", "SYSTEM_FSCK")


def batch(ip, parts):
    """Run several small commands in one shell call; returns {name: output}."""
    script = "; ".join(f"echo @@{name}; {cmd}" for name, cmd in parts)
    out, cur = {}, None
    for line in shell(ip, script).splitlines():
        if line.startswith("@@"):
            cur = line[2:].strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def parse_props(text):
    """getprop output to a dict; a value may run over several lines."""
    props, key, buf = {}, None, []
    for line in text.splitlines():
        if key is None and line.startswith("[") and "]: [" in line:
            key, rest = line[1:].split("]: [", 1)
            buf = [rest]
        elif key is not None:
            buf.append(line)
        if key is not None and buf[-1].endswith("]"):
            props[key] = "\n".join(buf)[:-1]
            key = None
    return props


def parse_duration(text):
    """'+18d0h36m40s701ms' to seconds; None for '<uninitialized>'."""
    text = text.lstrip("+-")
    if not text or not text[0].isdigit():
        return None
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001}
    total, num, unit = 0.0, "", ""
    for ch in text + "0":
        if ch.isdigit():
            if unit:
                total += float(num) * units.get(unit, 0)
                num, unit = "", ""
            num += ch
        else:
            unit += ch
    return total


def parse_hms(text):
    """ps TIME '[DD-]HH:MM:SS' to seconds."""
    days, _, hms = text.rpartition("-")
    secs = 0
    for part in hms.split(":"):
        secs = secs * 60 + float(part)
    return secs + (int(days) * 86400 if days else 0)


def kv(line, key):
    """Value of key=value in a space-separated line, or None."""
    for token in line.split():
        if token.startswith(key + "="):
            return token[len(key) + 1:]
    return None


def field(text, label):
    """Value after 'label: ' up to the next comma, or ''."""
    i = text.find(label + ": ")
    return text[i + len(label) + 2:].split(",")[0].strip() if i >= 0 else ""


def boot_history(props, tz_offset):
    """Newest first: [{reason, time, meaning}]."""
    rows = []
    for line in props.get("persist.sys.boot.reason.history", "").splitlines():
        reason, _, epoch = line.strip().rpartition(",")
        if not reason:
            continue
        rows.append({"reason": reason, "time": local_time(int(epoch), tz_offset) if epoch.isdigit() else "?",
                     "meaning": boot_meaning(reason)})
    return rows


def boot_meaning(reason):
    if reason.startswith("kernel_panic"):
        return "CRASH: the kernel crashed and the TV restarted itself"
    if reason.startswith("watchdog"):
        return "HANG: the system froze and a watchdog restarted it"
    if reason.startswith("cold"):
        return "power-on from no power: unplugged, a power cut, or a power fault. Ask the user"
    if reason.startswith("hard"):
        return "hardware reset"
    if reason.startswith(("reboot", "shutdown", "recovery", "bootloader")):
        return "requested restart (" + reason + ")"
    return "unknown: " + reason


def local_time(epoch, tz_offset):
    if epoch < 1600000000:  # before Sept 2020: the TV's clock was not set yet when it booted
        return "time unknown (clock not set at boot)"
    tz = datetime.timezone(datetime.timedelta(minutes=tz_offset))
    return datetime.datetime.fromtimestamp(epoch, tz).strftime("%Y-%m-%d %H:%M")


def parse_offset(text):
    """'+0530' to minutes."""
    text = text.strip()
    if len(text) != 5 or text[0] not in "+-":
        return 0
    minutes = int(text[1:3]) * 60 + int(text[3:])
    return -minutes if text[0] == "-" else minutes


def parse_meminfo(text):
    mem = {}
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        if rest.strip().split()[:1] and rest.split()[0].isdigit():
            mem[name.strip()] = int(rest.split()[0])
    return mem


def parse_rss(text):
    """dumpsys meminfo 'Total RSS/PSS by process' section to [(kB, process)]."""
    rows, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("Total RSS by process", "Total PSS by process")):
            inside = True
            continue
        if inside:
            if not s or s.startswith("Total "):
                break
            size, _, rest = s.partition(":")
            if size.endswith("K") and size[:-1].replace(",", "").isdigit():
                rows.append((int(size[:-1].replace(",", "")), rest.strip().split(" (pid")[0]))
    return rows


def parse_exit_info(text):
    """[(date, process, reason)] from dumpsys activity exit-info."""
    rows, date = [], ""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("timestamp="):
            date = s.split()[0][len("timestamp="):]
        elif s.startswith("process="):
            proc = s.split()[0][len("process="):]
            i = s.find(" reason=")
            reason = s[s.find("(", i) + 1:s.find(")", i)] if i >= 0 else "?"
            rows.append((date, proc, reason))
    return rows


def parse_dexopt(text):
    status, pkg = {}, None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]") and "." in s:
            pkg = s[1:-1]
        elif pkg and "status=" in s and pkg not in status:
            status[pkg] = s.split("status=", 1)[1].split("]")[0]
    return status


def parse_fsck(text):
    lines = text.splitlines()
    exit_code = ""
    for line in lines:
        if "exit(" in line:
            exit_code = line.split("exit(", 1)[1].split(")")[0]
    return {"exit": exit_code, "verdict": FSCK_EXIT.get(exit_code, "no exit code in the log"),
            "modified": any("FILE SYSTEM WAS MODIFIED" in line for line in lines),
            "serious": [line.strip() for line in lines if any(m in line for m in FSCK_SERIOUS)][:20],
            "routine": sorted({m for line in lines for m in FSCK_ROUTINE if m in line})}


def pkg_list(text):
    return {line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("package:")}


def collect(ip):
    connect(ip)
    settings_cmd = "; ".join(f"echo {ns} {k}=$(settings get {ns} {k})" for ns, k in SETTINGS)
    b = batch(ip, [
        ("props", "getprop"), ("uptime", "cat /proc/uptime"), ("offset", "date +%z"), ("now", "date +%s"),
        ("meminfo", "cat /proc/meminfo"), ("kswapd", "ps -A -o TIME,NAME | grep kswapd"),
        ("top", "top -b -n 1 | grep -m1 idle"), ("df", "df -h /data"),
        ("diskstats", "dumpsys diskstats | head -12"), ("mount", "mount | grep ' /data '"),
        ("dropbox", "dumpsys dropbox | grep -E '^[0-9]{4}-'"), ("settings", settings_cmd),
        ("thermal", "for z in /sys/class/thermal/thermal_zone*; do echo \"$(cat $z/type 2>/dev/null) $(cat $z/temp 2>/dev/null)\"; done"),
        ("wifi", "dumpsys wifi | grep -m1 mWifiInfo"),
        ("fg", "dumpsys activity activities | grep -m1 topResumedActivity"),
        ("power", "dumpsys power | grep -m1 mWakefulness="),
        ("launcher", "cmd package query-activities --brief -a android.intent.action.MAIN -c android.intent.category.LEANBACK_LAUNCHER"),
        ("user_pkgs", "pm list packages -3"), ("system_pkgs", "pm list packages -s"), ("disabled_pkgs", "pm list packages -d"),
        ("kills", "logcat -b events -d | grep -c -e am_kill -e killinfo"),
        ("anrs", "logcat -b events -d | grep -c am_anr"), ("fatals", "logcat -b crash -d | grep -c FATAL"),
        ("fsck", "dumpsys dropbox --print SYSTEM_FSCK | tail -60"),
        ("kmsg", "dumpsys dropbox --print SYSTEM_LAST_KMSG | tail -80"),
        ("anr_detail", "dumpsys dropbox --print system_app_anr | grep -e '^Process:' -e 'avg10' | head -12"),
    ])
    big = {name: shell(ip, cmd, timeout=240) for name, cmd in [
        ("meminfo_rss", "dumpsys meminfo"),
        ("standby", "dumpsys usagestats | grep usedByUser="),
        ("exit_info", "dumpsys activity exit-info"),
        ("dexopt", "dumpsys package dexopt"),
    ]}
    return b, big


def analyse(b, big):
    props = parse_props(b.get("props", ""))
    offset = parse_offset(b.get("offset", ""))
    uptime_s = float((b.get("uptime") or "0").split()[0])
    mem = parse_meminfo(b.get("meminfo", ""))
    kswapd = parse_hms(b["kswapd"].split()[0]) if b.get("kswapd", "").strip() else None
    top = b.get("top", "")
    idle = next((t for t in top.split() if t.endswith("%idle")), "")
    cpus = next((t for t in top.split() if t.endswith("%cpu")), "")
    rss = parse_rss(big["meminfo_rss"])
    rss_by_pkg = {}
    for kb, proc in rss:
        rss_by_pkg[proc.split(":")[0]] = rss_by_pkg.get(proc.split(":")[0], 0) + kb
    exits = parse_exit_info(big["exit_info"])
    lowmem_by_day, lowmem_by_proc = {}, {}
    for date, proc, reason in exits:
        if reason == "LOW_MEMORY":
            lowmem_by_day[date] = lowmem_by_day.get(date, 0) + 1
            lowmem_by_proc[proc] = lowmem_by_proc.get(proc, 0) + 1
    standby = {}
    for line in big["standby"].splitlines():
        pkg = kv(line, "package")
        if pkg:
            standby[pkg] = {"bucket": kv(line, "bucket"), "used_by_user_s_ago": parse_duration(kv(line, "usedByUser") or "")}
    dexopt = parse_dexopt(big["dexopt"])
    launcher = {line.strip().split("/")[0] for line in b.get("launcher", "").splitlines() if "/" in line}
    user_pkgs, system_pkgs = pkg_list(b.get("user_pkgs", "")), pkg_list(b.get("system_pkgs", ""))
    disabled = pkg_list(b.get("disabled_pkgs", ""))
    apps = []
    for pkg in sorted(launcher | user_pkgs):
        used = standby.get(pkg, {}).get("used_by_user_s_ago")
        apps.append({"package": pkg, "type": "user" if pkg in user_pkgs else "system", "disabled": pkg in disabled,
                     "last_opened_days_ago": None if used is None else round(used / 86400, 1),
                     "running_kb": rss_by_pkg.get(pkg, 0), "dexopt": dexopt.get(pkg, ""),
                     "protected": is_protected(pkg), "unreviewed_vendor": is_unreviewed_vendor(pkg),
                     "reviewed": REVIEWED.get(pkg, ("", "", ""))[:2]})
    background = [{"process": p, "kb": kb, "protected": is_protected(p.split(":")[0]),
                   "reviewed": REVIEWED.get(p.split(":")[0], ("", "", ""))[:2]}
                  for kb, p in rss[:30]]
    wifi = b.get("wifi", "")
    settings = {}
    for line in b.get("settings", "").splitlines():
        ns, _, rest = line.partition(" ")
        k, _, v = rest.partition("=")
        settings[f"{ns}.{k}"] = v
    dex_counts = {}
    for st in dexopt.values():
        dex_counts[st] = dex_counts.get(st, 0) + 1
    return {
        "collected_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "device": {k: props.get(k, "") for k in PROPS[:10]},
        "uptime_min": round(uptime_s / 60, 1),
        "boot": {"current": props.get("sys.boot.reason", ""), "history": boot_history(props, offset)},
        "integrity": {"verified_boot": props.get("ro.boot.verifiedbootstate", ""),
                      "verity": props.get("ro.boot.veritymode", ""),
                      "bootloader": props.get("ro.boot.vbmeta.device_state", ""),
                      "data_mount": "rw" if " (rw," in b.get("mount", "") else b.get("mount", "").strip()[:80],
                      "fsck": parse_fsck(b.get("fsck", "")) if "e2fsck" in b.get("fsck", "") else None},
        "crash_records": {tag: sum(1 for line in b.get("dropbox", "").splitlines() if f" {tag} " in line + " ")
                          for tag in CRASH_TAGS},
        "dropbox": b.get("dropbox", "").splitlines()[-15:],
        "last_kmsg_flags": [line.strip() for line in b.get("kmsg", "").splitlines() if any(f in line for f in KMSG_FLAGS)][-15:],
        "anr_detail": b.get("anr_detail", "").splitlines(),
        "memory": {"total_mb": mem.get("MemTotal", 0) // 1024, "available_mb": mem.get("MemAvailable", 0) // 1024,
                   "swap_used_mb": (mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)) // 1024,
                   "kswapd_cpu_s": kswapd,
                   "kswapd_s_per_min": round(kswapd / (uptime_s / 60), 2) if kswapd is not None and uptime_s > 60 else None,
                   "cpu": f"{idle} of {cpus}".strip()},
        "since_boot": {"app_kills": int(b.get("kills", "0").strip() or 0), "anrs": int(b.get("anrs", "0").strip() or 0),
                       "fatal_crashes": int(b.get("fatals", "0").strip() or 0)},
        "low_memory_kills_by_day": dict(sorted(lowmem_by_day.items())[-14:]),
        "low_memory_victims": sorted(lowmem_by_proc.items(), key=lambda x: -x[1])[:10],
        "storage": {"df": b.get("df", "").strip(), "diskstats": b.get("diskstats", "").strip().splitlines()[2:10]},
        "thermal": [line for line in b.get("thermal", "").splitlines() if line.strip() and not line.startswith(" ")],
        # the network name and MAC addresses are deliberately not kept
        "wifi": {"rssi": field(wifi, "RSSI"), "link_mbps": field(wifi, "Link speed"),
                 "standard": field(wifi, "Wi-Fi standard")},
        "settings": settings,
        "foreground": b.get("fg", "").strip(), "power": b.get("power", "").strip(),
        "dexopt_counts": dex_counts,
        "apps": apps,
        "top_processes": background,
        "disabled_packages": sorted(disabled),
    }


def summary(d):
    m, sb = d["memory"], d["since_boot"]
    dev = d["device"]
    out = [f"# {dev['ro.product.manufacturer']} {dev['ro.product.model']} - Android {dev['ro.build.version.release']}, "
           f"build {dev['ro.build.display.id']} ({dev['ro.build.date']}), patch {dev['ro.build.version.security_patch']}, SoC {dev['ro.soc.model']}",
           f"Up {d['uptime_min']} min. Now: {d['foreground'] or '?'} ({d['power']})", "", "## Restarts (newest first)"]
    out += [f"- {r['time']}: {r['reason']} -> {r['meaning']}" for r in d["boot"]["history"]] or ["- no history recorded"]
    cr = {k: v for k, v in d["crash_records"].items() if v}
    out += [f"Crash records kept by the TV: {cr or 'none'}"]
    if d["last_kmsg_flags"]:
        out += ["Last kernel log before the previous restart:"] + [f"  {line}" for line in d["last_kmsg_flags"]]
    out += ["", "## Lag",
            f"- Memory: {m['available_mb']} MB available of {m['total_mb']} MB, {m['swap_used_mb']} MB swapped out",
            f"- Memory reclaim (kswapd): {m['kswapd_cpu_s']} s CPU, {m['kswapd_s_per_min']} s per minute of uptime",
            f"- CPU idle: {m['cpu']}",
            f"- Since boot: {sb['app_kills']} apps killed, {sb['anrs']} frozen (ANR), {sb['fatal_crashes']} crashed",
            f"- Apps closed for low memory, by day: {d['low_memory_kills_by_day'] or 'none recorded'}"]
    if d["anr_detail"]:
        out += ["- Last frozen app: " + " | ".join(d["anr_detail"][:4])]
    i = d["integrity"]
    out += ["", "## Damage check",
            f"- Verified boot: {i['verified_boot']} (verity {i['verity']}, bootloader {i['bootloader']}); /data mounted {i['data_mount']}"]
    if i["fsck"]:
        f = i["fsck"]
        out += [f"- Last disk check: exit {f['exit']} = {f['verdict']}; routine fixes: {', '.join(f['routine']) or 'none'}; "
                f"serious lines: {len(f['serious'])}"] + [f"    {line}" for line in f["serious"]]
    else:
        out += ["- No disk-check record in the crash store (none was run, or it has rotated out)"]
    out += ["", "## Storage", *[f"  {line}" for line in d["storage"]["df"].splitlines()],
            *[f"  {line.strip()}" for line in d["storage"]["diskstats"]],
            "", f"## Network: Wi-Fi RSSI {d['wifi']['rssi']} dBm, link {d['wifi']['link_mbps']}, standard {d['wifi']['standard']}",
            f"## Thermal: {', '.join(d['thermal']) or 'not exposed on this TV'}",
            f"## Settings: {d['settings']}",
            f"## App compilation (dexopt): {d['dexopt_counts']}", "", "## Biggest memory users now"]
    for p in d["top_processes"][:15]:
        tag = "protected" if p["protected"] else (f"{p['reviewed'][0]}: {p['reviewed'][1]}" if p["reviewed"][0] else "")
        out.append(f"- {p['kb'] // 1024:4} MB  {p['process']}  {tag}")
    out += ["", "## Apps (launcher + user-installed)", "last opened | running | type | dexopt | package | note"]
    for a in sorted(d["apps"], key=lambda a: (a["last_opened_days_ago"] is not None, -(a["last_opened_days_ago"] or 0))):
        last = "never" if a["last_opened_days_ago"] is None else f"{a['last_opened_days_ago']}d ago"
        note = "protected" if a["protected"] else "unreviewed vendor" if a["unreviewed_vendor"] else \
            (f"{a['reviewed'][0]}: {a['reviewed'][1]}" if a["reviewed"][0] else "")
        out.append(f"{last:>11} | {a['running_kb'] // 1024:4} MB | {a['type']:6} | {a['dexopt']:13} | "
                   f"{a['package']}{' (disabled)' if a['disabled'] else ''} | {note}")
    return "\n".join(out)


def compare(old, new):
    rows = [("uptime (min)", old["uptime_min"], new["uptime_min"]),
            ("memory available (MB)", old["memory"]["available_mb"], new["memory"]["available_mb"]),
            ("swapped out (MB)", old["memory"]["swap_used_mb"], new["memory"]["swap_used_mb"]),
            ("kswapd s per min", old["memory"]["kswapd_s_per_min"], new["memory"]["kswapd_s_per_min"]),
            ("apps killed since boot", old["since_boot"]["app_kills"], new["since_boot"]["app_kills"]),
            ("frozen apps since boot", old["since_boot"]["anrs"], new["since_boot"]["anrs"]),
            ("crashes since boot", old["since_boot"]["fatal_crashes"], new["since_boot"]["fatal_crashes"])]
    out = ["## Before -> after", "metric | before | after"] + [f"{a} | {b} | {c}" for a, b, c in rows]
    o, n = old["uptime_min"] or 1, new["uptime_min"] or 1
    if abs(o - n) / max(o, n) > 0.25:
        out.append(f"NOTE: uptimes differ ({o} vs {n} min). Counts since boot and memory are not comparable yet; "
                   f"measure again at about {o} min of uptime.")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    ip = argv[1]
    out_dir = argv[argv.index("--out") + 1] if "--out" in argv else None
    base = argv[argv.index("--compare") + 1] if "--compare" in argv else None
    d = analyse(*collect(ip))
    model = "".join(c if c.isalnum() else "-" for c in d["device"]["ro.product.model"] or "tv")
    out_dir = out_dir or os.path.join(os.path.expanduser("~"), ".fix-android-tv-lag", model)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"diag-{datetime.datetime.now():%Y%m%d-%H%M%S}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    print(summary(d))
    if base:
        with open(base, encoding="utf-8") as fh:
            print("\n" + compare(json.load(fh), d))
    print(f"\nReport saved: {path}")


if __name__ == "__main__":
    main(sys.argv)
