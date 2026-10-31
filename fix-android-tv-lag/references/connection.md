# Connecting to the TV

## What is needed

- The computer and the TV on the same network.
- Python 3.8+ and Android SDK Platform-Tools (`adb`). `tvadb.py` finds adb on `PATH`, in `$ADB`, `$ANDROID_HOME`, `$ANDROID_SDK_ROOT` or the default Android SDK folders. If it is missing, ask the user before installing anything; the official download is https://developer.android.com/tools/releases/platform-tools.

## Finding the TV

`python scripts/tvadb.py find` checks the addresses in the computer's ARP table for port 5555 (ADB) and 8008 (Google Cast) and prints the name each Cast device gives itself. `--scan` probes every address on the computer's /24 instead, for a TV the computer has not talked to yet. If neither finds it, the user can read the address on the TV: Settings > Network & Internet > the connected network.

`adb closed` with `cast yes` is an Android TV with debugging still off, or a TV that is not Android at all: LG webOS and Samsung Tizen TVs answer Cast too and have no ADB.

## Turning on debugging (the user does this with the remote)

Give these steps word for word; the menu names differ slightly between TVs, so tell the user to look for the nearest match.

**Google TV** (most TVs from 2021 on):
1. Settings > System > About.
2. Scroll to **Android TV OS build** and press OK on it seven times, until it says "You are now a developer".
3. Back to Settings > System > **Developer options**, and turn on **USB debugging**.

**Older Android TV:** the same, through Settings > Device Preferences > About > **Build**, then Device Preferences > Developer options.

On the Sony BRAVIA this was tested on (Android 14), USB debugging alone opened ADB over the network on port 5555; no cable was involved.

If port 5555 stays closed and Developer options shows **Wireless debugging** instead, Android 11 and later pair over the network: Wireless debugging > Pair device with pairing code, then `adb pair TV-IP:PAIRING-PORT CODE` and `adb connect TV-IP:PORT` with the port that screen shows. This path was not tested on a TV for this skill.

## Authorising this computer

`python scripts/tvadb.py connect TV-IP` connects and waits. The TV shows **Allow USB debugging?** with the computer's key fingerprint: the user ticks **Always allow from this computer** and presses OK. Until then adb reports `unauthorized`.

## Windows

PowerShell 5.1 drops the double quotes inside arguments it passes to native programs. `adb shell "grep -E \"a|b\" file"` arrives as `grep -E a|b file`, and the `|` becomes a pipe on the TV or on the PC: the command fails or does something else. The scripts pass every command to adb as an argument list, so they are immune. For a one-off command, use Git Bash with `MSYS_NO_PATHCONV=1` set (otherwise it rewrites anything that looks like a path, `/data/...` included) and single quotes inside the remote command.

## Drops and silence

- The TV's Wi-Fi drops for a few seconds now and then: `error: closed` or `device offline`. The scripts reconnect and retry. Before deciding the TV restarted, compare `uptime` with the previous reading.
- No ping and no answer on port 8008 means the TV is off, in standby, rebooting or without power. Ask the user what happened before reading anything into it; when it is back, the boot history shows whether it restarted on its own.
- Some TVs drop ADB in standby. Ask the user to switch the TV on.

## Ending

`python scripts/tvadb.py disconnect TV-IP`, then ask the user to turn **USB debugging** off (Settings > System > Developer options). While it is on, any device on the network can ask for access, and one tap on OK grants it.
