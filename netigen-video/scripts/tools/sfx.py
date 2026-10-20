# Procedural SFX at 48 kHz stereo, float32 in [-1, 1]. numpy + scipy only.
import numpy as np, scipy.signal as sg, scipy.io.wavfile as wf, sys, os
SR = 48000
rng = np.random.default_rng(7)
def env(n, a, r):  # linear attack, exponential release
    t = np.arange(n) / SR; e = np.minimum(t / max(a, 1e-4), 1.0)
    return e * np.exp(-np.maximum(t - a, 0) / max(r, 1e-4))
def sweep_bp(x, f0, f1, q=2.0, block=512):  # band-pass whose centre glides f0->f1 (log)
    out = np.zeros_like(x); zi = None
    fc = np.geomspace(f0, f1, int(np.ceil(len(x) / block)))
    for i, f in enumerate(fc):
        b, a = sg.iirpeak(min(f, SR / 2 * 0.95), q, SR)
        seg = x[i * block:(i + 1) * block]
        if zi is None: zi = sg.lfilter_zi(b, a) * 0
        y, zi = sg.lfilter(b, a, seg, zi=zi); out[i * block:i * block + len(seg)] = y
    return out
def stereo(m, width=0.0, pan=0.0):
    d = int(0.012 * SR * width); r = np.roll(m, d) if d else m
    return np.stack([m * (1 - max(pan, 0)), r * (1 + min(pan, 0))], 1)
def norm(x, peak_db=-3): return x / (np.abs(x).max() + 1e-9) * 10 ** (peak_db / 20)
def whoosh(dur=0.9, f0=300, f1=4000):
    n = int(dur * SR); x = sweep_bp(rng.standard_normal(n), f0, f1, q=1.5)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2; return norm(stereo(x * e, width=1.0))
def riser(dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    tone = sum(np.sin(2 * np.pi * np.cumsum(np.geomspace(f, f * 4, n)) / SR) / k for k, f in enumerate([110, 165, 220], 1))
    noise = sweep_bp(rng.standard_normal(n), 400, 9000, q=1.2)
    e = (t / dur) ** 2.2; return norm(stereo((0.6 * tone + 0.8 * noise) * e, width=0.8))
def impact(dur=2.2):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 32 + 58 * np.exp(-t / 0.08)                       # pitch drop 90 -> 32 Hz
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.7)
    hit = sg.lfilter(*sg.butter(2, 2500, 'low', fs=SR), rng.standard_normal(n)) * env(n, 0.001, 0.06)
    return norm(stereo(np.tanh(2.2 * boom) + 0.5 * hit, width=0.3), -1)
def click(dur=0.06, f=2400):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * env(n, 0.0005, 0.008) + 0.3 * rng.standard_normal(n) * env(n, 0.0002, 0.002)
    return norm(stereo(x), -9)
def shimmer(dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in [1318.5, 1760, 2637, 3520]) * env(n, 0.02, 0.5)
    return norm(stereo(x, width=1.0), -12)
if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for name, fn in dict(whoosh=whoosh, riser=riser, impact=impact, click=click, shimmer=shimmer).items():
        y = fn(); wf.write(os.path.join(out, f"{name}.wav"), SR, y.astype(np.float32)); print(name, round(len(y) / SR, 2), "s")
