# fix-android-tv-lag

A Claude Code skill that finds out why an Android TV or Google TV is slow or keeps restarting, and fixes what can be fixed from your computer, over Wi-Fi. It changes nothing until it has looked, asks before removing anything you might use, logs every change so that it can be undone, and checks afterwards that the changes held and helped.

Works on Android TV and Google TV: Sony BRAVIA, TCL, Hisense, Philips, Xiaomi, Chromecast with Google TV, Android TV boxes. It does **not** work on Samsung (Tizen) or LG (webOS) TVs, which have no ADB.

## What it does

1. **Connects** to the TV over the network. You turn on USB debugging with the remote; the skill tells you exactly where.
2. **Diagnoses, read-only**:
   - why each recent restart happened: a crash (kernel panic), a freeze (watchdog), or power loss
   - why it lags: free memory, swapping, how often the TV has to close apps for memory, frozen apps
   - whether anything is damaged: the system image check (verified boot) and the last disk check
   - storage, Wi-Fi signal, software version, and which apps you never open
3. **Plans the cleanup with you**:
   - apps you never opened, demo and promotion apps, and uncompiled apps go straight into the plan
   - features you might use (voice search, casting, AirPlay, ambient mode, apps you open rarely) are asked about, with how much memory each one frees
4. **Applies the plan** through a guard that refuses core system and TV-maker packages, and logs every change with its undo.
5. **Restarts and verifies**: which changes held, which the TV switched back on by itself, and a before/after comparison at the same uptime.
6. **Hands back** a plain-language summary and reminds you to turn USB debugging off.

What it can't do: stop crashes caused by firmware bugs or failing hardware (it will tell you when the evidence points there), or remove the sponsored banners Google builds into the Google TV home screen (it explains the options).

## Requirements

- A computer on the same network as the TV, with Python 3.8+.
- Android SDK Platform-Tools (`adb`). The skill looks for it on `PATH` and in the usual SDK folders, and asks before installing anything.
- [Claude Code](https://claude.com/claude-code), or another agent that reads Agent Skills.

## Install

As a Claude Code plugin:

```
/plugin marketplace add Jrkesari/skills
/plugin install fix-android-tv-lag@jrkesari-skills
```

Or the whole skills repo, as your user skills folder:

```bash
git clone https://github.com/Jrkesari/skills ~/.claude/skills
```

Or just this skill: copy the `fix-android-tv-lag` folder into `~/.claude/skills/` (all projects) or a project's `.claude/skills/`.

## Use

Ask Claude Code in your own words, for example:

- "my sony bravia keeps restarting by itself and is really laggy, can you check it? it's on the same wifi"
- "speed up my google tv, remove the apps i never use"
- "is my android tv corrupted after the power cut?"

## Where its files go

Reports, the plan and the change log are kept on your computer in `~/.fix-android-tv-lag/<tv model>/`: `diag-<time>.json`, `plan.json` and `changes.jsonl`. To put everything back, ask Claude to undo the changes, or run `python scripts/apply_plan.py --undo ~/.fix-android-tv-lag/<model>/changes.jsonl TV-IP`. Uninstalled apps come back from the Play Store.

## Privacy

Reports never keep the Wi-Fi network name, MAC addresses, account names or emails. Nothing is sent anywhere but the TV. Turn USB debugging off when you are done: while it is on, any device on your network can ask the TV for access.

## Tested on

A Sony BRAVIA Google TV (Android 14, 2 GB RAM, Realtek SoC): it found two kernel panics and traced another restart to a power cut, removed or switched off 12 unused apps and features, and the TV went from closing 70 apps for memory in its first 40 minutes to none in the first minutes after. The package notes in `scripts/packages.py` say which TV each one was checked on. On other TVs the skill works from what that TV reports, and leaves unknown maker packages alone unless you agree.

## Files

| File | What it is |
|---|---|
| `SKILL.md` | The instructions Claude follows |
| `references/connection.md` | Turning on debugging, connecting, Windows quoting, drops |
| `references/diagnosis.md` | What each signal in the report means |
| `references/cleanup-catalog.md` | What is safe to remove, what to ask about, what never to touch, home-screen ads |
| `scripts/` | The tools the skill runs: see [scripts/README.md](scripts/README.md) |
| `evals/` | Test prompts for `claude plugin eval` |

## Licence

[MIT](../LICENSE)
