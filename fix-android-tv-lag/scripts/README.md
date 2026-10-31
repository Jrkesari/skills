# Scripts

Python 3.8+ standard library only, plus `adb` from Android SDK Platform-Tools. Run them from the skill folder. Every command reaches adb as an argument list, so PowerShell, cmd and bash cannot rewrite its quotes.

## tvadb.py: connect and drive the TV

```bash
python scripts/tvadb.py find [--scan]          # Android/Google TVs on this network: ADB port open?, Cast name
python scripts/tvadb.py connect TV-IP          # connects; waits while the TV asks "Allow USB debugging?"
python scripts/tvadb.py shell TV-IP 'COMMAND'  # one shell command; reconnects and retries after a Wi-Fi drop
python scripts/tvadb.py screen TV-IP           # the text, switches and bounds on screen (uiautomator)
python scripts/tvadb.py update-check TV-IP     # opens the system-update screen, prints it, goes home
python scripts/tvadb.py reboot TV-IP           # restarts and waits for sys.boot_completed
python scripts/tvadb.py disconnect TV-IP
```

adb is found in `$ADB`, on `PATH`, in `$ANDROID_HOME` / `$ANDROID_SDK_ROOT`, or in the default Android SDK folders on Windows, macOS and Linux. `screen` writes one temporary file to `/data/local/tmp` on the TV and deletes it straight after.

## diagnose.py: read-only report

```bash
python scripts/diagnose.py TV-IP [--out DIR] [--compare EARLIER.json]
```

Prints a summary and saves `diag-<time>.json` in `~/.fix-android-tv-lag/<model>/` (or `--out`). It covers device and build, uptime, boot history with each restart's cause, crash records and the last kernel log, memory and swap, memory-reclaim CPU, app kills, frozen apps and low-memory kills by day, verified boot and the last disk check, storage, Wi-Fi signal (never the network name or MAC addresses), heat sensors, relevant settings, app compilation, the biggest memory users, and every launcher or user-installed app with when it was last opened. `--compare` adds a before/after table and warns when the two uptimes are too far apart to compare.

It changes nothing on the TV.

## apply_plan.py: change, verify, undo

```bash
python scripts/apply_plan.py PLAN.json                  # dry run: checks each action, changes nothing
python scripts/apply_plan.py PLAN.json --apply          # runs it, logging each change and its undo to changes.jsonl
python scripts/apply_plan.py --verify CHANGES.jsonl TV-IP   # after a restart: which changes held
python scripts/apply_plan.py --undo CHANGES.jsonl TV-IP     # reverts everything, newest first
```

Actions: `uninstall` (user-installed apps), `remove-for-user` (system apps, persistent ones included), `disable`, `restrict-background`, `setting`, `compile-apps`. The plan format is in `--help`. It refuses protected packages, packages the TV is known to turn back on, and TV-maker packages nobody has reviewed unless the action carries `"vendor_ok": true`.

## packages.py

The protected lists and the reviewed packages with their verdicts (`safe`, `ask`, `skip`, `never`) and where each was seen. Add a package here once it has been checked on a real TV.
