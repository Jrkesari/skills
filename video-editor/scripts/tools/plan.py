# Plans the cut: gives each input a beat-aligned slot of the song and writes edit/timeline.json (the only source of timing).
# Usage: plan.py [--duration 30|song] [--pace slow|medium|fast] [--song-in 0|auto|end|<s>] [--order as-listed|date|name]
#                [--title "..."] [--end-card "..."] [--theme dark|light] [--look fullbleed|framed] [--fit auto|cover|contain]
#                [--name "Film name"] [--song audio/song.wav]
# Reads edit/media_index.json (probe.py) and audio/beats.json (beats.py). Edit timeline.json by hand afterwards.
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffbin import ROOT

PACE = {"slow": 3.2, "medium": 2.0, "fast": 1.0}  # target seconds per shot
XF = {"slow": 0.5, "medium": 0.25, "fast": 0.0}  # dissolve length; 0 is a hard cut on the beat
MOVES = ["push-in", "pan-right", "push-out", "pan-left"]
KS = [1, 2, 4, 8]  # beats per shot

ap = argparse.ArgumentParser()
ap.add_argument("--duration")
ap.add_argument("--pace", choices=list(PACE))
ap.add_argument("--song-in", default="0")
ap.add_argument("--order", default="as-listed", choices=["as-listed", "date", "name"])
ap.add_argument("--title", default="")
ap.add_argument("--end-card", default="")
ap.add_argument("--theme", default="dark", choices=["dark", "light"])
ap.add_argument("--look", default="fullbleed", choices=["fullbleed", "framed"])
ap.add_argument("--fit", default="auto", choices=["auto", "cover", "contain"])
ap.add_argument("--name", default="Film")
ap.add_argument("--song", default="audio/song.wav")
A = ap.parse_args()

items = [i for i in json.load(open(os.path.join(ROOT, "edit", "media_index.json"), encoding="utf-8")) if "w" in i]
if A.order == "date":
    items.sort(key=lambda i: i.get("date") or "~")
elif A.order == "name":
    items.sort(key=lambda i: os.path.basename(i["path"]).lower())
B = json.load(open(os.path.join(ROOT, "audio", "beats.json"), encoding="utf-8"))
beats, downs = np.array(B["beats"]), np.array(B["downbeats"])
period, song_len = 60 / B["tempo"], B["duration"]
pace = A.pace or "medium"
end_len = 3.0 if A.end_card else 0.0
n = len(items)
k = min(KS, key=lambda c: abs(np.log(c * period / PACE[pace])))

fixed = A.duration not in (None, "song")
if fixed:
    D = float(A.duration)
elif A.duration == "song":
    D = None
else:
    D = n * k * period + end_len + 0.4


def pick_song_in(D):
    if A.song_in == "auto":  # the loudest stretch of the song that fits, starting on a downbeat
        bars = np.array(B["bars"]) if B["bars"] else np.zeros((0, 2))
        best, si = -1e9, 0.0
        for d in downs:
            if d + D > song_len:
                break
            m = bars[(bars[:, 0] >= d) & (bars[:, 0] < d + D), 1]
            if len(m) and m.mean() > best:
                best, si = m.mean(), float(d)
        return si
    if A.song_in == "end":  # finish on the song's real ending
        return max(0.0, song_len - D)
    return float(A.song_in)


if D is None:
    song_in = pick_song_in(0) if A.song_in not in ("auto", "end") else 0.0
    D = song_len - song_in
else:
    song_in = pick_song_in(min(D, song_len))
    D = min(D, song_len - song_in)

g = beats - song_in
g = g[(g > 0.2) & (g < D - 0.2)]
d0 = next((d - song_in for d in downs if d - song_in >= 0), g[0] if len(g) else 0.0)
Dc = float(g[np.argmin(abs(g - (D - end_len)))]) if end_len and len(g) else D  # the end card starts on a beat


def cuts_for(k):
    i0 = int(np.argmin(abs(g - d0))) if len(g) else 0
    L = k * period
    return [float(c) for c in g[i0::k] if 0.6 * L <= c <= Dc - 0.6 * L]


if fixed and not A.pace:  # a fixed length: pick the pace that gives every input one slot
    k = min(KS, key=lambda c: abs(len(cuts_for(c)) + 1 - n))
cuts = cuts_for(k)
bounds = [0.0] + cuts + [Dc]
slots = len(bounds) - 1
notes = []
if slots > n:
    notes.append(f"{slots} slots for {n} inputs: inputs repeat (videos from a later point, images with another move)")
elif slots < n:
    notes.append(f"{slots} slots for {n} inputs: the last {n - slots} inputs are left out; lengthen the film or quicken the pace")

shots = []
for i in range(slots):
    it, rep = items[i % n], i // n
    s, e = bounds[i], bounds[i + 1]
    xf = 0.0 if i == 0 else round(min(XF[pace], 0.4 * (e - s)), 3)
    shot = {"id": f"s{i + 1:02d}", "n": it["n"], "src": it["path"], "kind": it["kind"], "w": it["w"], "h": it["h"],
            "start": round(s, 3), "end": round(e, 3), "xf": xf, "focus": [0.5, 0.5], "fit": A.fit}
    if it["kind"] == "video":
        need = e - s + xf
        spare = max(0.0, it["dur"] - need)
        shot.update(move="push-in", amount=0.03, speed=1.0, keep_audio=False, audio=it.get("audio", False),
                    **{"in": round(spare * ((0.5 + 0.37 * rep) % 1.0), 3)})
        if it["dur"] < need:
            notes.append(f'{shot["id"]}: #{it["n"]} is {it["dur"]:.1f} s for a {need:.1f} s slot; its last frame holds')
    else:
        shot["move"] = MOVES[(i + rep) % 4]
    shots.append(shot)

texts = []
if A.title:
    texts.append({"text": A.title, "style": "title", "start": 0.35, "end": round(next((c for c in bounds[1:] if c >= 2.5), Dc), 3)})
if A.end_card:
    texts.append({"text": A.end_card, "style": "title", "start": round(Dc + 0.3, 3), "end": round(D - 0.25, 3)})

natural_end = abs(song_in + D - song_len) < 0.5
tl = {"name": A.name, "duration": round(D, 3), "fps": 30, "theme": A.theme, "look": A.look, "accent": "#EAC873",
      "song": A.song, "song_in": round(song_in, 3), "song_gain": 0, "fade_in": 0.0 if song_in == 0 else 0.25,
      "fade_out": 1.0 if natural_end else round(min(2.5, D * 0.15), 2), "video_fade_out": 0.8,
      "tempo": B["tempo"], "pace": pace, "beats_per_shot": k,
      "vo": {}, "vo_take": "", "vo_timing": "", "vo_fix": {}, "clip_audio_gain": -6, "clip_duck": -8,
      "shots": shots, "texts": texts, "sfx": []}
dst = os.path.join(ROOT, "edit", "timeline.json")
json.dump(tl, open(dst, "w", encoding="utf-8"), indent=1)
print(f"{D:.2f} s from song {song_in:.2f}-{song_in + D:.2f} s | {B['tempo']} bpm | {k} beats ({k * period:.2f} s) per shot | {slots} shots")
for s in shots:
    print(f'{s["id"]} {s["start"]:6.2f}-{s["end"]:6.2f}  #{s["n"]:<3} {s["kind"]:<5} {s["move"]:<9} xf {s["xf"]}  {os.path.basename(s["src"])}')
for t in texts:
    print(f'text {t["start"]:.2f}-{t["end"]:.2f} {t["style"]}: {t["text"]}')
for m in notes:
    print("NOTE", m)
print(dst)
