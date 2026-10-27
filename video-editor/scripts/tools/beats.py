# Beat grid of the user's song, so cuts land on the music: tempo, beats, downbeats, bar loudness and lifts.
# Usage: beats.py <song> [--out audio/beats.json] [--bpm 96]   (any format ffmpeg reads; --bpm overrides a wrong tempo guess)
import json, os, subprocess, sys, tempfile
import numpy as np, scipy.io.wavfile as wf, scipy.signal as sg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ffbin import ROOT, ffmpeg

SR, HOP, NFFT = 22050, 512, 2048
FR = SR / HOP  # onset frames per second


def load_mono(path):
    tmp = os.path.join(tempfile.mkdtemp(), "song.wav")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", tmp], check=True)
    sr, x = wf.read(tmp)
    return x.astype(np.float32) / 32768


def onset_env(x):
    f, _, Z = sg.stft(x, SR, nperseg=NFFT, noverlap=NFFT - HOP)  # zero-padded ends: frame k is centred on k * HOP
    M = np.abs(Z)
    edges = np.geomspace(30, 11000, 65)  # log-spaced bands (mel-like), so the kick weighs as much as the hats
    B = np.stack([M[(f >= a) & (f < b)].mean(0) if ((f >= a) & (f < b)).any() else np.zeros(M.shape[1])
                  for a, b in zip(edges[:-1], edges[1:])])
    d = np.maximum(0, np.diff(np.log1p(100 * B), axis=1))
    full = np.concatenate([[0], d.sum(0)])
    low = np.concatenate([[0], d[edges[1:] <= 160].sum(0)])  # kick drum bands, for beat phase and downbeats
    full = np.maximum(0, full - np.convolve(full, np.ones(16) / 16, "same"))
    return full / (full.std() + 1e-9), low, np.abs(Z).mean(0)


def tempo(o, lo=60, hi=180):
    n = len(o)
    ac = np.fft.irfft(np.abs(np.fft.rfft(o - o.mean(), 2 * n)) ** 2)[:n]
    lags = np.arange(int(60 * FR / hi), int(60 * FR / lo) + 1)
    bpm = 60 * FR / lags
    score = ac[lags] * np.exp(-0.5 * (np.log2(bpm / 115) / 0.9) ** 2)  # mild prior towards ~115 bpm
    k = int(np.argmax(score))
    if 0 < k < len(lags) - 1:  # parabolic refinement of the peak lag
        a, b, c = score[k - 1], score[k], score[k + 1]
        lag = lags[k] + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    else:
        lag = lags[k]
    return 60 * FR / lag


def track(o, bpm, tight=100.0):
    """Dynamic-programming beat tracker (Ellis 2007): each beat is the best previous beat about one period back."""
    p = 60 * FR / bpm
    n = len(o)
    C, P = o.astype(float).copy(), np.full(n, -1)
    lo, hi = max(1, int(round(p / 2))), int(round(2 * p))
    for i in range(lo, n):
        js = np.arange(max(0, i - hi), i - lo + 1)
        sc = C[js] - tight * np.log((i - js) / p) ** 2
        k = int(np.argmax(sc))
        C[i] = o[i] + sc[k]
        P[i] = js[k]
    i = n - int(p) + int(np.argmax(C[n - int(p):]))
    out = []
    while i >= 0:
        out.append(i)
        i = P[i]
    return np.array(out[::-1])


if __name__ == "__main__":
    a = sys.argv[1:]
    src = a[0]
    dst = a[a.index("--out") + 1] if "--out" in a else os.path.join(ROOT, "audio", "beats.json")
    x = load_mono(src)
    o, low, mag = onset_env(x)
    bpm = float(a[a.index("--bpm") + 1]) if "--bpm" in a else tempo(o)
    fr = track(o, bpm)
    half = int(round(30 * FR / bpm))  # locked onto the off-beat (hats) when the kick sits half a beat away
    pk = lambda i: np.max([low[np.clip(i + k, 0, len(low) - 1)] for k in range(-2, 3)], 0)  # peak within +-2 frames
    off = fr + half
    if pk(off).sum() > 1.3 * pk(fr).sum():
        fr = off[off < len(low)]
    rms = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(HOP) / HOP, "same")[::HOP]) + 1e-9)
    loud = np.nonzero(rms > rms.max() - 40)[0]
    first, last = loud[0] / FR, loud[-1] / FR  # skip beats in leading/trailing silence
    fr = fr[(fr / FR >= first - 0.05) & (fr / FR <= last + 0.05)]
    keep = [fr[0]]
    for b in fr[1:]:  # drop strays closer than 0.7 of a beat to the previous one
        if b - keep[-1] >= 0.7 * 60 * FR / bpm:
            keep.append(b)
    if len(keep) > 1 and keep[1] - keep[0] < 0.9 * 60 * FR / bpm:
        keep = keep[1:]
    fr = np.array(keep)
    beats = fr / FR
    phase = int(np.argmax([pk(fr[ph::4]).mean() for ph in range(4)]))
    downs = beats[phase::4]
    bars = []
    for t0, t1 in zip(downs, list(downs[1:]) + [len(x) / SR]):
        if t1 - t0 < 3 * 60 / bpm:  # a partial last bar would read as a false lift or drop
            continue
        seg = x[int(t0 * SR):int(t1 * SR)]
        bars.append([round(float(t0), 3), round(float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)), 1)])
    lifts = [b[0] for k, b in enumerate(bars) if k >= 4 and b[1] - np.mean([e for _, e in bars[k - 4:k]]) > 3.0]
    out = {"song": os.path.abspath(src).replace("\\", "/"), "duration": round(len(x) / SR, 3), "tempo": round(bpm, 2),
           "beats": [round(float(b), 3) for b in beats], "downbeats": [round(float(d), 3) for d in downs],
           "bars": bars, "lifts": lifts}
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    json.dump(out, open(dst, "w", encoding="utf-8"), indent=1)
    print(f"{out['duration']} s, {out['tempo']} bpm, {len(beats)} beats, {len(downs)} bars, first beat {beats[0]:.2f} s, lifts at {lifts[:8]}")
    print(dst)
