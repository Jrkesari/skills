import os
# 2x stills of each step of the website's Neuron scene, plus the four-layer diagram, in one viewport.
import sys, time
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
import lib
lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")
fmt = sys.argv[1]; W, H = lib.FORMATS[fmt]
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, color_scheme="light")
    ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=" + repr(open(os.path.join(ROOT, "shared/light-theme.css")).read()) + ";document.head.appendChild(s)})")
    pg = ctx.new_page()
    pg.goto("http://localhost:3107/platform", wait_until="domcontentloaded", timeout=120000); pg.wait_for_timeout(9000)
    lib.still(pg, f"ws_layers_{fmt}")
    bx = pg.evaluate("""() => { let e = document.querySelector('[aria-label$="Neuron demo"]');
      while (e && e.getBoundingClientRect().height < 300) e = e.parentElement;
      const r = e.getBoundingClientRect(); return {x: r.x, y: r.y, width: r.width, height: r.height}; }""")
    sy = pg.evaluate("scrollY")
    print("demo", bx)
    target = bx["y"] + sy - (H - bx["height"]) / 2 if fmt == "land" else bx["y"] + sy - 260
    pg.evaluate(f"scrollTo(0, {target - 2000})"); pg.wait_for_timeout(1200)
    pg.evaluate(f"scrollTo(0, {target})"); t0 = time.time()
    for k, at in enumerate([0.25, 1.6, 3.6, 6.4, 8.6, 11.4]):
        while time.time() - t0 < at: pg.wait_for_timeout(50)
        lib.still(pg, f"ws_neuron{k}_{fmt}")
    b.close()
