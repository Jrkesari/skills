# Inventories the user's media: kind, size (rotation applied), duration, audio, date; writes edit/media_index.json
# and numbered contact sheets edit/contact-N.jpg so every item can be looked at before planning.
# Usage: probe.py <file or folder> [...]   (folders are read one level deep, sorted by name)
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffbin import ROOT, ffmpeg, ffprobe

IMG = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff", ".gif"}
VID = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mts", ".3gp"}
TILE, COLS, ROWS = (320, 240), 6, 4


def probe_video_noprobe(p):
    """Fallback when only ffmpeg exists (e.g. the imageio-ffmpeg binary): parse `ffmpeg -i`."""
    err = subprocess.run([ffmpeg(), "-hide_banner", "-i", p], capture_output=True, text=True, errors="replace").stderr
    v = re.search(r"Stream .*Video: .*?(\d{2,5})x(\d{2,5})", err)
    if not v:
        return None
    w, h = int(v.group(1)), int(v.group(2))
    rot = re.search(r"rotat(?:e|ion of)\s*:?\s*(-?[\d.]+)", err)
    if rot and abs(int(float(rot.group(1)))) % 180 == 90:
        w, h = h, w
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    fps = re.search(r"([\d.]+) fps", err)
    date = re.search(r"creation_time\s*:\s*(\S+)", err)
    return {"kind": "video", "w": w, "h": h, "dur": round(int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3]), 3) if dur else 0.0,
            "fps": float(fps[1]) if fps else 30.0, "audio": "Audio:" in err, "date": date[1] if date else ""}


def probe_video(p):
    if not os.path.exists(ffprobe()):
        return probe_video_noprobe(p)
    d = json.loads(subprocess.run([ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", p],
                                  capture_output=True, text=True).stdout or "{}")
    v = next((s for s in d.get("streams", []) if s["codec_type"] == "video"), None)
    if not v:
        return None
    w, h = int(v["width"]), int(v["height"])
    rot = int(v.get("tags", {}).get("rotate", 0) or 0)
    for sd in v.get("side_data_list", []):
        rot = int(sd.get("rotation", rot) or rot)
    if abs(rot) % 180 == 90:  # ffmpeg auto-rotates on decode, so plan with the displayed size
        w, h = h, w
    num, den = (v.get("avg_frame_rate") or "30/1").split("/")
    return {"kind": "video", "w": w, "h": h, "dur": round(float(d["format"].get("duration", 0)), 3),
            "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else 30.0,
            "audio": any(s["codec_type"] == "audio" for s in d["streams"]),
            "date": d["format"].get("tags", {}).get("creation_time", "")}


def probe_image(p):
    try:
        im = Image.open(p)
    except Exception as e:  # HEIC needs pillow-heif; convert with ffmpeg if PIL cannot open it
        return {"kind": "image", "error": str(e)}
    date = (im.getexif().get(36867) or im.getexif().get(306) or "") if hasattr(im, "getexif") else ""
    im = ImageOps.exif_transpose(im)
    return {"kind": "image", "w": im.width, "h": im.height, "date": str(date)}


def thumb(item):
    p = item["path"]
    if item["kind"] == "video":
        tmp = os.path.join(tempfile.mkdtemp(), "t.jpg")
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f'{item["dur"] / 2:.2f}', "-i", p, "-frames:v", "1",
                        "-vf", "scale=640:-2", tmp])
        im = Image.open(tmp) if os.path.exists(tmp) else Image.new("RGB", TILE, "#333")
    else:
        im = ImageOps.exif_transpose(Image.open(p))
    im = im.convert("RGB")
    im.thumbnail(TILE)
    return im


def sheets(items):
    out, per = [], COLS * ROWS
    for s in range(0, len(items), per):
        sheet = Image.new("RGB", (COLS * TILE[0], ROWS * (TILE[1] + 28)), "#111")
        dr = ImageDraw.Draw(sheet)
        for k, it in enumerate(items[s:s + per]):
            x, y = (k % COLS) * TILE[0], (k // COLS) * (TILE[1] + 28)
            if "w" in it:
                im = thumb(it)
                sheet.paste(im, (x + (TILE[0] - im.width) // 2, y + (TILE[1] - im.height) // 2))
            tag = f'#{it["n"]} {"V %.1fs" % it["dur"] if it["kind"] == "video" else "IMG"} {it.get("w", "?")}x{it.get("h", "?")}'
            dr.text((x + 6, y + TILE[1] + 6), tag, fill="#ddd")
        path = os.path.join(ROOT, "edit", f"contact-{s // per + 1}.jpg")
        sheet.save(path, quality=85)
        out.append(path)
    return out


if __name__ == "__main__":
    files = []
    for a in sys.argv[1:]:
        if os.path.isdir(a):
            files += [os.path.join(a, f) for f in sorted(os.listdir(a))]
        else:
            files.append(a)
    items = []
    for p in files:
        ext = os.path.splitext(p)[1].lower()
        info = probe_video(p) if ext in VID else probe_image(p) if ext in IMG else None
        if info:
            items.append({"n": len(items) + 1, "path": os.path.abspath(p).replace("\\", "/"), **info})
    os.makedirs(os.path.join(ROOT, "edit"), exist_ok=True)
    json.dump(items, open(os.path.join(ROOT, "edit", "media_index.json"), "w", encoding="utf-8"), indent=1)
    for it in items:
        print(f'#{it["n"]:<3} {it["kind"]:<5} {it.get("w", "?")}x{it.get("h", "?")} '
              f'{("%.1fs" % it["dur"]) if it["kind"] == "video" else "":>7} {"audio" if it.get("audio") else "":5} {os.path.basename(it["path"])}'
              + (f'  ERROR {it["error"]}' if "error" in it else ""))
    print("sheets:", *sheets(items))
