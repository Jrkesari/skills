# Cuts the real captures into timed clips and stills for both films, with personal data blurred into the pixels.
# Usage: prepare_media.py <fmt> [names]   (fmt: a formats.FORMATS key; reads edit/media.json, writes the project's assets/)
import json, os, re, subprocess, sys
from PIL import Image, ImageFilter

ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from formats import FORMATS, layout_of, project_dir
FF = os.path.join(ROOT, "bin", "ffmpeg.exe")
TAKES = os.path.join(ROOT, "capture", "takes")
STILLS = os.path.join(ROOT, "capture", "stills2x_root", "stills")
SENSITIVE = re.compile(os.environ.get("CAP_SENSITIVE", r"@netision") + r"|avatar|\(?[a-z]+@[a-z]+\.", re.I)


def blur_boxes(boxes, pad=6):
    """Logged boxes whose text is personal: names, emails, avatars."""
    out = []
    for b in boxes:
        x, y, w, h, txt = b
        if SENSITIVE.search(txt) or txt == "avatar":
            out.append((max(x - pad, 0), max(y - pad, 0), w + 2 * pad, h + 2 * pad))
    return sorted(set(out))


def take_boxes(take):
    d = json.load(open(os.path.join(TAKES, take + ".json")))
    return blur_boxes([b for _, bx in d["boxes"] for b in bx]), d


def event_time(d, spec):
    """'label+0.5' -> seconds into the take."""
    m = re.match(r"([a-z0-9-]+)([+-][\d.]+)?$", spec)
    t = next(t for t, lab in d["events"] if lab == m.group(1))
    return t + float(m.group(2) or 0)


def cut_clip(c, fmt, out_dir, extra_boxes):
    boxes, d = take_boxes(c["take"])
    boxes = sorted(set(boxes + [tuple(b) for b in extra_boxes]))
    if c.get("after_send"):  # the home greeting sits where the chat title is once a turn opens
        boxes = [b for b in boxes if b[1] > 60]
    src = os.path.join(TAKES, c["take"] + ".mp4")
    probe = subprocess.run([FF.replace("ffmpeg.exe", "ffprobe.exe"), "-v", "error", "-select_streams", "v", "-show_entries",
                            "stream=width,height", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip().split(",")
    sw = int(probe[0]); css_w = FORMATS[fmt][0]
    k = sw / css_w  # source pixels per CSS pixel (2 for 4K takes)
    t0, t1 = event_time(d, c["in"]), event_time(d, c["out"])
    speed = (t1 - t0) / c["dur"]
    W, H = FORMATS[fmt]
    edge = ",fillborders=right=10:mode=smear" if layout_of(fmt) == "port" else ""  # tall takes carry a dark right band
    chain = [f"[0:v]setpts=(PTS-STARTPTS)/{speed:.5f},scale={W}:{H}:flags=lanczos{edge},fps=30[v0]"]
    last = "v0"
    for i, (x, y, w, h) in enumerate(boxes):
        chain.append(f"[{last}]split[a{i}][b{i}];[b{i}]crop={w}:{h}:{x}:{y},gblur=sigma=10:steps=3[c{i}];[a{i}][c{i}]overlay={x}:{y}[v{i + 1}]")
        last = f"v{i + 1}"
    out = os.path.join(out_dir, c["name"] + ".mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", src,
                    "-filter_complex", ";".join(chain), "-map", f"[{last}]", "-t", f"{c['dur']:.3f}",
                    "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-an", out], check=True)
    return {"name": c["name"], "dur": c["dur"], "speed": round(speed, 2), "src": [round(t0, 2), round(t1, 2)], "blurred": len(boxes)}


def prep_still(s, out_dir):
    src = s.get("path") or os.path.join(STILLS, s["src"] + ".png")
    im = Image.open(src).convert("RGB")
    k = im.width / s.get("w", FORMATS.get(s["src"].rsplit("_", 1)[-1], (1920,))[0])  # source CSS width from its format suffix
    bj = src[:-4] + ".boxes.json"
    boxes = blur_boxes(json.load(open(bj))) if os.path.exists(bj) else []
    boxes += [tuple(b) for b in s.get("blur", [])]
    for x, y, w, h in boxes:
        box = tuple(int(v * k) for v in (x, y, x + w, y + h))
        im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(14 * k)), box[:2])
    for x, y, w, h in s.get("patch", []):  # paint a control out with the colour beside it
        box = tuple(int(v * k) for v in (x, y, x + w, y + h))
        im.paste(im.getpixel((box[0] - 4, box[1] + (box[3] - box[1]) // 2)), box)
    out = os.path.join(out_dir, s["name"] + ".jpg")
    im.save(out, quality=93, subsampling=0)
    return {"name": s["name"], "size": im.size, "blurred": len(boxes)}


if __name__ == "__main__":
    fmt = sys.argv[1]
    spec = json.load(open(os.path.join(ROOT, "edit", "media.json")))[fmt]
    base = os.path.join(project_dir(ROOT, fmt), "assets")
    for sub in ["clips", "stills"]:
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    only = set(sys.argv[2:])
    report = []
    for c in spec["clips"]:
        if not only or c["name"] in only:
            report.append(cut_clip(c, fmt, os.path.join(base, "clips"), c.get("blur", [])))
            print(report[-1], flush=True)
    for s in spec["stills"]:
        if not only or s["name"] in only:
            report.append(prep_still(s, os.path.join(base, "stills")))
            print(report[-1], flush=True)
