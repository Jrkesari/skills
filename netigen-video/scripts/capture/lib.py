# Shared capture helpers: authed dark context, redaction-box logging, event log, recorder.
import json, os, sys, time
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from rec import Recorder, HIDE
S = os.path.join(ROOT, r"capture")
OUT = os.path.join(ROOT, r"capture\takes")
# Capture at the film's own aspect so the real UI reflows to it; land/port are the two layouts build.py knows.
FORMATS = {"land": (1920, 1080), "port": (1080, 1920), "16x10": (1920, 1200), "4x3": (1440, 1080),
           "1x1": (1080, 1080), "4x5": (1080, 1350), "21x9": (2520, 1080)}
SENSITIVE = os.environ.get("CAP_SENSITIVE", r"@netision\.com")  # the recording account's and teammates' names, | separated
if "CAP_SENSITIVE" not in os.environ:
    print("[WARNING] CAP_SENSITIVE unset: only the company email domain will be blurred", flush=True)
BOXES_JS = """(re) => { const rx = new RegExp(re, 'i'); const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) { const n = w.currentNode; if (!rx.test(n.textContent)) continue;
    const el = n.parentElement; if (!el || !el.offsetParent) continue; const r = el.getBoundingClientRect();
    if (r.width && r.height && r.bottom > 0 && r.top < innerHeight) out.push([Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height), n.textContent.trim().slice(0, 40)]); }
  document.querySelectorAll('img').forEach(i => { const r = i.getBoundingClientRect(); if (/avatar|googleusercontent|graph|profile/i.test(i.src + i.alt) && r.width && r.width < 64) out.push([Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height), 'avatar']); });
  return out; }"""

SCALE = int(os.environ.get("CAP_SCALE", "2"))
def context(p, fmt, dpr=1):
    w, h = FORMATS[fmt]
    b = p.chromium.launch(headless=True, args=["--disable-renderer-backgrounding", "--disable-background-timer-throttling"])
    theme = os.environ.get("CAP_THEME", "light")
    ctx = b.new_context(storage_state=S + r"\state.json", viewport={"width": w, "height": h}, device_scale_factor=dpr, color_scheme=theme)
    ctx.add_init_script(f"try{{localStorage.setItem('theme','{theme}')}}catch(e){{}}")
    ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='nextjs-portal{display:none!important}';document.head.appendChild(s)})")
    return b, ctx

class Take:
    """One recorded clip: frames, an event log with clip-relative times, and redaction boxes."""
    def __init__(self, page, name, fmt):
        self.page, self.name, self.fmt = page, name, fmt
        self.dir = os.path.join(OUT, f"{name}_{fmt}")
        self.rec = Recorder(page, self.dir + "_frames", quality=90)
        self.events, self.boxes = [], []
    def start(self):
        self.page.add_style_tag(content=HIDE)
        self.rec.start(); self.t0 = time.time(); self.mark("start")
    def mark(self, label):
        t = round(time.time() - self.t0, 2) if hasattr(self, "t0") else 0
        self.events.append([t, label])
        try:
            self.boxes.append([t, self.page.evaluate(BOXES_JS, SENSITIVE)])
        except Exception:
            pass
        print(f"[{self.name}] {t:7.2f}s {label}", flush=True)
    def stop(self):
        self.mark("stop")
        info = self.rec.stop(self.dir + ".mp4")
        json.dump({"info": info, "events": self.events, "boxes": self.boxes, "wallclock_t0": self.t0}, open(self.dir + ".json", "w"), indent=1)
        print(f"[{self.name}] saved {self.dir}.mp4 {info}", flush=True)

def still(page, name, full=False):
    os.makedirs(os.path.join(OUT, "stills"), exist_ok=True)
    path = os.path.join(OUT, "stills", name + ".png")
    page.add_style_tag(content=HIDE)
    page.screenshot(path=path, full_page=full)
    boxes = page.evaluate(BOXES_JS, SENSITIVE)
    json.dump(boxes, open(path[:-4] + ".boxes.json", "w"))
    print("still", path, len(boxes), "boxes", flush=True)

def type_human(page, text, cps=16):
    for ch in text:
        page.keyboard.type(ch)
        page.wait_for_timeout(int(1000 / cps) + (40 if ch in " ,." else 0))

def wait_turn(page, take, timeout=420):
    """Wait for the running turn to finish: the Stop button appears, then is gone for 4 s."""
    stop = page.get_by_role("button", name="Stop generating")
    t = time.time()
    try:
        stop.first.wait_for(state="visible", timeout=30000); take.mark("running")
    except Exception:
        take.mark("no-stop-seen")
    gone = None
    while time.time() - t < timeout:
        if page.get_by_text("This page couldn").count() or page.get_by_text("Couldn't generate a response").count():
            take.mark("error-state"); return False
        if stop.count() == 0 or not stop.first.is_visible():
            gone = gone or time.time()
            if time.time() - gone > 4:
                take.mark("done"); return True
        else:
            gone = None
        page.wait_for_timeout(500)
    take.mark("timeout"); return False
