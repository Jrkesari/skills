# Finds ffmpeg/ffprobe: $FFMPEG, then <film>/bin, then PATH.
import os, shutil

ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder


def ffmpeg():
    exe = ".exe" if os.name == "nt" else ""
    for p in (os.environ.get("FFMPEG"), os.path.join(ROOT, "bin", "ffmpeg" + exe), shutil.which("ffmpeg")):
        if p and os.path.exists(p):
            return p
    raise SystemExit("ffmpeg not found: set FFMPEG or put it in <film>/bin")


def ffprobe():
    f = ffmpeg()
    d, b = os.path.split(f)
    return os.path.join(d, b.replace("ffmpeg", "ffprobe"))
