# Turns each planned shot into a ready plate for one canvas: images rotated, sized and blur-filled when the aspect
# differs; videos tone-mapped to SDR when HDR, optionally stabilised, trimmed, speed-set, cropped on their focus point and padded to the slot. Originals are never changed.
# Usage: prepare.py <fmt> [shot ids]   (writes <project>/assets/shots/ and edit/prepared_<fmt>.json; audio/clips/ for keep_audio)
import json, os, subprocess, sys
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from formats import project_dir, window_rect
from ffbin import ROOT, ffmpeg

HEAD = 1.12  # plate size over the window, so pushes and pans never show an edge


def even(v):
    return int(round(v / 2) * 2)


def fit_of(s, ww, wh):
    if s.get("fit", "auto") != "auto":
        return s["fit"]
    r = (s["w"] / s["h"]) / (ww / wh)
    return "cover" if 0.72 <= r <= 1.4 else "contain"  # a big aspect mismatch would crop away too much


def blur_img(im, boxes):
    """boxes: [[x, y, w, h], ...] as fractions of the source picture."""
    for x, y, w, h in boxes:
        b = (int(x * im.width), int(y * im.height), int((x + w) * im.width), int((y + h) * im.height))
        im.paste(im.crop(b).filter(ImageFilter.GaussianBlur(max(8, im.width // 120))), b[:2])
    return im


def prep_image(s, ww, wh, fit, dark, out):
    im = blur_img(ImageOps.exif_transpose(Image.open(s["src"])).convert("RGB"), s.get("blur", []))
    if fit == "cover":
        f = max(ww / im.width, wh / im.height) * HEAD * 1.15
        if f < 1:  # downscale big photos; never upscale here (the browser scales the plate)
            im = im.resize((round(im.width * f), round(im.height * f)), Image.LANCZOS)
        res = im
    else:
        CW, CH = even(ww * HEAD), even(wh * HEAD)
        bg = ImageOps.fit(im, (CW // 6, CH // 6)).filter(ImageFilter.GaussianBlur(6)).resize((CW, CH), Image.BICUBIC)
        bg = ImageEnhance.Brightness(bg).enhance(0.5 if dark else 1.08)
        fg = ImageOps.contain(im, (round(CW * 0.9), round(CH * 0.9)), Image.LANCZOS)
        bg.paste(fg, ((CW - fg.width) // 2, (CH - fg.height) // 2))
        res = bg
    res.save(out, quality=92, subsampling=0)
    return res.size


def is_hdr(src):
    """iPhone clips are usually HLG (BT.2020). Left as is, HyperFrames promotes the whole render to 10-bit HDR HEVC."""
    r = subprocess.run([ffmpeg(), "-hide_banner", "-i", src], capture_output=True, text=True, errors="replace")  # no ffprobe needed
    return any(t in r.stderr for t in ("arib-std-b67", "smpte2084"))


TONEMAP = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,")


def stab_pass(s, need, sp):
    """Pass 1 of vidstab on the trimmed clip; returns the transform filter for pass 2 (handheld shake out, moves kept)."""
    d = os.path.join(ROOT, "edit", "stab")
    os.makedirs(d, exist_ok=True)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f'{s.get("in", 0):.3f}', "-t", f"{need * sp + 0.5:.3f}", "-i", s["src"],
                    "-vf", f'vidstabdetect=shakiness=6:accuracy=15:result={s["id"]}.trf', "-f", "null", "-"], check=True, cwd=d)
    return f'vidstabtransform=input={s["id"]}.trf:smoothing={s.get("stab_smooth", 24)}:optzoom=1:zoomspeed=0.2:interpol=bicubic,', d


def prep_video(s, ww, wh, fit, dark, out):
    need = s["end"] - s["start"] + s.get("xf", 0)
    sp = float(s.get("speed", 1.0))
    CW, CH = even(ww * HEAD), even(wh * HEAD)
    fx, fy = s.get("focus", [0.5, 0.5])
    tm = TONEMAP if is_hdr(s["src"]) else ""
    st, cwd = stab_pass(s, need, sp) if s.get("stabilize") else ("", None)
    chain, last = [f"[0:v]{st}{tm}setpts=(PTS-STARTPTS)/{sp:.5f}[v0]"], "v0"
    for i, (x, y, w, h) in enumerate(s.get("blur", [])):
        chain.append(f"[{last}]split[a{i}][b{i}];[b{i}]crop=iw*{w}:ih*{h}:iw*{x}:ih*{y},gblur=sigma=20:steps=3[c{i}];"
                     f"[a{i}][c{i}]overlay=main_w*{x}:main_h*{y}[v{i + 1}]")
        last = f"v{i + 1}"
    if fit == "cover":
        chain.append(f"[{last}]scale={CW}:{CH}:force_original_aspect_ratio=increase:flags=lanczos,"
                     f"crop={CW}:{CH}:(in_w-out_w)*{fx}:(in_h-out_h)*{fy}[p]")
    else:
        bri = -0.22 if dark else 0.06
        chain.append(f"[{last}]split[m][n];[m]scale={CW // 4}:{CH // 4}:force_original_aspect_ratio=increase,crop={CW // 4}:{CH // 4},"
                     f"gblur=sigma=8,scale={CW}:{CH},eq=brightness={bri}[bg];"
                     f"[n]scale={even(CW * 0.9)}:{even(CH * 0.9)}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos[fg];"
                     f"[bg][fg]overlay=(W-w)/2:(H-h)/2[p]")
    chain.append(f"[p]fps=30,tpad=stop_mode=clone:stop_duration={need:.3f},format=yuv420p[out]")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f'{s.get("in", 0):.3f}', "-t", f"{need * sp + 0.5:.3f}", "-i", s["src"],
                    "-filter_complex", ";".join(chain), "-map", "[out]", "-t", f"{need:.3f}",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-g", "30", "-keyint_min", "30",  # dense keyframes seek cleanly
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-an", "-movflags", "+faststart", out], check=True, cwd=cwd)
    if s.get("keep_audio") and s.get("audio"):  # format-independent; build_audio.py places it on the film clock
        os.makedirs(os.path.join(ROOT, "audio", "clips"), exist_ok=True)
        tempo = [] if abs(sp - 1) < 1e-3 else [f"atempo={min(max(sp, 0.5), 2.0)}"]
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-ss", f'{s.get("in", 0):.3f}', "-t", f"{need * sp:.3f}", "-i", s["src"],
                        "-vn", "-af", ",".join(tempo + ["aresample=48000"]), "-ac", "2", "-c:a", "pcm_s16le",
                        os.path.join(ROOT, "audio", "clips", s["id"] + ".wav")], check=True)
    return CW, CH


if __name__ == "__main__":
    fmt, only = sys.argv[1], set(sys.argv[2:])
    TL = json.load(open(os.path.join(ROOT, "edit", "timeline.json"), encoding="utf-8"))
    for s in TL["shots"]:  # per-format overrides, e.g. "land": {"focus": [...], "src": ...}
        s.update(s.get(fmt) or {})
    _, _, ww, wh = window_rect(fmt, TL.get("look", "fullbleed"))
    dark = TL.get("theme", "dark") == "dark"
    base = os.path.join(project_dir(ROOT, fmt), "assets", "shots")
    os.makedirs(base, exist_ok=True)
    mpath = os.path.join(ROOT, "edit", f"prepared_{fmt}.json")
    man = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) and only else {}
    for s in TL["shots"]:
        if only and s["id"] not in only:
            continue
        fit = fit_of(s, ww, wh)
        ext = "mp4" if s["kind"] == "video" else "jpg"
        out = os.path.join(base, f'{s["id"]}.{ext}')
        w, h = (prep_video if s["kind"] == "video" else prep_image)(s, ww, wh, fit, dark, out)
        man[s["id"]] = {"file": f'assets/shots/{s["id"]}.{ext}', "w": w, "h": h, "kind": s["kind"], "fit": fit}
        print(s["id"], fit, f"{w}x{h}", os.path.basename(s["src"]), flush=True)
    json.dump(man, open(mpath, "w", encoding="utf-8"), indent=1)
    print(mpath)
