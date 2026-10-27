# Builds the film mix from the user's song, plus optional voiceover, kept clip sound and SFX, all placed by edit/timeline.json.
# Usage: build_audio.py [--diag]   (writes audio/mix_raw.wav, and edit/captions.json when there is a voiceover; then run norm.sh)
import json, os, sys
import numpy as np, scipy.io.wavfile as wf

ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, "tools"))
import sfx as S
from mix import load, place, duck_curve, SR

A = os.path.join(ROOT, "audio")
TL = json.load(open(os.path.join(ROOT, "edit", "timeline.json"), encoding="utf-8"))
n = int(TL["duration"] * SR)
vo, mus, clips, fx = (np.zeros((n, 2), np.float32) for _ in range(4))

# song: the master clock; never time-stretched, only trimmed and faded
song = load(os.path.join(ROOT, TL["song"]))
si = int(TL.get("song_in", 0) * SR)
bed = song[si:si + n].copy()
if len(bed) < n:
    print(f"NOTE song runs out {(n - len(bed)) / SR:.2f} s before the film ends")
m = len(bed)
fi, fo = min(int(TL.get("fade_in", 0) * SR), m), min(int(TL.get("fade_out", 2.0) * SR), m)
if fi:
    bed[:fi] *= np.linspace(0, 1, fi)[:, None]
if fo:
    bed[m - fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
place(mus, bed, 0, TL.get("song_gain", 0))

# optional voiceover: one take, spliced per line with pre/post roll so onsets are not clipped
caps = []
if TL.get("vo"):
    T = {l["id"]: l for l in json.load(open(os.path.join(A, TL["vo_timing"]), encoding="utf-8"))}
    for k, v in TL.get("vo_fix", {}).items():
        T[k].update(v)
    take = load(os.path.join(A, TL["vo_take"]))
    for lid, at in TL["vo"].items():
        l = T[lid]
        s0, s1 = max(l["start"] - 0.22, 0), l["end"] + 0.24
        seg = take[int(s0 * SR):int(s1 * SR)].copy()
        f1, f2 = int(0.015 * SR), int(0.12 * SR)
        seg[:f1] *= np.linspace(0, 1, f1)[:, None]
        seg[-f2:] *= np.linspace(1, 0, f2)[:, None]
        place(vo, seg, at)
        off = at - s0
        words = [dict(w, start=round(w["start"] + off, 3), end=round(w["end"] + off, 3)) for w in l["words"]]
        caps.append({"id": lid, "text": l["text"], "start": round(l["start"] + off, 3), "end": round(l["end"] + off, 3), "words": words})
    json.dump(caps, open(os.path.join(ROOT, "edit", "captions.json"), "w", encoding="utf-8"), indent=1)

# optional sound kept from the user's clips (prepare.py writes audio/clips/<id>.wav)
for s in TL["shots"]:
    p = os.path.join(A, "clips", s["id"] + ".wav")
    if s.get("keep_audio") and os.path.exists(p):
        x = load(p)
        k = min(len(x) // 2, int(0.06 * SR))
        x[:k] *= np.linspace(0, 1, k)[:, None]
        x[len(x) - k:] *= np.linspace(1, 0, k)[:, None]
        place(clips, x, max(s["start"] - s.get("xf", 0), 0), s.get("audio_gain", TL.get("clip_audio_gain", -6)))

lib = {"whoosh": S.whoosh(0.8, 400, 5000), "whoosh_soft": S.whoosh(0.6, 600, 3500), "impact": S.impact(2.4), "shimmer": S.shimmer(1.8), "click": S.click()}
for c in TL.get("sfx", []):
    place(fx, S.riser(c["dur"]) if c["name"] == "riser" else lib[c["name"]], c["t"], c["gain"])

g = np.ones((n, 1), np.float32)
if np.abs(vo).max() > 0:
    g = g * duck_curve(vo, -10, 0.06, 0.5)
if np.abs(clips).max() > 0 and TL.get("clip_duck"):
    g = g * duck_curve(clips, TL["clip_duck"], 0.08, 0.4)
mix = vo + clips + mus * g + fx
mix /= max(1.0, np.abs(mix).max() / 0.89)
wf.write(os.path.join(A, "mix_raw.wav"), SR, mix.astype(np.float32))
print("peak dB", round(20 * np.log10(np.abs(mix).max() + 1e-9), 2), "| vo lines", len(caps), "| kept clip sounds",
      sum(1 for s in TL["shots"] if s.get("keep_audio")))
if "--diag" in sys.argv:
    r = lambda x, mask: round(float(20 * np.log10(np.sqrt((x[mask] ** 2).mean()) + 1e-9)), 1) if mask.any() else None
    speech = np.abs(vo).max(1) > 0.02
    print("song rms overall", r(mus * g, np.ones(n, bool)), "| VO rms in speech", r(vo, speech), "| song under speech", r(mus * g, speech))
