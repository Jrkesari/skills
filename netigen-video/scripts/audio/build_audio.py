import os
# Builds the film mix from the VO take, the Lyria bed and procedural SFX, all placed by edit/timeline.json.
import json, sys, numpy as np, scipy.io.wavfile as wf
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"tools"))
import sfx as S
from mix import load, place, duck_curve, SR
A = os.path.join(ROOT, r"audio")
TL = json.load(open(os.path.join(ROOT, r"edit\timeline.json")))
T = {l["id"]: l for l in json.load(open(A + "/" + TL.get("vo_timing", "vo_timing.json")))}
for k, v in TL["vo_fix"].items(): T[k].update(v)
n = int(TL["duration"] * SR)
vo, mus, fx = (np.zeros((n, 2), np.float32) for _ in range(3))
take = load(A + "/" + TL.get("vo_take", "vo_charon/all.wav"))
caps = []
for lid, at in TL["vo"].items():
    l = T[lid]; s0, s1 = max(l["start"] - 0.22, 0), l["end"] + 0.24
    seg = take[int(s0 * SR):int(s1 * SR)].copy()
    f1, f2 = int(0.015 * SR), int(0.12 * SR); seg[:f1] *= np.linspace(0, 1, f1)[:, None]; seg[-f2:] *= np.linspace(1, 0, f2)[:, None]
    place(vo, seg, at)
    off = at - s0
    words = [dict(w, start=round(w["start"] + off, 3), end=round(w["end"] + off, 3)) for w in l["words"]]
    if lid == "l07": words[0]["start"] = round(T["l07"]["start"] + off, 3)
    caps.append({"id": lid, "text": l["text"], "start": round(l["start"] + off, 3), "end": round(l["end"] + off, 3), "words": words})
mo = int(TL.get("music_offset", 1.9) * SR)
bed = load(A + "\\" + TL.get("music", "music_take3.wav"))[mo:mo + n].copy()  # outro lands on the end card
fi, fo = int(0.25 * SR), int(3.0 * SR); bed[:fi] *= np.linspace(0, 1, fi)[:, None]; bed[n - fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
place(mus, bed, 0, -4)
lib = {"whoosh": S.whoosh(0.8, 400, 5000), "whoosh_soft": S.whoosh(0.6, 600, 3500), "impact": S.impact(2.4), "shimmer": S.shimmer(1.8), "click": S.click()}
for c in TL["sfx"]:
    x = S.riser(c["dur"]) if c["name"] == "riser" else lib[c["name"]]
    place(fx, x, c["t"], c["gain"])
mix = vo + mus * duck_curve(vo, -10, 0.06, 0.5) + fx
mix /= max(1.0, np.abs(mix).max() / 0.89)
wf.write(A + r"\mix_raw.wav", SR, mix.astype(np.float32))
json.dump(caps, open(os.path.join(ROOT, r"edit\captions.json"), "w"), indent=1)
print("peak dB", round(20 * np.log10(np.abs(mix).max()), 2), "lines", len(caps))
if "--diag" in sys.argv:
    speech = np.abs(vo).max(1) > 0.02
    d = duck_curve(vo, -10, 0.06, 0.5)
    r = lambda x, m: 20 * np.log10(np.sqrt((x[m] ** 2).mean()) + 1e-9)
    print("VO rms in speech", round(r(vo, speech), 1), "| music under speech", round(r(mus * d, speech), 1), "| music in gaps", round(r(mus * d, ~speech), 1), "| sfx overall", round(r(fx, np.abs(fx).max(1) > 1e-4), 1))
