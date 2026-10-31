#!/usr/bin/env python3
"""Check, apply, verify and undo a cleanup plan on an Android TV. Every change is logged with its undo.

Usage:
  python apply_plan.py PLAN.json                  check the plan (dry run): nothing changes
  python apply_plan.py PLAN.json --apply          apply it; each change is appended to changes.jsonl beside the plan
  python apply_plan.py --verify CHANGES.jsonl IP  after a restart: which changes held, which the TV undid
  python apply_plan.py --undo CHANGES.jsonl IP    put every change back, newest first

Plan (JSON):
  {"tv": "TV-IP", "actions": [
    {"do": "uninstall", "package": "PKG", "why": "..."},            a user-installed app (reinstall from Play Store)
    {"do": "remove-for-user", "package": "PKG", "why": "..."},      a system app, incl. persistent ones; undo restores it
    {"do": "disable", "package": "PKG", "why": "..."},              a system app; undo re-enables it
    {"do": "restrict-background", "package": "PKG", "why": "..."},  the app runs only while it is open
    {"do": "setting", "namespace": "secure|global|system", "key": "K", "value": "V", "why": "..."},
    {"do": "compile-apps", "why": "..."}                            the TV's overnight app optimisation, now
  ]}
An unreviewed TV-maker package (see packages.py) also needs "vendor_ok": true, set only after the user agreed.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packages import REVIEWED, is_protected, is_unreviewed_vendor  # noqa: E402
from tvadb import connect, shell  # noqa: E402

PACKAGE_ACTIONS = ("uninstall", "remove-for-user", "disable", "restrict-background")
OP = "RUN_ANY_IN_BACKGROUND"


def pkg_state(ip, pkg):
    out = shell(ip, f"dumpsys package {pkg} | grep -e pkgFlags= -e 'User 0:'")
    flags = next((line for line in out.splitlines() if "pkgFlags=" in line), "")
    user0 = next((line for line in out.splitlines() if "installed=" in line), "")
    if not flags:
        return None
    enabled = next((t.split("=")[1] for t in user0.split() if t.startswith("enabled=")), "0")
    return {"system": " SYSTEM " in flags.replace("[", " ").replace("]", " "),
            "persistent": "PERSISTENT" in flags,
            "installed": "installed=true" in user0, "enabled": int(enabled) if enabled.isdigit() else 0,
            "running": bool(shell(ip, f"pidof {pkg}").strip())}


def appops_mode(ip, pkg):
    out = shell(ip, f"cmd appops get {pkg} {OP}")
    return out.split(":", 1)[1].split(";")[0].strip() if f"{OP}:" in out else "default"


def check(ip, a):
    """(problem or None, warning or None, state before)."""
    do = a.get("do")
    if do == "compile-apps":
        return None, "takes a few minutes and keeps the TV busy meanwhile", None
    if do == "setting":
        if a.get("namespace") not in ("secure", "global", "system") or not a.get("key") or "value" not in a:
            return "a setting needs namespace (secure|global|system), key and value", None, None
        return None, None, shell(ip, f"settings get {a['namespace']} {a['key']}").strip()
    if do not in PACKAGE_ACTIONS:
        return f"unknown action '{do}'", None, None
    pkg = a.get("package", "")
    verdict, note, _ = REVIEWED.get(pkg, ("", "", ""))
    if is_protected(pkg):
        return f"{pkg} is protected ({note or 'core system or TV-maker service'}); leave it", None, None
    if verdict == "skip":
        return f"{pkg}: {note}. Leave it", None, None
    if is_unreviewed_vendor(pkg) and not a.get("vendor_ok"):
        return f"{pkg} is an unreviewed TV-maker package; ask the user, then add \"vendor_ok\": true", None, None
    st = pkg_state(ip, pkg)
    if not st or not st["installed"]:
        return f"{pkg} is not installed on this TV", None, st
    if do == "uninstall" and st["system"]:
        return f"{pkg} is a system app: use disable or remove-for-user", None, st
    if do == "restrict-background":
        st["appops"] = appops_mode(ip, pkg)
    warn = None
    if do == "disable" and st["persistent"]:
        warn = "persistent: disable leaves it running even after a restart; use remove-for-user"
    elif do == "uninstall":
        warn = "deletes the app and its data; only the Play Store can bring it back"
    return None, warn, st


def run(ip, a, before):
    """Apply one action; returns (ok, output, undo command or None)."""
    do, pkg = a["do"], a.get("package", "")
    if do == "uninstall":
        cmd, undo = f"pm uninstall {pkg}", None
    elif do == "remove-for-user":
        cmd, undo = f"pm uninstall --user 0 {pkg}; am force-stop {pkg}", f"cmd package install-existing {pkg}"
    elif do == "disable":
        cmd, undo = f"pm disable-user --user 0 {pkg}; am force-stop {pkg}", f"pm enable --user 0 {pkg}"
    elif do == "restrict-background":
        cmd = f"cmd appops set {pkg} {OP} ignore; am force-stop {pkg}"
        undo = f"cmd appops set {pkg} {OP} {before.get('appops', 'default')}"
    elif do == "setting":
        ns, key = a["namespace"], a["key"]
        cmd = f"settings put {ns} {key} {a['value']}"
        undo = f"settings delete {ns} {key}" if before in ("", "null") else f"settings put {ns} {key} {before}"
    else:
        cmd, undo = "pm bg-dexopt-job", None
    out = shell(ip, cmd, timeout=900).strip()
    ok = "Failure" not in out and "Exception" not in out and "Error" not in out
    return ok, out, undo


def held(ip, e):
    """Whether a logged change still holds, in words."""
    do, pkg = e["do"], e.get("package", "")
    if do == "setting":
        now = shell(ip, f"settings get {e['namespace']} {e['key']}").strip()
        return now == str(e["value"]), f"value now {now}"
    if do == "compile-apps":
        return True, "done"
    st = pkg_state(ip, pkg)
    if do == "uninstall":
        return st is None, "gone" if st is None else "installed again"
    if not st:
        return True, "gone"
    running = ", still running (restart the TV)" if st["running"] else ""
    if do == "remove-for-user":
        return not st["installed"], ("removed" if not st["installed"] else "PUT BACK by the system") + running
    if do == "disable":
        return st["enabled"] in (2, 3), ("disabled" if st["enabled"] in (2, 3) else "TURNED BACK ON by the system") + running
    mode = appops_mode(ip, pkg)
    return mode == "ignore", f"background mode {mode}"


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return
    if argv[1] in ("--verify", "--undo"):
        log, ip = argv[2], argv[3]
        with open(log, encoding="utf-8") as fh:
            entries = [json.loads(line) for line in fh if line.strip()]
        applied = [e for e in entries if e.get("ok") and e.get("phase") == "apply"]
        connect(ip)
        if argv[1] == "--verify":
            for e in applied:
                ok, words = held(ip, e)
                print(f"{'held ' if ok else 'UNDONE'}  {e['do']:19} {e.get('package') or e.get('key', '')}: {words}")
            return
        with open(log, "a", encoding="utf-8") as fh:
            for e in reversed(applied):
                if not e.get("undo"):
                    print(f"cannot undo {e['do']} {e.get('package', '')}: {'reinstall it from the Play Store' if e['do'] == 'uninstall' else 'nothing to undo'}")
                    continue
                out = shell(ip, e["undo"]).strip()
                print(f"undo {e['undo']}: {out or 'ok'}")
                fh.write(json.dumps({"phase": "undo", "time": now(), "cmd": e["undo"], "out": out}) + "\n")
        return

    plan_path = argv[1]
    with open(plan_path, encoding="utf-8") as fh:
        plan = json.load(fh)
    ip, apply = plan["tv"], "--apply" in argv
    connect(ip)
    checked, problems = [], 0
    for a in plan["actions"]:
        problem, warn, before = check(ip, a)
        label = f"{a['do']:19} {a.get('package') or a.get('key', '')}"
        if problem:
            problems += 1
            print(f"REFUSED  {label}: {problem}")
        else:
            print(f"ok       {label}{'  (warning: ' + warn + ')' if warn else ''}")
            checked.append((a, before))
    if not apply:
        print(f"\nDry run: {len(checked)} action(s) would run, {problems} refused. Add --apply to run them.")
        return
    if problems:  # what runs must be exactly the plan the user saw
        sys.exit(f"\n{problems} action(s) refused: remove or fix them in the plan, then apply again. Nothing changed.")
    log = os.path.join(os.path.dirname(os.path.abspath(plan_path)), "changes.jsonl")
    model = shell(ip, "getprop ro.product.model").strip()
    with open(log, "a", encoding="utf-8") as fh:
        for a, before in checked:
            ok, out, undo = run(ip, a, before)
            print(f"{'done ' if ok else 'FAILED'}  {a['do']:19} {a.get('package') or a.get('key', '')}: {out[-160:]}")
            fh.write(json.dumps({"phase": "apply", "time": now(), "model": model, **a, "before": before,
                                 "ok": ok, "out": out[-400:], "undo": undo}) + "\n")
    print(f"\nLogged to {log}. Restart the TV (tell the user first), then run --verify.")


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    main(sys.argv)
