# HyperFrames page builder for the launch film: one GSAP timeline, real captures as camera-moved plates.
import json, html, os

ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder


class Film:
    def __init__(self, fmt, W, H, duration):
        self.fmt, self.W, self.H, self.dur = fmt, W, H, duration
        self.els, self.js, self.n, self.kids, self.wout = [], [], 0, {}, {}

    def uid(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def add(self, s):
        self.els.append(s)

    def tl(self, s):
        self.js.append(s)

    # --- containers -------------------------------------------------------
    def window(self, x, y, w, h, t_in, t_out, radius=22, frame=True, enter="rise", exit_="fade", tilt=None, z=10):
        """An untimed box the plates live in; shown between t_in and t_out by opacity."""
        wid = self.uid("win")
        cls = "win framed" if frame else "win"
        self.kids[wid] = []
        self.wout[wid] = t_out
        self.add(f'<div id="{wid}" class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;border-radius:{radius}px;z-index:{z}"><div class="win-inner">@@{wid}@@</div></div>')
        frm = {"opacity": 0}
        if enter == "rise":
            frm.update(y=40, scale=0.965)
        elif enter == "zoom":
            frm.update(scale=1.08)
        if tilt:
            self.tl(f'gsap.set("#{wid}", {{transformPerspective: 2200, rotationY: {tilt[0]}, rotationX: {tilt[1]}}});')
        self.tl(f'tl.fromTo("#{wid}", {json.dumps(frm)}, {{opacity: 1, y: 0, scale: 1, duration: 0.7, ease: "expo.out"}}, {max(t_in - 0.06, 0):.3f});')
        if exit_ == "fade":  # overlaps the next scene's entrance so no frame is empty
            self.tl(f'tl.to("#{wid}", {{opacity: 0, y: -24, scale: 0.98, duration: 0.4, ease: "power2.in"}}, {t_out - 0.25:.3f});')
        elif exit_ == "cut":
            self.tl(f'tl.set("#{wid}", {{opacity: 0}}, {t_out:.3f});')
        return wid

    # --- plates (real captures) --------------------------------------------
    def plate(self, win, ww, wh, src, sw, sh, t0, t1, keys, video=False, xfade=0.28, dim=0.0, tag=None):
        """A capture inside a window. keys: [(t, cx, cy, z, ease)] in film time; (cx, cy) in capture CSS px."""
        pid = self.uid("pl")
        s0 = max(ww / sw, wh / sh)
        if video:
            media = (f'<video id="{pid}v" class="media" src="{src}" muted playsinline data-start="{t0:.3f}" '
                     f'data-duration="{t1 - t0:.3f}" data-track-index="2" style="width:{sw}px;height:{sh}px"></video>')
        else:
            media = f'<img class="media" src="{src}" style="width:{sw}px;height:{sh}px" alt="" />'
        dimdiv = f'<div class="dim" style="opacity:{dim}"></div>' if dim else ""
        self.els_insert(win, f'<div id="{pid}" class="plate" style="width:{sw}px;height:{sh}px;opacity:0">{media}{dimdiv}</div>')

        def xf(cx, cy, z):
            s = s0 * z
            x, y = ww / 2 - cx * s, wh / 2 - cy * s
            x = min(0, max(ww - sw * s, x)) if sw * s >= ww else (ww - sw * s) / 2
            y = min(0, max(wh - sh * s, y)) if sh * s >= wh else (wh - sh * s) / 2
            return round(x, 2), round(y, 2), round(s, 5)

        x, y, s = xf(*keys[0][1:4])
        self.tl(f'tl.set("#{pid}", {{x: {x}, y: {y}, scale: {s}}}, 0);')
        self.tl(f'tl.to("#{pid}", {{opacity: 1, duration: {xfade}, ease: "none"}}, {max(t0 - 0.06, 0):.3f});')
        if t1 < self.wout.get(win, 1e9) - 0.01:  # the window's own exit hides its last plate
            self.tl(f'tl.to("#{pid}", {{opacity: 0, duration: {xfade}, ease: "none"}}, {t1 - xfade:.3f});')
        for (ta, *_), (tb, cx, cy, z, *ease) in zip(keys, keys[1:]):
            x, y, s = xf(cx, cy, z)
            e = ease[0] if ease else "power2.inOut"
            self.tl(f'tl.to("#{pid}", {{x: {x}, y: {y}, scale: {s}, duration: {tb - ta:.3f}, ease: "{e}"}}, {ta:.3f});')
        if tag:
            tid = self.uid("tag")
            self.els_insert(win, f'<div id="{tid}" class="tag">{html.escape(tag)}</div>')
            self.tl(f'tl.fromTo("#{tid}", {{opacity: 0}}, {{opacity: 1, duration: 0.25}}, {t0 + 0.1:.3f}); tl.to("#{tid}", {{opacity: 0, duration: 0.2}}, {t1 - 0.25:.3f});')
        return pid, xf

    def els_insert(self, win, s):
        self.kids[win].append(s)

    # --- type -------------------------------------------------------------
    def words(self, lines, x, y, w, size, t_out, align="left", lh=1.04, z=30, cls="hl", serif_scale=1.14, exit_dur=0.4):
        """lines: [[(text, 'sans'|'serif', t), ...], ...]; each word rises out of a blur at its time."""
        hid = self.uid("hl")
        rows = []
        for line in lines:
            spans = []
            for text, style, t in line:
                for k, word in enumerate(text.split()):
                    sid = self.uid("w")
                    fs = size * (serif_scale if style == "serif" else 1)
                    spans.append(f'<span id="{sid}" class="wd {style}" style="font-size:{fs:.0f}px">{html.escape(word)}</span>')
                    self.tl(f'tl.fromTo("#{sid}", {{opacity: 0, y: {size * 0.3:.0f}, filter: "blur(12px)"}}, {{opacity: 1, y: 0, filter: "blur(0px)", duration: 0.65, ease: "expo.out"}}, {t + 0.06 * k:.3f});')
            rows.append(f'<div class="row">{" ".join(spans)}</div>')
        self.add(f'<div id="{hid}" class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;text-align:{align};line-height:{lh};z-index:{z}">{"".join(rows)}</div>')
        if t_out is not None:
            self.tl(f'tl.to("#{hid}", {{opacity: 0, y: -20, filter: "blur(10px)", duration: {exit_dur}, ease: "power2.in"}}, {t_out - exit_dur:.3f});')
        return hid

    def text(self, s, x, y, w, t_in, t_out, cls, align="left", z=30, anim="rise"):
        tid = self.uid("tx")
        self.add(f'<div id="{tid}" class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;text-align:{align};z-index:{z};opacity:0">{s}</div>')
        frm = {"opacity": 0, "y": 16} if anim == "rise" else {"opacity": 0}
        self.tl(f'tl.fromTo("#{tid}", {json.dumps(frm)}, {{opacity: 1, y: 0, duration: 0.55, ease: "expo.out"}}, {t_in:.3f});')
        if t_out is not None:  # never before its own entrance has finished, or the entrance wins and it stays
            self.tl(f'tl.to("#{tid}", {{opacity: 0, duration: 0.35, ease: "power1.in"}}, {max(t_out - 0.35, t_in + 0.6):.3f});')
        return tid

    def captions(self, caps, ids, x, y, w, size, max_words=6):
        """Phrase captions from the VO's word times; spoken words brighten as they are said."""
        chunks = []
        for c in caps:
            if c["id"] not in ids:
                continue
            ws, cur, mine = c["words"], [], []
            for k, wd in enumerate(ws):  # break at punctuation, else at max_words, never strand one word
                cur.append(wd)
                left = len(ws) - k - 1
                if (wd["word"][-1] in ".,:" and len(cur) >= 2 and left != 1) or (len(cur) >= max_words and left > 1):
                    mine.append(cur); cur = []
            if cur:
                mine.append(cur)
            if len(mine) > 1 and len(mine[-1]) == 1:
                mine[-2] += mine.pop()
            chunks += mine
        chunks.sort(key=lambda ch: ch[0]["start"])
        for i, ch in enumerate(chunks):
            t0 = ch[0]["start"] - 0.12
            nxt = chunks[i + 1][0]["start"] - 0.12 if i + 1 < len(chunks) else 1e9
            t1 = min(ch[-1]["end"] + 0.45, nxt)
            cid = self.uid("cap")
            spans = "".join(f'<span id="{cid}w{k}" class="cw">{html.escape(wd["word"])}</span> ' for k, wd in enumerate(ch))
            self.add(f'<div id="{cid}" class="cap" style="left:{x}px;top:{y}px;width:{w}px;font-size:{size}px;opacity:0">{spans}</div>')
            self.tl(f'tl.fromTo("#{cid}", {{opacity: 0, y: 10}}, {{opacity: 1, y: 0, duration: 0.18, ease: "power2.out"}}, {t0:.3f});')
            if t1 >= nxt - 0.21:  # gone before the next phrase arrives
                self.tl(f'tl.set("#{cid}", {{opacity: 0}}, {nxt - 0.01:.3f});')
            else:
                self.tl(f'tl.to("#{cid}", {{opacity: 0, duration: 0.2, ease: "none"}}, {t1:.3f});')
            for k, wd in enumerate(ch):
                self.tl(f'tl.to("#{cid}w{k}", {{opacity: 1, duration: 0.12, ease: "none"}}, {wd["start"]:.3f});')

    # --- page -------------------------------------------------------------
    def body(self):
        out = chr(10).join(self.els)
        for wid, kids in self.kids.items():
            out = out.replace(f"@@{wid}@@", "".join(kids))
        return out

    def page(self, css, audio):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={self.W}, height={self.H}" />
<title>Netigen launch film</title>
<script src="assets/lib/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{self.dur}" data-width="{self.W}" data-height="{self.H}" data-fps="30">
{self.body()}
<audio id="mix" src="{audio}" data-start="0" data-duration="{self.dur}" data-track-index="9" data-volume="1"></audio>
</div>
<script>
document.fonts.ready.then(() => {{
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
tl.set({{}}, {{}}, {self.dur});
window.__timelines["main"] = tl;
}});
</script>
</body>
</html>
"""
