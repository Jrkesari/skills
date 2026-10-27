# Writes an .srt from the voiceover captions (edit/captions.json), or from the on-screen texts when there is no voiceover.
# Usage: srt.py deliver/<name>.srt
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffbin import ROOT


def ts(t):
    ms = int(round(max(t, 0) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


TL = json.load(open(os.path.join(ROOT, "edit", "timeline.json"), encoding="utf-8"))
cap = os.path.join(ROOT, "edit", "captions.json")
if TL.get("vo") and os.path.exists(cap):
    rows = [(c["start"], c["end"] + 0.35, c["text"]) for c in json.load(open(cap, encoding="utf-8"))]
else:
    rows = [(t["start"], t["end"], t["text"].replace("*", "")) for t in TL.get("texts", [])]
rows.sort()
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as fh:
    for i, (a, b, text) in enumerate(rows, 1):
        fh.write(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n\n")
print(sys.argv[1], len(rows), "cues")
