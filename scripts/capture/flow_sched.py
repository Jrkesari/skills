# Nexus Scheduled: describe a recurring task in plain words -> TaskConfirm card (never created). Usage: flow_sched.py land|port
import sys, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]
QS = "Every weekday at 8 AM, search the web for the five most important GCC retail news stories of the last 24 hours and summarise each one with its source."
with sync_playwright() as p:
    b, ctx = context(p, fmt); pg = ctx.new_page()
    pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
    t = Take(pg, "sched", fmt); t.start()
    pg.get_by_role("link", name="Scheduled").first.click(); pg.wait_for_timeout(3500); t.mark("page")
    for name in ["Industry news watch", "Morning inbox summary"]:
        pg.get_by_role("button", name=name).first.hover(); pg.wait_for_timeout(900)
    t.mark("templates")
    pg.locator("textarea").first.click(); type_human(pg, QS, cps=20); pg.wait_for_timeout(500); t.mark("typed")
    pg.keyboard.press("Enter"); t.mark("sent")
    try:
        pg.get_by_role("button", name="Create task").first.wait_for(state="visible", timeout=180000); t.mark("confirm-card")
        pg.wait_for_timeout(1500)
        btn = pg.get_by_role("button", name="Create task").first
        btn.scroll_into_view_if_needed(); btn.hover(); pg.wait_for_timeout(2500); t.mark("create-hover")
    except Exception as e:
        print("confirm failed", str(e)[:120])
    t.stop(); still(pg, f"sched_confirm_{fmt}")
    open(os.path.join(OUT, f"sched_{fmt}.url"), "w").write(pg.url)
    b.close()
