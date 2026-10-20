# Writes index.html for both films from one story; layouts differ per canvas. Usage: build.py land|port
import json, os, sys
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.dirname(__file__))
from engine import Film, ROOT
from formats import FORMATS, layout_of, project_dir

fmt = sys.argv[1]
TL = json.load(open(os.path.join(ROOT, "edit", "timeline.json")))
CAPS = json.load(open(os.path.join(ROOT, "edit", "captions.json")))
W_ = {}
for c in CAPS:
    for w in c["words"]:
        W_.setdefault(c["id"], {}).setdefault(w["word"].strip(".,").lower(), w["start"])  # first occurrence
MARK = open(os.path.join(ROOT, "shared", "netigen-mark.svg")).read()
PATHS = MARK[MARK.index("<path"):MARK.index("</svg>")]
# Layout constants below are written for 1920x1080 (land) and 1080x1920 (port). For another canvas,
# re-place windows, header and captions for its W x H and check every scene in snapshots.
LAND = layout_of(fmt) == "land"
W, H = FORMATS[fmt]
f = Film(fmt, W, H, TL["duration"])
SCN = {s["id"]: (s["start"], s["end"]) for s in TL["scenes"]}
SRC = FORMATS[fmt]                                    # capture CSS size for this format's takes
LS, PS, WSZ = (1920, 1080), (1080, 1920), (796, 440)   # WSZ: a netigen.ai product scene's stage


def t(line, word):
    return W_[line][word]


def clip(name): return f"assets/clips/{name}.mp4"


MEDIA = {c["name"]: c for c in json.load(open(os.path.join(ROOT, "edit", "media.json")))[fmt]["clips"]}


def clip_at(name, event, start=None):
    """Film time at which a take's event shows in its clip; start is the clip's film start (default: its scene's start)."""
    import re
    c = MEDIA[name]; ev = {lab: tt for tt, lab in json.load(open(os.path.join(ROOT, "capture", "takes", c["take"] + ".json")))["events"]}
    def t_of(spec):
        m = re.match(r"([a-z0-9-]+?)([+-][\d.]+)?$", spec)
        return ev[m.group(1)] + float(m.group(2) or 0)
    i0, i1 = t_of(c["in"]), t_of(c["out"])
    return (start if start is not None else SCN[c.get("scene", "naper")][0]) + (ev[event] - i0) * c["dur"] / (i1 - i0)
def still(name): return f"assets/stills/{name}.jpg"


def plate_s(win, ww, wh, src, sw, sh, t0, t1, keys, **kw):
    """Like Film.plate but keys carry absolute scale s instead of zoom."""
    s0 = max(ww / sw, wh / sh)
    return f.plate(win, ww, wh, src, sw, sh, t0, t1, [(k[0], k[1], k[2], k[3] / s0) + tuple(k[4:]) for k in keys], **kw)


def header(kicker_html, t_in, t_out, x, y):
    hid = f.uid("hdr")
    f.add(f'<div id="{hid}" class="hdr" style="left:{x}px;top:{y}px"><div class="m">{MARK}</div><div class="k">{kicker_html}</div></div>')
    f.tl(f'tl.fromTo("#{hid}", {{opacity: 0, x: -14}}, {{opacity: 1, x: 0, duration: 0.6, ease: "expo.out"}}, {t_in:.3f});')
    f.tl(f'tl.to("#{hid}", {{opacity: 0, duration: 0.35}}, {t_out - 0.35:.3f});')


def chip(text, x, y, t_in, t_out, z=48):
    cid = f.uid("chip")
    f.add(f'<div id="{cid}" class="chip" style="left:{x}px;top:{y}px;z-index:{z};opacity:0"><i></i>{text}</div>')
    f.tl(f'tl.fromTo("#{cid}", {{opacity: 0, y: 14, scale: 0.96}}, {{opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "expo.out"}}, {t_in:.3f});')
    f.tl(f'tl.to("#{cid}", {{opacity: 0, duration: 0.3}}, {t_out - 0.3:.3f});')


def card(src, sw, sh, x, y, w, h, t_in, t_out, cx, cy, s, s2=None, dim=0.0, tilt=None, enter="rise", z=20, video=False, drift=(0, 0)):
    wid = f.window(x, y, w, h, t_in, t_out, radius=18 if LAND else 22, enter=enter, tilt=tilt, z=z)
    plate_s(wid, w, h, src, sw, sh, t_in, t_out, [(t_in, cx, cy, s), (t_out, cx + drift[0], cy + drift[1], s2 or s * 1.04, "none")], dim=dim, video=video, xfade=0.01)
    return wid


f.add('<div class="bg"></div><div class="vignette"></div><div class="grain"></div>')

# ---------------------------------------------------------------- HOOK
h0, h1 = SCN["hook"]
if LAND:
    f.words([[("Every team has", "sans", 0.5)], [("more", "sans", t("l01", "more")), ("questions", "sans", t("l01", "questions"))],
             [("than", "serif", t("l01", "than")), ("hours.", "serif", t("l01", "hours"))]], 110, 330, 860, 98, 3.95, serif_scale=1.22)
    hw = f.window(900, 210, 940, 600, 0.0, 3.95, enter="zoom", exit_="fade", tilt=(-13, 3))
    f.plate(hw, 940, 600, clip("hook_type"), *SRC, 0.0, 3.95, [(0.0, 1088, 545, 1.45), (3.95, 1088, 545, 1.62, "none")], video=True, xfade=0.01)
    f.words([[("Netigen", "sans", t("l02", "netigen")), ("turns", "sans", t("l02", "turns")), ("them", "sans", t("l02", "them")), ("into", "sans", t("l02", "into"))],
             [("finished", "serif", t("l02", "finished")), ("work.", "serif", t("l02", "work"))]], 110, 380, 860, 76, 7.45, serif_scale=1.7, lh=1.12)
    # one slot, four finished artifacts in turn: a cited answer, a deck, a scheduled task, the dashboard
    slot = f.window(960, 250, 860, 540, 3.95, 7.45, enter="rise", tilt=(-9, 2))
    seq = [("nx_research_cite_land", 1082, 326, 0.97, 1.0), ("nx_deck_preview_land", 1552, 569, 1.17, 1.23), ("nx_sched_land", 1080, 440, 0.91, 0.99), ("wsc_nim_home", 487, 220, 1.39, 1.4)]
    tt = [4.00, 4.85, 5.70, 6.55, 7.45]
    for i, (name, cx, cy, sa, sb) in enumerate(seq):
        plate_s(slot, 860, 540, still(name), *(WSZ if name.startswith("wsc_") else LS), tt[i], tt[i + 1] + (0.12 if i < 3 else 0), [(tt[i], cx, cy, sa), (tt[i + 1], cx, cy, sb, "none")], xfade=0.12)
else:
    f.words([[("Every team has", "sans", 0.5)], [("more", "sans", t("l01", "more")), ("questions", "sans", t("l01", "questions"))],
             [("than", "serif", t("l01", "than")), ("hours.", "serif", t("l01", "hours"))]], 112, 330, 860, 96, 3.95, serif_scale=1.22)
    hw = f.window(40, 760, 1000, 640, 0.0, 3.95, enter="zoom", tilt=(0, 6))
    f.plate(hw, 1000, 640, clip("hook_type"), *SRC, 0.0, 3.95, [(0.0, 668, 955, 1.32), (3.95, 668, 955, 1.45, "none")], video=True, xfade=0.01)
    f.words([[("Netigen", "sans", t("l02", "netigen")), ("turns", "sans", t("l02", "turns"))], [("them", "sans", t("l02", "them")), ("into", "sans", t("l02", "into"))],
             [("finished", "serif", t("l02", "finished")), ("work.", "serif", t("l02", "work"))]], 112, 320, 880, 90, 7.45, serif_scale=1.45, lh=1.14)
    slot = f.window(40, 760, 1000, 640, 3.95, 7.45, enter="rise", tilt=(0, 5))
    seq = [("nx_research_cite_land", 1082, 330, 1.15, 1.17), ("nx_deck_preview_port", 811, 990, 1.85, 1.95), ("nx_sched_port", 662, 420, 1.23, 1.31), ("wsc_nim_home", 487, 220, 1.62, 1.65)]
    tt = [4.00, 4.85, 5.70, 6.55, 7.45]
    for i, (name, cx, cy, sa, sb) in enumerate(seq):
        plate_s(slot, 1000, 640, still(name), *(WSZ if name.startswith("wsc_") else LS if name.endswith("_land") else PS), tt[i], tt[i + 1] + (0.12 if i < 3 else 0), [(tt[i], cx, cy, sa), (tt[i + 1], cx, cy, sb, "none")], xfade=0.12)

# ---------------------------------------------------------------- ECOSYSTEM
e0, e1 = SCN["eco"]
mx, my, ms = (960, 330, 250) if LAND else (540, 600, 300)
MP = PATHS
for i in range(3):
    MP = MP.replace("<path d=", f'<path id="mp{i}" class="mp" data-x=', 1)
MP = MP.replace("data-x=", "d=")
f.add(f'<div id="eco-mark" class="mark" style="left:{mx - ms / 2}px;top:{my - ms / 2}px;width:{ms}px;height:{ms}px;z-index:30;opacity:0">'
      f'<svg viewBox="0 0 234 233" fill="currentColor">{MP}</svg></div>')
f.tl(f'tl.set("#eco-mark", {{opacity: 1}}, {e0:.3f});')
starts = [(-260, -120, -24), (40, 240, 18), (280, -60, 30)]
for i, (dx, dy, r) in enumerate(starts):
    f.tl(f'tl.fromTo(\"#mp{i}\", {{x: {dx}, y: {dy}, rotation: {r}, opacity: 0, transformOrigin: "50% 50%"}}, {{x: 0, y: 0, rotation: 0, opacity: 1, duration: 0.9, ease: "expo.out"}}, {e0 - 0.04 + 0.1 * i:.3f});')
spread = [(-16, -6), (0, 14), (16, -4)]
for i, (dx, dy) in enumerate(spread):
    f.tl(f'tl.to(\"#mp{i}\", {{x: {dx}, y: {dy}, duration: 0.7, ease: "power3.inOut"}}, {t("l03", "four"):.3f});')
names = [("Naper", "Enterprise context", "naper", "wsc_nap_overview", (398, 220, 0.48)),
         ("Nexus", "AI workspace", "nexus", "wsc_nex_home", (398, 220, 0.48)),
         ("Neuron", "Enterprise intelligence", "neuron", "ws_neuron5", (1400, 540, 0.36)),
         ("Nimbus", "Trust &amp; observability", "nimbus", "wsc_nim_home", (398, 220, 0.48))]
for i, (nm, desc, key, th, (tx, ty, ts)) in enumerate(names):
    ti = t("l03", key)
    if ti + 0.58 < e1 - 0.55:  # no pulse once the mark is flying to the header
        f.tl(f'tl.to("#eco-mark", {{scale: 1.05, duration: 0.18, ease: "power2.out"}}, {ti:.3f}); tl.to("#eco-mark", {{scale: 1, duration: 0.4, ease: "power2.inOut"}}, {ti + 0.18:.3f});')
    for j in range(3):
        f.tl(f'tl.to(\"#mp{j}\", {{fill: "#7C3AED", duration: 0.2}}, {ti:.3f}); tl.to(\"#mp{j}\", {{fill: "#0F0E14", duration: 0.5}}, {ti + 0.3:.3f});')
    pre = t("l03", "layers") + 0.1 * i  # all four previewed on "layers", each lit on its name
    if LAND:
        cx = 300 + 440 * i
        nid = f.text(nm, cx - 210, 610, 420, pre, e1, "label", align="center")
        f.text(desc, cx - 210, 660, 420, min(ti + 0.08, e1 - 0.95), e1, "sub", align="center")
        wid = card(still(th), *(WSZ if th.startswith("wsc_") else LS), cx - 190, 716, 380, 214, pre + 0.05, e1, tx, ty, ts, ts * 1.04, dim=0.6, z=20)
        f.tl(f'tl.to("#{wid} .dim", {{opacity: 0, duration: 0.35}}, {ti:.3f});')
    else:
        y = 820 + 124 * i
        nid = f.text(nm, 0, y, W, pre, e1, "label", align="center")
        did = f.text(desc, 0, y + 50, W, min(ti + 0.08, e1 - 0.95), e1, "sub", align="center")
        f.tl(f'gsap.set("#{did}", {{fontSize: 22}});')
    f.tl(f'gsap.set("#{nid}", {{color: "#9C99A8"}}); tl.to("#{nid}", {{color: "#0F0E14", duration: 0.3}}, {ti:.3f});')
for i in range(3):
    f.tl(f'tl.to(\"#mp{i}\", {{x: 0, y: 0, duration: 0.5, ease: "power3.inOut"}}, {e1 - 0.75:.3f});')
hx, hy = (96, 52) if LAND else (112, 300)
f.tl(f'tl.to("#eco-mark", {{x: {hx + 17 - mx}, y: {hy + 17 - my}, scale: {34 / ms:.4f}, duration: 0.7, ease: "expo.inOut"}}, {e1 - 0.55:.3f});')
f.tl(f'tl.set("#eco-mark", {{opacity: 0}}, {e1 + 0.2:.3f});')

# ---------------------------------------------------------------- shared layout for product scenes
if LAND:
    WX, WY, WW, WH = 270, 128, 1380, 776
    HDR = (96, 52)
else:
    WX, WY, WW, WH = 40, 520, 1000, 780
    HDR = (112, 300)


def product(name, kicker, a, b):
    header(f"<b>{name}</b> &nbsp;·&nbsp; {kicker}", a, b, *HDR)
    if not LAND:
        f.text(name, 112, 356, 900, a + 0.05, b, "label", z=31).__str__()
        f.tl(f'gsap.set("#{f.els[-1].split(chr(34))[1]}", {{fontSize: 104, letterSpacing: "-0.045em", fontWeight: 650}});')


# ---------------------------------------------------------------- NAPER
a, b = SCN["naper"]
product("Naper", "enterprise context", a, b)
split = t("l04", "with") + 0.05      # -> seats: a new organisation's seat count
lim = t("l04", "spend") - 0.1         # -> spend limits
win = f.window(WX, WY, WW, WH, a, b, enter="rise")
tio = clip_at("np_group", "inherit-off")
if LAND:
    plate_s(win, WW, WH, clip("np_group"), *SRC, a, split + 0.15, [(a, 960, 510, 2.06), (tio, 960, 510, 2.06), (tio + 0.5, 960, 420, 2.08), (split + 0.15, 960, 660, 2.08, "none")], video=True)
    chip("Finance gets 3 of 7 agents", WX + WW - 470, WY + WH - 80, clip_at("np_group", "agents-picked") + 0.15, split + 0.1)
    plate_s(win, WW, WH, still("wsc_nap_members"), *WSZ, split, lim + 0.15, [(split, 486, 175, 2.2), (lim + 0.15, 490, 185, 2.3)])
    plate_s(win, WW, WH, still("wsc_nap_limits"), *WSZ, lim, b, [(lim, 486, 150, 2.15), (b, 486, 160, 2.2)])
else:
    plate_s(win, WW, WH, clip("np_group"), *SRC, a, split + 0.15, [(a, 540, 960, 1.43), (split + 0.15, 540, 1000, 1.45, "none")], video=True)
    chip("Finance gets 3 of 7 agents", WX + WW - 430, 392, clip_at("np_group", "agents-picked") + 0.15, split + 0.1)
    plate_s(win, WW, WH, still("wsc_nap_members"), *WSZ, split, lim + 0.15, [(split, 403, 180, 2.31), (lim + 0.15, 408, 185, 2.38)])
    plate_s(win, WW, WH, still("wsc_nap_limits"), *WSZ, lim, b, [(lim, 384, 199, 2.52), (b, 382, 199, 2.56)])

# ---------------------------------------------------------------- NEXUS
a, b = SCN["nexus"]
product("Nexus", "AI workspace", a, b)
win = f.window(WX, WY, WW, WH, a, b, enter="rise")
q0 = a + 0.05
s1 = t("l05", "your") + 0.2           # picker -> typing
s2 = t("l06", "it") - 0.25            # typing -> search time-lapse
s3 = t("l06", "cites") + 0.05         # time-lapse -> cited answer still
s4 = t("l07", "turns") + 0.05         # -> deck time-lapse
s5 = t("l07", "into") + 0.05         # -> deck preview still
s6 = t("l09", "and")                  # -> schedule
s7 = t("l09", "again") + 0.25         # -> task card still
if LAND:
    plate_s(win, WW, WH, clip("nx_pick"), *SRC, q0, s1 + 0.15, [(q0, 1160, 765, 1.25), (s1 + 0.15, 1150, 765, 1.3, "none")], video=True)
    plate_s(win, WW, WH, clip("nx_type"), *SRC, s1, s2 + 0.15, [(s1, 1088, 530, 1.5), (s2 + 0.15, 1088, 530, 1.58, "none")], video=True)
    plate_s(win, WW, WH, clip("nx_search"), *SRC, s2, s3 + 0.15, [(s2, 1100, 350, 1.3), (s3 + 0.15, 1090, 350, 1.36, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_research_cite_land"), *LS, s3, s4 + 0.15, [(s3, 1082, 340, 1.35), (s4 + 0.15, 1082, 345, 1.45)])
    plate_s(win, WW, WH, clip("nx_deck"), *SRC, s4, s5 + 0.15, [(s4, 1087, 380, 1.3), (s5 + 0.15, 1087, 390, 1.34, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_deck_preview_land"), *LS, s5, s6 + 0.15, [(s5, 1553, 569, 1.88), (s6 + 0.15, 1552, 569, 1.98)])
    plate_s(win, WW, WH, clip("nx_sched"), *SRC, s6, s7 + 0.15, [(s6, 1083, 330, 1.25), (s7 + 0.15, 1083, 380, 1.25, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_sched_land"), *LS, s7, b, [(s7, 1083, 380, 1.25), (b, 1083, 420, 1.4)], xfade=0.15)
else:
    plate_s(win, WW, WH, clip("nx_pick"), *SRC, q0, s1 + 0.15, [(q0, 668, 1090, 1.26), (s1 + 0.15, 668, 1090, 1.28, "none")], video=True)
    plate_s(win, WW, WH, clip("nx_type"), *SRC, s1, s2 + 0.15, [(s1, 668, 960, 1.25), (s2 + 0.15, 668, 960, 1.28, "none")], video=True)
    plate_s(win, WW, WH, clip("nx_search"), *SRC, s2, s3 + 0.15, [(s2, 667, 372, 1.23), (s3 + 0.15, 667, 380, 1.26, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_research_cite_land"), *LS, s3, s4 + 0.15, [(s3, 1082, 393, 1.136), (s4 + 0.15, 1082, 393, 1.18)])
    plate_s(win, WW, WH, clip("nx_deck"), *SRC, s4, s5 + 0.15, [(s4, 668, 400, 1.23), (s5 + 0.15, 668, 420, 1.26, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_deck_preview_port"), *PS, s5, s6 + 0.15, [(s5, 811, 990, 1.85), (s6 + 0.15, 811, 990, 2.0)])
    plate_s(win, WW, WH, clip("nx_sched"), *SRC, s6, s7 + 0.15, [(s6, 662, 400, 1.23), (s7 + 0.15, 662, 400, 1.23, "none")], video=True, tag="TIME-LAPSE")
    plate_s(win, WW, WH, still("nx_sched_port"), *PS, s7, b, [(s7, 662, 400, 1.23), (b, 662, 420, 1.28)], xfade=0.15)

# ---------------------------------------------------------------- NEURON
a, b = SCN["neuron"]
product("Neuron", "enterprise intelligence", a, b)
win = f.window(WX, WY, WW, WH, a, b, enter="rise")
# the website's own Neuron scene, step by step: sources, warehouse, semantic layer, index, agents
steps = [(1, a), (2, t("l13", "answers") - 0.1), (3, t("l13", "knowledge") - 0.15), (4, t("l13", "data") - 0.15), (5, t("l13", "agents") - 0.15)]
c0, c1 = ((1400, 540, 1.34), (1420, 540, 1.42)) if LAND else ((1405, 525, 1.25), (1405, 525, 1.3))
cam = lambda tt: tuple(c0[j] + (c1[j] - c0[j]) * (tt - a) / (b - a) for j in range(3))  # one camera, so steps dissolve in place
for k, (st, t0) in enumerate(steps):
    t1 = steps[k + 1][1] + 0.25 if k + 1 < len(steps) else b
    plate_s(win, WW, WH, still(f"ws_neuron{st}"), *LS, t0, t1, [(t0, *cam(t0)), (t1, *cam(t1), "none")], xfade=0.25, tag="NETIGEN.AI · LAYER DIAGRAM" if k == 0 else None)

# ---------------------------------------------------------------- NIMBUS
a, b = SCN["nimbus"]
product("Nimbus", "trust &amp; observability", a, b)
NH = WH if LAND else 560
win = f.window(WX, WY if LAND else WY + 110, WW, NH, a, b, enter="rise")
c1 = t("l10", "what") - 0.05
c2 = t("l10", "how") - 0.1
c3 = t("l10", "and") - 0.05
DIV = 180                                           # the scene's sidebar ends here
z0, z1 = (2.25, 2.32) if LAND else (1.62, 1.66)
fb = ((487, 258, 2.25), (484, 258, 2.27)) if LAND else ((487, 258, 1.62), (486, 258, 1.63))  # tiles and cards whole  # the feedback cards
shots = [("wsc_nim_home", a + 0.05, c1, 200, 200),    # the console's home
         ("wsc_nim_cost", c1, c2, 172, 172),          # what every answer cost
         ("wsc_nim_agents", c2, c3, 172, 172)]        # how fast it came back
for st, t0, t1, y0, y1 in shots:
    plate_s(win, WW, NH, still(st), *WSZ, t0, t1 + 0.15, [(t0, DIV + WW / z0 / 2, y0, z0), (t1 + 0.15, DIV + WW / z1 / 2, y1, z1)], xfade=0.18)
plate_s(win, WW, NH, still("wsc_nim_home"), *WSZ, c3, b, [(c3, *fb[0]), (b, *fb[1])], xfade=0.18)  # how people rated it

# ---------------------------------------------------------------- UNIFY
a, b = SCN["unify"]
trio = [("np_group_b", "Govern it.", "Naper", "govern", (900, 520, 0.42), (540, 760, 0.8)),
        ("nx_deck_preview", "Use it.", "Nexus", "use", (1552, 569, 0.6), (810, 965, 1.08)),
        ("ws_neuron5", "Ground it.", "Neuron", "ground", (1450, 540, 0.42), (1450, 560, 0.9)),
        ("wsc_nim_cost", "See it.", "Nimbus", "see", (480, 190, 0.62), (480, 190, 1.2))]
for i, (st, lab, nm, word, lk, pk) in enumerate(trio):
    tw = t("l11", word)
    if LAND:
        x, y, w, h = 56 + 460 * i, 270, 430, 290
        wid = card(still(st if st.startswith("ws") else st + "_land"), *(WSZ if st.startswith("wsc_") else LS), x, y, w, h, a + 0.08 * i, b, lk[0], lk[1], lk[2], lk[2] * 1.05, dim=0.45, z=20)
        f.text(lab, x, y + h + 40, w, tw, b, "card-label", align="center")
        f.text(nm, x, y + h + 96, w, tw + 0.1, b, "sub", align="center")
    else:
        x, y, w, h = 70, 400 + 262 * i, 580, 220
        src, dims = (still(st), WSZ if st.startswith("wsc_") else LS) if st.startswith("ws") else (still(st + "_port"), PS)
        wid = card(src, *dims, x, y, w, h, a + 0.08 * i, b, pk[0], pk[1], pk[2], pk[2] * 1.05, dim=0.45, z=20)
        f.text(lab, x + w + 44, y + 62, 340, tw, b, "card-label", align="left")
        f.text(nm, x + w + 46, y + 124, 340, tw + 0.1, b, "sub", align="left")
    f.tl(f'tl.to("#{wid} .dim", {{opacity: 0, duration: 0.35}}, {tw:.3f}); tl.to("#{wid}", {{scale: 1.035, duration: 0.5, ease: "expo.out"}}, {tw:.3f});')

# ---------------------------------------------------------------- END
a, b = SCN["end"]
if LAND:
    em, ey, wmy, l1y, url_y = 190, 300, 500, 676, 930
else:
    em, ey, wmy, l1y, url_y = 220, 560, 800, 1000, 1290
f.add(f'<div id="end-mark" class="mark" style="color:#7C3AED;left:{W / 2 - em / 2}px;top:{ey - em / 2}px;width:{em}px;height:{em}px;z-index:30;opacity:0">{MARK}</div>')
f.add(f'<div id="end-glow" style="position:absolute;left:{W / 2 - 500}px;top:{ey - 500}px;width:1000px;height:1000px;border-radius:50%;background:radial-gradient(circle, rgba(124,58,237,.16), rgba(124,58,237,0) 62%);opacity:0;z-index:25"></div>')
f.tl(f'tl.fromTo("#end-mark", {{opacity: 0, scale: 0.55, filter: "blur(14px)"}}, {{opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.9, ease: "expo.out"}}, {a:.3f});')
f.tl(f'tl.fromTo("#end-glow", {{opacity: 0, scale: 0.6}}, {{opacity: 1, scale: 1, duration: 1.6, ease: "expo.out"}}, {a:.3f}); tl.to("#end-glow", {{opacity: 0.55, duration: 4, ease: "sine.inOut"}}, {a + 1.6:.3f});')
f.add(f'<div id="end-wm" class="wordmark" style="left:0;width:{W}px;top:{wmy}px;text-align:center;z-index:31;opacity:0">Netigen</div>')
f.tl(f'tl.fromTo("#end-wm", {{opacity: 0, y: 30, filter: "blur(10px)"}}, {{opacity: 1, y: 0, filter: "blur(0px)", duration: 0.8, ease: "expo.out"}}, {t("l12", "netigen"):.3f});')
f.words([[("One", "sans", t("l12", "one")), ("AI", "sans", t("l12", "ai")), ("platform.", "sans", t("l12", "platform"))],
         [("Every", "serif", t("l12", "every")), ("stage", "serif", t("l12", "stage")), ("of", "serif", t("l12", "of")), ("business.", "serif", t("l12", "business"))]],
        0, l1y, W, 64 if LAND else 70, None, align="center", serif_scale=1.3, lh=1.25)
f.text("netigen.ai", 0, url_y, W, t("l12", "business") + 0.6, None, "url", align="center")
f.add('<div id="fadeout" class="fade"></div>')
f.tl(f'tl.to("#fadeout", {{opacity: 1, duration: 0.6, ease: "power1.in"}}, {TL["duration"] - 0.65:.3f});')

# ---------------------------------------------------------------- captions
if LAND:
    f.add('<div id="capband" class="capband" style="top:860px;height:220px;opacity:0"></div>')
    f.tl(f'tl.to("#capband", {{opacity: 1, duration: 0.5}}, {SCN["naper"][0]:.3f}); tl.to("#capband", {{opacity: 0, duration: 0.5}}, {SCN["unify"][0]:.3f});')
    f.captions(CAPS, {"l03", "l04", "l05", "l06", "l07", "l09", "l13", "l10"}, 160, 946, 1600, 46, max_words=8)
else:
    f.add('<div id="capband" class="capband" style="top:1300px;height:260px;opacity:0;background:linear-gradient(180deg,transparent,rgba(246,244,240,.85),transparent)"></div>')
    f.tl(f'tl.to("#capband", {{opacity: 1, duration: 0.5}}, {SCN["naper"][0]:.3f}); tl.to("#capband", {{opacity: 0, duration: 0.5}}, {SCN["unify"][0]:.3f});')
    f.captions(CAPS, {"l03", "l04", "l05", "l06", "l07", "l09", "l13", "l10"}, 60, 1350, 960, 50, max_words=6)

css = open(os.path.join(ROOT, "edit", "style_dark.css" if os.environ.get("CAP_THEME") == "dark" else "style.css")).read()
out = os.path.join(project_dir(ROOT, fmt), "index.html")
open(out, "w", encoding="utf-8").write(f.page(css, "assets/mix.wav"))
print("wrote", out, len(f.js), "tweens")
