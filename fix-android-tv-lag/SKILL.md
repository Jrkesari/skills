---
name: fix-android-tv-lag
description: Diagnoses and fixes a slow, laggy, freezing or randomly restarting Android TV or Google TV (Sony BRAVIA, TCL, Hisense, Philips, Xiaomi, Chromecast with Google TV, Android TV boxes) from the user's computer over Wi-Fi ADB. Reads why the TV restarted (kernel panic, power loss, watchdog), memory pressure and low-memory app kills, storage, disk-check and verified-boot results; then removes never-used apps, switches off features the user does not need, optimises apps and verifies after a restart, logging every change with its undo. Use whenever someone says their TV is slow, hangs, lags, keeps restarting or crashing, asks to speed up, clean up or debloat a smart TV, remove bloatware, preinstalled apps or home-screen ads, free TV memory, or check whether the TV is corrupted, even if they never mention ADB. Not for Samsung (Tizen) or LG (webOS) TVs, which have no ADB.
license: MIT
compatibility: Needs Python 3.8+ and Android SDK Platform-Tools (adb) on a computer on the same network as the TV, and USB debugging turned on in the TV's developer options. Tested on a Sony BRAVIA Google TV (Android 14).
---

# Fix Android TV lag

Works on the user's TV from their computer over Wi-Fi ADB: a read-only diagnosis first, then a cleanup limited to what the data and the user justify, every change logged with its undo, a restart, and a check that the changes held and helped.

Scripts (Python standard library, run from this skill's folder; details in [scripts/README.md](scripts/README.md)):

| Script | Does |
|---|---|
| `scripts/tvadb.py` | find the TV, connect, run a command, read the screen, check for updates, restart and wait |
| `scripts/diagnose.py` | read-only report: restarts, lag, damage, storage, apps; `--compare` against an earlier one |
| `scripts/apply_plan.py` | check, apply, verify and undo a cleanup plan; refuses protected packages |

Read when needed: [references/connection.md](references/connection.md) (getting connected, Windows quoting, drops), [references/diagnosis.md](references/diagnosis.md) (what each signal means), [references/cleanup-catalog.md](references/cleanup-catalog.md) (what is safe to remove, what to ask, what never to touch, ads).

## Ground rules

1. **Diagnose before changing anything.** The TV keeps only a handful of crash records, and a restart you cause can push the evidence out, so the first full report comes before any change.
2. **The user decides about features.** Anything they might use (voice search, casting, AirPlay, ambient mode, an app they have opened) is asked about with AskUserQuestion, giving the memory each one frees and what stops working. Apps never opened and demo or promotion apps can go straight into the plan, but show the whole plan before applying it.
3. **Every change goes through `apply_plan.py`.** It refuses protected and unreviewed TV-maker packages and logs each change with its undo; a hand-typed `pm` command has neither guard.
4. **Say so before every restart.** The screen goes dark for up to a minute and people assume it broke.
5. **Don't fight the TV.** If a change is undone at boot (the maker or Google Play services turns a package back on), leave it and tell the user; forcing it again is how a working TV becomes an unstable one.
6. **Be straight about crashes.** A kernel panic or an unexplained power-on is firmware, hardware or mains power. Freeing memory removes pressure that can set one off; it is not a promise of no more crashes.
7. **Keep personal details out.** Settings screens show account names and emails, and Wi-Fi details identify a home. Don't repeat them in chat or save them anywhere; reports stay on the user's computer.
8. **Finish clean.** Disconnect and ask the user to turn USB debugging off.

## Workflow

Copy this checklist and keep it updated:

```
- [ ] 1 Connect
- [ ] 2 Diagnose and report (read-only)
- [ ] 3 Plan with the user
- [ ] 4 Dry run, then apply
- [ ] 5 Restart and verify the changes held
- [ ] 6 Compare at the same uptime
- [ ] 7 Hand back
```

### 1. Connect

```bash
python scripts/tvadb.py find          # TVs in this computer's ARP table; add --scan to probe the whole /24
python scripts/tvadb.py connect TV-IP # waits while the TV asks "Allow USB debugging?"
```

If the TV shows `adb closed`, give the user the exact remote-control steps from [references/connection.md](references/connection.md) (developer options, then USB debugging) and wait for them. On Windows, run one-off adb commands through these scripts or Git Bash: PowerShell 5.1 strips the double quotes inside native arguments, so a quoted `grep` pattern silently becomes a pipe on the PC.

### 2. Diagnose and report

```bash
python scripts/diagnose.py TV-IP      # prints the summary, saves diag-<time>.json: this is the baseline
python scripts/tvadb.py update-check TV-IP   # optional: reads the system-update screen
```

Interpret it with [references/diagnosis.md](references/diagnosis.md), then tell the user in plain words:

- **Restarts:** each one with its time and cause. For every `cold` power-on, ask whether the power went off or the TV was unplugged then; if not, it is a power fault. Ask whether the red standby light blinks in a pattern.
- **Lag:** memory available, how much is swapped out, how many apps the TV had to close for memory (since boot and by day), frozen apps, the biggest memory users.
- **Damage check:** verified boot, and the last disk check if one is recorded.
- **What is fine:** storage, software version, Wi-Fi signal.

### 3. Plan with the user

From the report's app table and memory list, sort candidates with [references/cleanup-catalog.md](references/cleanup-catalog.md):

- **Straight into the plan:** apps never opened (`last opened: never`, not protected), demo, promotion and recommendation apps marked `safe`, `compile-apps` when many apps show `verify`, animation scales to `0.5`.
- **Ask first** (one AskUserQuestion, multi-select, MB and what stops working in each option): features marked `ask` (AirPlay, ambient mode, casting, voice search, smart-speaker control), apps opened rarely, keeping streaming apps from running in the background.
- **Leave out:** `protected`, `skip` (the TV turns them back on) and unreviewed TV-maker packages unless the user agrees after you explain.

Write the plan as `plan.json` in the report's folder; the format is in `apply_plan.py --help`. A screensaver or other setting goes in as a `setting` action so that it is logged and undoable.

### 4. Dry run, then apply

```bash
python scripts/apply_plan.py PLAN.json           # check only; fix or drop anything REFUSED (--apply runs only a clean plan)
python scripts/apply_plan.py PLAN.json --apply   # appends each change and its undo to changes.jsonl
```

Settings that live in the user's Google account (Autoplay video, Apps-only mode) have no adb setting; they are changed on screen, per the catalog's "Driving settings screens" section.

### 5. Restart and verify

Tell the user the TV is about to restart, then:

```bash
python scripts/tvadb.py reboot TV-IP
python scripts/apply_plan.py --verify CHANGES.jsonl TV-IP
```

A package `PUT BACK` or `TURNED BACK ON by the system` stays that way (rule 5); tell the user. One `still running` after the restart is a persistent app that needs `remove-for-user`.

### 6. Compare at the same uptime

Counts since boot and memory swing hard in the first minutes, so measure at the uptime the baseline was taken at (the summary's first line), with the TV in normal use:

```bash
python scripts/diagnose.py TV-IP --compare BASELINE.json
```

If the TV drops off the network meanwhile, ask whether it was switched off or the power went before reading anything into it; when it is back, the boot history says whether it restarted on its own.

### 7. Hand back

Use this shape, in plain words (package names only if the user wants them):

```markdown
**What was wrong:** <restart causes; why it lagged, with the numbers>
**What I changed:** <removed / switched off / optimised>, all undoable (`apply_plan.py --undo changes.jsonl TV-IP`) except uninstalled apps (Play Store)
**What I left alone and why:** <features kept, things the TV turns back on>
**Before -> after:** <the compare table at matched uptime>
**Keep it healthy:** restart weekly (standby is not a restart), a stabiliser or UPS if the power cuts out, updates on; if it still restarts on its own, the cause is hardware: service
**Turn USB debugging off now:** Settings > System > Developer options
```

Then `python scripts/tvadb.py disconnect TV-IP`.

## Ads on the home screen

Google TV builds its sponsored banners into its own home screen and offers no switch for them. Apps-only mode does not remove them: the TV's own dialog says featured content still shows, and it turns off search and voice. What helps is turning Autoplay video off (stills cost far less than video), and the only full removal is replacing the home screen, which loses Google TV's tabs and profiles. Explain this and let the user choose; details in the catalog.

## When something goes wrong

| Symptom | Do |
|---|---|
| `unauthorized` | The TV is showing "Allow USB debugging?"; ask the user to accept it with "Always allow" ticked |
| `error: closed`, `offline` mid-run | Wi-Fi blip: the scripts reconnect. Check `uptime` before concluding the TV restarted |
| No ping, no port 8008 | The TV is off, in standby or without power: ask the user |
| A disabled app still runs after a restart | It is persistent: `remove-for-user`, restart again |
| `REFUSED` in a dry run | Protected, re-enabled by the TV, or an unreviewed maker package: leave it, or ask and set `vendor_ok` |
| A tap does nothing on a dialog | Dialog buttons can ignore taps: read the screen, cancel with `KEYCODE_BACK`, never press OK blind |
