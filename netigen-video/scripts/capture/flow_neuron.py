# Website Neuron layer (netision-website, local): record its scene playing from first view; 2x stills of its final step.

import sys, os, time
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder

sys.path.insert(0, os.path.join(ROOT, r"capture"))

from playwright.sync_api import sync_playwright

import lib

fmt = sys.argv[1]; scale = int(sys.argv[2]) if len(sys.argv) > 2 else 2

W, H = lib.FORMATS[fmt]

URL = "http://localhost:3107/platform"

with sync_playwright() as p:

    b = p.chromium.launch(headless=True, args=[f"--force-device-scale-factor={scale}"])

    ctx = b.new_context(viewport={"width": W, "height": H}, color_scheme="dark")

    pg = ctx.new_page()

    pg.goto(URL, wait_until="domcontentloaded", timeout=120000); pg.wait_for_timeout(9000)

    demo = pg.locator('[aria-label="Neuron demo"]').first

    if not demo.count():

        demo = pg.get_by_text("Rows match").first

    sec = demo.locator("xpath=ancestor::section[1]")

    box = sec.bounding_box() if sec.count() else demo.bounding_box()

    print("box", box)

    target = max(0, box["y"] + pg.evaluate("scrollY") - max(0, (H - box["height"]) / 2))

    pg.evaluate(f"scrollTo(0, {target} - 1400)"); pg.wait_for_timeout(1500)

    t = lib.Take(pg, "neuron", fmt)

    t.rec = lib.Recorder(pg, t.dir + "_frames", quality=90, max_side=4000)

    t.start()

    pg.evaluate(f"scrollTo({{top: {target}, behavior: 'smooth'}})"); pg.wait_for_timeout(1200); t.mark("in-view")

    pg.wait_for_timeout(13500); t.mark("scene-end")

    t.stop()

    ctx2 = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=2, color_scheme="dark")

    p2 = ctx2.new_page(); p2.goto(URL, wait_until="domcontentloaded", timeout=120000); p2.wait_for_timeout(8000)

    p2.evaluate(f"scrollTo(0, {target})"); p2.wait_for_timeout(11800)

    lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")

    lib.still(p2, f"ws_neuron_{fmt}")

    p2.evaluate("scrollTo(0, 0)"); p2.wait_for_timeout(9000)

    lib.still(p2, f"ws_layers_{fmt}")

    b.close()

