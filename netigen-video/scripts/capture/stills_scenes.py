import os
# 2x stills of website product scenes (demo data) at each step, from the dev gallery; logs the wide stage box.
import sys, time, json
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
import lib
lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")
SCENES = {"NimbusLayerScene": [1.4, 3.9, 6.1, 7.4, 10.4],
          "NaperLayerScene": [1.5, 2.4, 3.0, 3.5, 4.1, 5.0, 7.5, 10.1],
          "NexusLayerScene": [1.3, 2.9, 4.4, 6.4, 7.9, 10.4]}
boxes = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    for name, times in SCENES.items():
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2, color_scheme="dark")
        pg = ctx.new_page()
        pg.goto(f"http://localhost:3107/dev/scenes?only={name}", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_selector("[aria-label^='Pause'], [aria-label^='Play']", timeout=60000)
        t0 = time.time()
        box = pg.evaluate("""() => { let e = document.querySelector("[aria-label^='Pause'], [aria-label^='Play']");
          while (e && e.getBoundingClientRect().height < 300) e = e.parentElement;
          const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }""")
        boxes[name] = box
        for k, at in enumerate(times):
            while time.time() - t0 < at: pg.wait_for_timeout(40)
            lib.still(pg, f"ws_{name}_{k}")
        ctx.close()
    b.close()
json.dump(boxes, open(lib.OUT + r"\scene_boxes.json", "w"))
print(boxes)
