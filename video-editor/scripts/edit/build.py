# Builds one canvas's HyperFrames index.html from edit/timeline.json and edit/prepared_<fmt>.json.
# Usage: build.py <fmt>   (run prepare.py <fmt> first; audio/mix.wav is copied into the project by the render step)
import html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import Film, ROOT
from formats import FORMATS, project_dir, window_rect, zones

fmt = sys.argv[1]
TL = json.load(open(os.path.join(ROOT, "edit", "timeline.json"), encoding="utf-8"))
PREP = json.load(open(os.path.join(ROOT, "edit", f"prepared_{fmt}.json"), encoding="utf-8"))
W, H = FORMATS[fmt]
D = TL["duration"]
look = TL.get("look", "fullbleed")
framed = look == "framed"
Z = zones(fmt)
f = Film(fmt, W, H, D)
f.add('<div class="bg"></div><div class="vignette"></div><div class="grain"></div>')
X, Y, WW, WH = window_rect(fmt, look)
win = f.window(X, Y, WW, WH, 0, D, radius=18 if framed else 0, frame=framed,
               enter="fade" if TL.get("video_fade_in") else "none", exit_="none")


def camera(s, sw, sh, t0, t1):
    """Ken Burns keys for one shot: (t, cx, cy, zoom[, ease]) in the plate's px."""
    fx, fy = s.get("focus", [0.5, 0.5])
    cx, cy = fx * sw, fy * sh
    amt = s.get("amount") or min(0.10, max(0.04, 0.025 * (t1 - t0)))
    dx, dy = sw * amt * 0.4, sh * amt * 0.4  # stays inside the zoom's overflow, so a pan never stalls on an edge
    z = 1 + amt
    a, b = {
        "push-in": ((cx, cy, 1.0), (cx, cy, z)),
        "push-out": ((cx, cy, z), (cx, cy, 1.0)),
        "pan-left": ((cx + dx, cy, z), (cx - dx, cy, z)),
        "pan-right": ((cx - dx, cy, z), (cx + dx, cy, z)),
        "pan-up": ((cx, cy + dy, z), (cx, cy - dy, z)),
        "pan-down": ((cx, cy - dy, z), (cx, cy + dy, z)),
    }.get(s.get("move", "push-in"), ((cx, cy, 1.0), (cx, cy, 1.0)))  # "still"
    return [(t0, *a), (t1, *b, "none" if s["kind"] == "video" else "sine.inOut")]


def scrim(kind, t0, t1):
    """A soft gradient behind text over pictures, with its own in and out tweens."""
    if framed:
        return
    sid = f.uid("scr")
    f.add(f'<div id="{sid}" class="scrim {kind}"></div>')
    f.tl(f'tl.fromTo("#{sid}", {{opacity: 0}}, {{opacity: 1, duration: 0.4, ease: "none"}}, {max(t0 - 0.1, 0):.3f});')
    f.tl(f'tl.to("#{sid}", {{opacity: 0, duration: 0.4, ease: "none"}}, {max(t1 - 0.4, t0 + 0.4):.3f});')


shots = TL["shots"]
for s in shots:  # per-format overrides, as in prepare.py
    s.update(s.get(fmt) or {})
for i, s in enumerate(shots):
    p = PREP[s["id"]]
    xf = s.get("xf", 0.0)
    t0, t1 = max(s["start"] - xf, 0.0), s["end"]
    last = i == len(shots) - 1
    pid, _ = f.plate(win, WW, WH, p["file"], p["w"], p["h"], t0, t1, camera(s, p["w"], p["h"], t0, t1),
                     video=p["kind"] == "video", xfade=xf, fade_out=False, hide_at=None if last else t1 + 0.04)
    if last and t1 < D - 0.05:  # an end card follows on the background
        f.tl(f'tl.to("#{pid}", {{opacity: 0, duration: 0.5, ease: "power1.in"}}, {t1 - 0.25:.3f});')

for tx in TL.get("texts", []):
    st = tx.get("style", "title")
    if st == "title":
        x, y, w, size = Z["title"]
        size = tx.get("size", size)
        rows, t = [], tx["start"]
        for line in tx["text"].split("\n"):  # a line wrapped in *...* is set in the italic serif
            serif = len(line) > 2 and line.startswith("*") and line.endswith("*")
            rows.append([(line.strip("*"), "serif" if serif else "sans", t)])
            t += 0.06 * len(line.split()) + 0.18
        y -= round((len(rows) - 1) * size * 0.6)
        scrim("mid", tx["start"], tx["end"])
        f.words(rows, x, y, w, size, tx["end"], align="center", lh=1.14)
    else:
        x, y, w, size = Z[st][:4]
        scrim("low", tx["start"], tx["end"])
        f.text(html.escape(tx["text"]).replace("\n", "<br>"), x, y, w, tx["start"], tx["end"], st,
               align="left" if st == "lower" else "center", size=tx.get("size", size))

if TL.get("fx"):  # an optional film-specific module in edit/ with apply(film, TL, fmt, W, H): extra layers, custom cards
    import importlib
    importlib.import_module(TL["fx"]).apply(f, TL, fmt, W, H)

cap_path = os.path.join(ROOT, "edit", "captions.json")
if TL.get("vo") and os.path.exists(cap_path):
    caps = [c for c in json.load(open(cap_path, encoding="utf-8")) if c["id"] not in TL.get("no_captions", [])]
    if caps:
        x, y, w, size, mw = Z["caption"]
        scrim("low", caps[0]["start"] - 0.2, max(c["end"] for c in caps) + 0.5)
        f.captions(caps, {c["id"] for c in caps}, x, y, w, size, mw)

vfo = TL.get("video_fade_out", 0.8)
if vfo:
    f.add('<div id="endfade" class="fade"></div>')
    f.tl(f'tl.fromTo("#endfade", {{opacity: 0}}, {{opacity: 1, duration: {vfo}, ease: "power1.in"}}, {D - vfo:.3f});')

theme = "style_light.css" if TL.get("theme") == "light" else "style.css"
css = open(os.path.join(HERE, theme), encoding="utf-8").read() + f':root {{ --accent: {TL.get("accent", "#EAC873")}; }}\n'
out = os.path.join(project_dir(ROOT, fmt), "index.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(f.page(css, "assets/mix.wav", TL.get("name", "Film")))
print("wrote", out, len(f.js), "tweens")
