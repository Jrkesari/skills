import os
# Dense 2x stills across one loop of a website scene, to pick the exact step frames.
import sys, time
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
import lib
lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")
name, secs = sys.argv[1], float(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=3, color_scheme="light")
    ctx.add_init_script("document.addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent=" + repr(open(os.path.join(ROOT, "shared/light-theme.css")).read()) + ";document.head.appendChild(s)})")
    pg = ctx.new_page()
    pg.goto(f"http://localhost:3107/dev/scenes?only={name}", wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_selector("[aria-label^='Pause'], [aria-label^='Play']", timeout=60000)
    t0 = time.time(); k = 0
    while time.time() - t0 < secs:
        pg.screenshot(path=lib.OUT + rf"\dense\{name}_{k:02d}.png", clip={"x": 366, "y": 106, "width": 796, "height": 440}); k += 1
        pg.wait_for_timeout(180)
    b.close()
print(k)
