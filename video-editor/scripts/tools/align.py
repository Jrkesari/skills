# Optional voiceover: word timestamps for a known script (whisper times, script spelling).
# Usage: align.py take.wav "script text" [model]   or   align.py take.wav --lines lines.json --out vo_timing.json [model]
# VO_NAMES: comma-separated proper names in the script, passed to whisper as a hint ("Aanya, Goa, Kesari").
import os, sys, json, re, difflib, numpy as np, scipy.io.wavfile as wf, scipy.signal as sg, whisper
def load16k(p):
    sr, x = wf.read(p); x = x.astype(np.float32) / (32768 if x.dtype == np.int16 else 1)
    x = x.mean(1) if x.ndim == 2 else x
    return sg.resample_poly(x, 16000, sr).astype(np.float32)
def align(wav, script, model="small.en", names=os.environ.get("VO_NAMES", "")):
    m = whisper.load_model(model)
    r = m.transcribe(load16k(wav), language="en", word_timestamps=True, fp16=False, initial_prompt=names or None, condition_on_previous_text=False)
    heard = [w for s in r["segments"] for w in s["words"]]
    key = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    sw = script.split(); out = [None] * len(sw)
    sm = difflib.SequenceMatcher(None, [key(w) for w in sw], [key(w["word"]) for w in heard], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):  # one heard word per script word
            for n in range(i2 - i1): out[i1 + n] = dict(word=sw[i1 + n], start=round(heard[j1 + n]["start"], 3), end=round(heard[j1 + n]["end"], 3))
        elif op == "replace":  # unequal spans: spread the heard time evenly
            t0, t1 = heard[j1]["start"], heard[j2 - 1]["end"]; k = i2 - i1
            for n in range(k): out[i1 + n] = dict(word=sw[i1 + n], start=round(t0 + (t1 - t0) * n / k, 3), end=round(t0 + (t1 - t0) * (n + 1) / k, 3))
    for i, w in enumerate(out):  # words whisper missed: interpolate from neighbours
        if w is None:
            p = next((out[j]["end"] for j in range(i - 1, -1, -1) if out[j]), 0.0)
            q = next((out[j]["start"] for j in range(i + 1, len(out)) if out[j]), p)
            out[i] = dict(word=sw[i], start=p, end=q)
    return out
def per_line(wav, lines, model="small.en"):
    """Split one whole-script take into vo_timing records {id, text, start, end, words} by each line's word count."""
    words, out, i = align(wav, " ".join(l["text"] for l in lines), model), [], 0
    for l in lines:
        ws = words[i:i + len(l["text"].split())]; i += len(ws)
        out.append({"id": l["id"], "text": l["text"], "start": ws[0]["start"], "end": ws[-1]["end"], "words": ws})
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--lines" in a:
        lines = json.load(open(a[a.index("--lines") + 1], encoding="utf-8")); dst = a[a.index("--out") + 1]
        rest = [x for x in a[1:] if x not in ("--lines", "--out", a[a.index("--lines") + 1], dst)]
        json.dump(per_line(a[0], lines, *rest), open(dst, "w", encoding="utf-8"), indent=1); print(dst)
    else:
        print(json.dumps(align(*a), indent=0))
