# Nexus: a fresh chat with Outlook switched on, asking for a mail draft (never sent). Usage: flow_mail.py land|port
import sys, os, re
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
from flow_deck import pick_model
fmt = sys.argv[1]
QM = "Draft an email to leadership@example.com saying our GCC retail deck is ready for Thursday's review. Two short lines."
with sync_playwright() as p:
    b, ctx = context(p, fmt); pg = ctx.new_page()
    pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
    pick_model(pg)
    t = Take(pg, "mail", fmt); t.start()
    pg.get_by_role("button", name="Add assets").click(); pg.wait_for_timeout(900)
    pg.get_by_role("menuitem", name="Apps").hover(); pg.wait_for_timeout(1000); t.mark("apps-menu")
    pg.get_by_text("Outlook", exact=True).last.click(); pg.wait_for_timeout(900); t.mark("outlook-on")
    for _ in range(3): pg.keyboard.press("Escape"); pg.wait_for_timeout(250)
    pg.locator("textarea").first.click(force=True); type_human(pg, QM, cps=18); pg.wait_for_timeout(500); t.mark("typed")
    pg.keyboard.press("Enter"); t.mark("sent")
    wait_turn(pg, t, timeout=400); pg.wait_for_timeout(2500)
    try:
        send = pg.get_by_role("button", name="Send").last
        send.hover(timeout=5000); pg.wait_for_timeout(2500); t.mark("send-hover")
    except Exception as e:
        print("send hover failed", str(e)[:100])
    t.stop(); still(pg, f"mail_answer_{fmt}")
    open(os.path.join(OUT, f"mailchat_{fmt}.url"), "w").write(pg.url)
    b.close()
