# Reading the diagnosis

## Contents
- Restarts: boot reasons, the kernel log, what to ask the user
- Lag: memory, reclaim, app kills, frozen apps, CPU
- Measuring fairly
- Damage: verified boot and the disk check
- Storage, Wi-Fi, heat, software version
- App usage and app compilation

Numbers quoted below come from one Sony BRAVIA Google TV (2 GB RAM, Realtek SoC, Android 14) before and after a cleanup. Use them as a sense of scale, not as thresholds: compare a TV against itself.

## Restarts

`persist.sys.boot.reason.history` holds the last few boots, newest first, as `reason,epoch` (four on the tested TV, so older restarts are gone). `diagnose.py` turns each into a time and a meaning:

| Reason | Means | Next |
|---|---|---|
| `kernel_panic` | The kernel crashed and the TV restarted itself | Look at the last kernel log; see "Crashes" below |
| `watchdog` | The system froze and a watchdog reset it | Same as a crash |
| `cold` | Power-on from no power | Ask: unplugged, power cut, or switched off at the wall then? If none, a power-supply fault |
| `hard...` | Hardware reset | Treat like a crash if the user did nothing |
| `reboot,shell` | adb reboot (your own) | Nothing |
| `reboot,...`, `shutdown,...` | A restart someone or something asked for (settings, update) | Nothing, unless the user did not ask for it |

An epoch from before 2020 (`1514764819` is 1 January 2018) means the clock was not set yet when the TV booted: the time is unknown, not wrong. A power-on is usually such a boot.

**The last kernel log.** `SYSTEM_LAST_KMSG` in the TV's crash store (`dumpsys dropbox`) is the tail of the previous boot's kernel log. It survives only a warm restart; after a power cut there is none. The report keeps the flagged lines: `Kernel panic - not syncing`, `Unable to handle kernel`, `Internal error: Oops`, `watchdog`, and `reboot: Restarting system with command '...'`, which names who asked for a restart. The crash store is small (five entries on the tested TV), which is one more reason the first report comes before any restart.

**Crashes.** No app or setting causes a kernel panic directly: it is a bug in the firmware's drivers or a hardware fault (memory, storage chip, power). Heavy memory pressure can make a buggy driver fall over more often, so a cleanup may make panics rarer, but the fixes that address the cause are a firmware update and, if panics continue after the cleanup and the update, service. On the tested TV, two panics nine minutes apart came after days in which the TV had closed 34 and 36 apps for memory (against 1 to 5 on ordinary days).

**The red light.** Many TVs (Sony among them) blink the standby light in a repeating pattern after a fault. The number of blinks is the error code service asks for.

## Lag

| Signal | Where | Reading it |
|---|---|---|
| Memory available | `MemAvailable` | What apps can still get without killing others. On the tested 2 GB TV, ~590 MB with heavy swapping |
| Swapped out | `SwapTotal - SwapFree` | Memory compressed out of the way (zram). Hundreds of MB means constant reshuffling |
| Reclaim work | `kswapd` CPU seconds per minute of uptime | Time the kernel spends finding free memory: 1.8 s/min on the tested TV before cleanup |
| Apps killed since boot | `am_kill` / `killinfo` in the events log | 70 in the first 40 minutes before; 0 in the first minutes after |
| Low-memory kills by day | `dumpsys activity exit-info`, reason `LOW_MEMORY` | Spikes on the days before a crash are worth mentioning |
| Frozen apps (ANR) | `system_app_anr` in the crash store | The report keeps the process and the pressure lines: `memory some avg10=65.90` means tasks waited on memory 66% of the last 10 s |
| CPU | `top`, the idle figure | Use idle %, not load average: on Realtek TV chips the load average sits around 20-25 even when idle, from kernel threads waiting on hardware |

## Measuring fairly

- The first 5-10 minutes after a boot are busy (apps starting, optimisation, swap filling), so a reading then says little.
- Compare at the same uptime as the baseline, with the TV used the same way.
- Your own screen navigation costs memory: TV Settings and Play services screens stay loaded afterwards. `am force-stop com.android.tv.settings` after using Settings.
- "Apps killed since boot" counts from the events log, which can wrap on a long uptime; compare short, equal windows.

## Damage

**Verified boot.** `ro.boot.verifiedbootstate=green` with `ro.boot.veritymode=enforcing` means the system partitions match the maker's signed image and are checked on every read; damage there would stop the boot or change the state. `orange` means an unlocked bootloader, `yellow` a system signed with someone else's key, `red` a failed check: service.

**The disk check.** After an unclean shutdown the TV runs `e2fsck` on its data partition and keeps the log as `SYSTEM_FSCK`. The exit code says what happened (man e2fsck): 0 clean, 1 errors found and corrected, 2 corrected and a reboot needed, 4 errors left uncorrected, 8 the check could not run.

- Routine after a power cut, nothing lost: `extent tree could be shorter`, `QUOTA WARNING ... Update quota info`, `Free blocks/inodes count wrong`, orphan inodes cleared, `recovering journal`, then `FILE SYSTEM WAS MODIFIED` with exit 1.
- Damage: `UNEXPECTED INCONSISTENCY`, `illegal block`, `Unattached inode`, `deleted/unused inode`, `Duplicate or bad block`, `Multiply-claimed`, `I/O error`, `short read`, or exit 4 and up. Repeated across boots, the storage chip is failing: tell the user to expect service, and that a factory reset will not fix hardware.

## Storage, Wi-Fi, heat, software

- **Storage:** `df /data` and `dumpsys diskstats`. Low free space on `/data` makes app updates and installs fail; the 100%-full system partition is normal (it is read-only). App caches are rebuilt as soon as the apps run, so clearing them frees no memory and only buys space for a while.
- **Wi-Fi:** RSSI above -60 dBm is good, -60 to -70 workable, below -70 weak. A weak signal shows up as buffering, which users also call lag. The report never keeps the network name or MAC addresses.
- **Heat:** many TVs expose no temperature sensors to the shell. Then ask about the vents: dust and a tight cabinet are the usual cause of restarts that start after the TV has been on for a while.
- **Software:** `tvadb.py update-check` opens the update screen and reads it ("Your system is up to date", and when it last checked).

## App usage and compilation

**Last opened.** `dumpsys usagestats` App Standby lines carry `usedByUser=+<time>`: how long ago the user last opened the app, in TV-on time, kept across restarts. `<uninitialized>` means never opened since tracking began (usually setup or the last factory reset). The in-memory daily and yearly usage stats are no use here: when the clock jumps at boot they restart from that boot.

**Compilation.** `dumpsys package dexopt` gives each app's state: `speed-profile` or `speed` are compiled; `verify` runs interpreted until the TV compiles it, usually just after an update. The TV compiles overnight when idle in standby, which never happens if it is unplugged every night or the power keeps cutting out. `pm bg-dexopt-job` (the plan's `compile-apps`) does it now: about 2.5 minutes on the tested TV, which then compiled Prime Video and Google Assistant from `verify`.
