# Mix VO + music + SFX at 48 kHz with sidechain ducking; writes float WAV for loudnorm/mux.
import numpy as np, scipy.io.wavfile as wf, scipy.signal as sg, sys
SR = 48000
def load(p):
    sr, x = wf.read(p)
    x = x.astype(np.float32) / (np.iinfo(x.dtype).max if x.dtype.kind == "i" else 1)
    if x.ndim == 1: x = np.stack([x, x], 1)
    return sg.resample_poly(x, SR, sr, axis=0).astype(np.float32) if sr != SR else x
def place(bus, x, t, gain_db=0):
    i = int(t * SR); j = min(len(bus), i + len(x)); bus[i:j] += x[:j - i] * 10 ** (gain_db / 20)
def duck_curve(vo, depth_db=-9, att=0.08, rel=0.45):  # music gain follows VO presence
    lvl = np.abs(vo).max(1); hop = int(0.01 * SR)
    on = np.array([lvl[i:i + hop].max() > 0.02 for i in range(0, len(lvl), hop)], float)
    g = np.empty_like(on); a, r = np.exp(-0.01 / att), np.exp(-0.01 / rel); s = 0
    for k, v in enumerate(on): s = (a if v > s else r) * s + (1 - (a if v > s else r)) * v; g[k] = s
    return np.repeat(10 ** (depth_db * g / 20), hop)[:len(vo)][:, None]
def fade(x, fin=0.5, fout=1.5):
    n1, n2 = int(fin * SR), int(fout * SR)
    if n1: x[:n1] *= np.linspace(0, 1, n1)[:, None]
    if n2: x[-n2:] *= np.linspace(1, 0, n2)[:, None]
    return x
if __name__ == "__main__":  # demo: python mix.py out.wav vo.wav music.wav impact.wav
    out, vo_p, mus_p, sfx_p = sys.argv[1:5]; dur = 9.0; n = int(dur * SR)
    vo, mus, sfx = (np.zeros((n, 2), np.float32) for _ in range(3))
    place(vo, load(vo_p), 1.0); place(mus, fade(load(mus_p)[:n].copy(), 0.3, 1.0), 0, -6); place(sfx, load(sfx_p), 0.6, -8)
    mix = vo + mus * duck_curve(vo) + sfx
    mix /= max(1.0, np.abs(mix).max() / 0.89); wf.write(out, SR, mix.astype(np.float32)); print("peak", round(20 * np.log10(np.abs(mix).max()), 1))
