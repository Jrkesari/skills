"""Which packages a cleanup may touch. Shared by diagnose.py and apply_plan.py."""

# The TV stops working properly without these: home screen, settings, setup, Play services,
# Bluetooth (voice remotes), inputs, live TV, accessibility, speech, keyboards, installers.
PROTECTED_EXACT = {
    "android",
    "com.google.android.tts",              # spoken answers and TalkBack
    "com.google.android.marvin.talkback",  # accessibility
    "com.google.android.youtube.tv.recommendations",
}
PROTECTED_PREFIXES = (
    "com.android.", "android.",
    "com.google.android.gms", "com.google.android.gsf",
    "com.google.android.apps.tv.launcherx", "com.google.android.tvlauncher", "com.google.android.leanbacklauncher",
    "com.google.android.tungsten.", "com.google.android.tv.", "com.google.android.inputmethod.",
    "com.google.android.webview", "com.google.android.permissioncontroller", "com.google.android.packageinstaller",
    "com.google.android.ext.", "com.google.android.overlay", "com.google.android.modulemetadata",
    "com.google.android.onetimeinitializer", "com.google.android.partnersetup", "com.google.android.feedback",
)
# TV makers' and chip makers' packages: unknown ones are left alone until someone has reviewed them.
VENDOR_PREFIXES = (
    "com.sony.", "com.realtek.", "com.mediatek.", "com.amlogic.", "com.tcl.", "com.hisense.", "com.xiaomi.",
    "com.mitv.", "com.philips.", "org.droidtv.", "com.nvidia.", "com.skyworth.", "com.vestel.", "com.toshiba.",
    "com.panasonic.", "com.sharp.", "com.lge.", "com.samsung.",
)

# Packages reviewed on a real TV. verdict: safe | ask | skip (the system turns it back on) | never.
# "Seen on" names the device it was checked on; on any other TV, check the package exists before acting.
REVIEWED = {
    "com.sony.dtv.multiscreendemo": ("safe", "Store demo-mode app, runs in the background (~30 MB)", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.promos": ("safe", "Sony promotions", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.sonyselect": ("safe", "Sony Select app suggestions, runs in the background (~33 MB)", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.airplayapp": ("ask", "Apple AirPlay & HomeKit (~80 MB). Persistent: use remove-for-user and restart, disable alone keeps it running", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.sonytab": ("ask", "Sony tab on the home screen (~53 MB); the tab label can stay after it is off", "Sony BRAVIA VU3, Android 14"),
    "com.sonypicturescore": ("ask", "Sony Pictures Core movie app (~56 MB in the background)", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.m2.seeds.iot": ("skip", "Alexa / Google Home control; Sony turns it back on at every boot", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.m2.seeds.iot.remotestart": ("skip", "Alexa / Google Home remote power-on; Sony turns it back on at every boot", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.m2.devicecontrolservice": ("never", "Sony device control service", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.sonysystemservice": ("never", "Sony system service", "Sony BRAVIA VU3, Android 14"),
    "com.sony.dtv.timers": ("never", "Sleep and on/off timers", "Sony BRAVIA VU3, Android 14"),
    "com.realtek.servicemenu": ("never", "Factory service menu", "Sony BRAVIA VU3, Android 14"),
    "com.realtek.usbupdate": ("never", "Firmware update from USB", "Sony BRAVIA VU3, Android 14"),
    "com.google.android.apps.tv.dreamx": ("ask", "Ambient mode screensaver (~108 MB while it runs); also set secure screensaver_enabled=0", "Sony BRAVIA VU3, Android 14"),
    "com.google.android.youtube.tvmusic": ("safe", "YouTube Music, when the user never opens it", "Sony BRAVIA VU3, Android 14"),
    "com.google.android.play.games": ("safe", "Google Play Games, when the user never opens it", "Sony BRAVIA VU3, Android 14"),
    "com.google.android.syncadapters.calendar": ("skip", "Calendar sync; Google Play services turns it back on within minutes", "Sony BRAVIA VU3, Android 14"),
    "android.autoinstalls.config.google.gtvpai": ("skip", "Partner app auto-install config; Google Play services turns it back on", "Sony BRAVIA VU3, Android 14"),
    "com.google.android.katniss": ("ask", "Google Assistant / Gemini voice search (~170-280 MB); the remote's mic button stops working. Not tested off", "not tested"),
    "com.google.android.apps.mediashell": ("ask", "Chromecast built-in (~62 MB); casting from phones stops. Not tested off", "not tested"),
}


def is_protected(pkg):
    verdict = REVIEWED.get(pkg, ("",))[0]
    if verdict in ("safe", "ask", "skip"):
        return False
    return verdict == "never" or pkg in PROTECTED_EXACT or pkg.startswith(PROTECTED_PREFIXES)


def is_unreviewed_vendor(pkg):
    return pkg not in REVIEWED and pkg.startswith(VENDOR_PREFIXES)
