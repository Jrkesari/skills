# 2x stills of Naper's Add Organization dialog filled with a fictional org (never created).
import sys, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
import lib
lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")
for fmt in ["land", "port"]:
    with sync_playwright() as p:
        b, ctx = lib.context(p, fmt, dpr=2); pg = ctx.new_page()
        pg.goto("http://localhost:3002/platform/organizations", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
        pg.get_by_role("button", name="Add", exact=True).first.click(); pg.wait_for_timeout(2500); pg.screenshot(path=f"dbg_org_{fmt}.png")
        d = pg
        d.get_by_placeholder("Acme", exact=True).fill("Acme"); pg.wait_for_timeout(300)
        d.get_by_placeholder("25", exact=True).fill("25"); pg.wait_for_timeout(300)
        d.get_by_placeholder("it@acme.com", exact=True).fill("it@example.com"); pg.wait_for_timeout(600)
        lib.still(pg, f"np_neworg_{fmt}")
        d.get_by_role("button", name="Cancel").click(); pg.wait_for_timeout(400)
        b.close()
