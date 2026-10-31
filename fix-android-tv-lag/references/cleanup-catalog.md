# What to clean up, what to ask, what never to touch

## Contents
- How candidates are chosen
- Straight into the plan
- Ask first
- Never touch
- What the TV turns back on
- Persistent apps
- Ads on the Google TV home screen
- Driving settings screens
- Keeping it healthy

`scripts/packages.py` holds the machine-readable version of this page (`REVIEWED`, the protected lists); `apply_plan.py` enforces it. Package names below were seen on a Sony BRAVIA Google TV on Android 14 unless marked otherwise. On any other TV, a package exists only if `pm list packages` shows it.

## How candidates are chosen

From the diagnosis, never from a generic debloat list:

1. Apps the user never opened (`last opened: never`) or not for months.
2. What is actually holding memory now (the report's biggest-users list), mapped to the feature it serves.
3. Settings that cost memory or CPU (screensaver, animations) and apps left uncompiled.

A list copied from the internet removes things this TV may need and misses what this TV actually runs.

## Straight into the plan

Show the plan, then apply; no separate question for each.

| Action | Plan entry | Notes |
|---|---|---|
| User-installed apps never opened | `uninstall` | Deletes app and data; the Play Store brings it back |
| Preinstalled apps never opened (e.g. `com.google.android.youtube.tvmusic`, `com.google.android.play.games`) | `disable` | Undo re-enables |
| Store demo mode `com.sony.dtv.multiscreendemo` (~30 MB running) | `disable` | Sony |
| Promotions `com.sony.dtv.promos`, app suggestions `com.sony.dtv.sonyselect` (~33 MB) | `disable` | Sony |
| Uncompiled apps (many `verify`) | `compile-apps` | Minutes of CPU; nothing to undo |
| Menu animations | `setting global window_animation_scale 0.5`, same for `transition_animation_scale` and `animator_duration_scale` | Menus feel quicker; undo restores the previous values |

## Ask first

One AskUserQuestion, multi-select, each option with its memory and what stops working:

| Feature | Plan entries | Frees | Stops working |
|---|---|---|---|
| Apple AirPlay & HomeKit | `remove-for-user com.sony.dtv.airplayapp` | ~80 MB | Casting from Apple devices. Persistent: see below |
| Ambient mode (screensaver) | `disable com.google.android.apps.tv.dreamx`, and `setting secure screensaver_enabled 0`, `screensaver_activate_on_sleep 0`, `screensaver_activate_on_dock 0` | ~108 MB while it runs | Photos or art when idle; the screen just turns off on its timer |
| Sony tab on the home screen | `disable com.sony.dtv.sonytab` | ~53 MB | The tab's content; its label may stay |
| An app opened rarely (e.g. `com.sonypicturescore`) | `disable` (system) or `uninstall` (user) | ~55 MB each when running in the background | That app |
| Streaming apps running when closed | `restrict-background PKG` | Often 400+ MB together | Home-screen rows update less often; the apps still open and play. Not yet tested on a TV |
| Chromecast built-in | `disable com.google.android.apps.mediashell` | ~62 MB | Casting from phones. Not tested |
| Voice search (Google Assistant / Gemini) | `disable com.google.android.katniss` | ~170-280 MB | The remote's mic button. Not tested; most people keep it |
| Video autoplay on the home screen | On screen: Settings > Accounts & Profiles > the account > **Autoplay video** off | CPU and memory while browsing | Trailers and video ads play only when chosen. The TV's text: "Applies to videos like trailers, Freeplay channels, and some ads" |

## Never touch

`apply_plan.py` refuses these: the home screen (`com.google.android.apps.tv.launcherx` and older launchers), setup (`com.google.android.tungsten.setupwraith`), Play services and Play Store, everything `com.android.*` and `android.*` (settings, Bluetooth for voice remotes, live TV and inputs, providers, keyboards, installers), the Google TV services under `com.google.android.tv.*` (remote, firmware updates), WebView, text-to-speech and TalkBack (accessibility), and the TV maker's and chip maker's services (`com.realtek.*`, `com.mediatek.*`, Sony's system, timer and control services, the service menu, USB updates).

A TV-maker package nobody has reviewed is refused too, until the user agrees and the action carries `"vendor_ok": true`. When unsure what a package does, leave it.

## What the TV turns back on

Seen on the tested TV, minutes or one restart after being disabled:

- `com.google.android.syncadapters.calendar`, `android.autoinstalls.config.google.gtvpai`: Google Play services re-enabled both within minutes.
- `com.sony.dtv.m2.seeds.iot`, `com.sony.dtv.m2.seeds.iot.remotestart` (Alexa / Google Home control): Sony re-enabled both at boot.

`apply_plan.py --verify` reports these as `TURNED BACK ON by the system`. Leave them and tell the user; they are marked `skip` so a plan will not try again.

## Persistent apps

A package flagged `PERSISTENT` (`dumpsys package PKG | grep pkgFlags`) is started by the system and kept alive. `disable` does not stop it, not even across a restart: on the tested TV AirPlay was still running after both. `remove-for-user` (`pm uninstall --user 0`) followed by a restart does stop it, and `cmd package install-existing PKG` brings it back. `apply_plan.py` warns when `disable` meets one.

## Ads on the Google TV home screen

Seen on Google TV, Android 14 (Sony BRAVIA):

- The sponsored banners ("Sponsored", "Presented by ...") are part of Google's home screen. No setting turns them off.
- **Apps-only mode** (Settings > Accounts & Profiles > the account > Apps only mode) does not remove them either. Its own confirmation screen says: "non-personalized, featured content will still be shown on your home screen" and "Search and voice will be disabled in this mode". It also hides Google's recommendations and the watchlist.
- **Autoplay video off** turns video banners into stills, which is most of their cost.
- The only full removal is another home screen from the Play Store, set up as the home app (on Google TV that means disabling `launcherx`, which this skill's guard refuses). It loses the Movies and Shows tabs, profiles and Google's recommendations. Offer it only when the user asks again after hearing the trade-off; it is outside what this skill has tested.

## Driving settings screens

Some settings live in the user's account, not in `settings`, so they are changed on screen:

1. `python scripts/tvadb.py screen TV-IP` lists what the TV shows, with bounds `[x1,y1][x2,y2]` and switch states.
2. Tap a row at the centre of its bounds: `python scripts/tvadb.py shell TV-IP "input tap X Y"`. Read the screen again after every step.
3. Dialog buttons can ignore taps. Moving focus with DPAD keys without looking can land it on a confirm button (in testing it landed on "Turn on" for Apps-only mode), so never press OK (`KEYCODE_DPAD_CENTER`) blind. Cancel with `input keyevent KEYCODE_BACK`.
4. Finish with `input keyevent KEYCODE_HOME` and `am force-stop com.android.tv.settings`, which frees the memory Settings held.
5. Screens show the account name and email: never repeat them.

## Keeping it healthy

- Restart weekly (Settings > System > Restart): pressing power on the remote is standby, not a restart, and memory slowly fills.
- Where the power cuts out, a stabiliser or small UPS: every cut forces a disk check, and voltage swings wear the power board.
- Leave automatic updates on. Crash fixes only arrive that way.
- A factory reset clears software problems and nothing else. Mention it only as a last resort, and say it erases apps and sign-ins.
