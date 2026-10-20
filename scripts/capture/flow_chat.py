# Nexus chat flow: model pick -> web research with citations -> deck -> mail draft. Usage: flow_chat.py land|port [stages]
import sys, json, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]; stages = sys.argv[2].split(",") if len(sys.argv) > 2 else ["research", "deck", "mail"]
STATE = os.path.join(OUT, f"chat_{fmt}.url")
Q1 = "What are the three biggest shifts in GCC retail this quarter? One line each, with sources."
Q2 = "Turn this into a 5-slide deck for our leadership team."
Q3 = "Draft an email to leadership@example.com sharing the deck, in two short lines."
os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b, ctx = context(p, fmt)
    pg = ctx.new_page()
    if "research" in stages:
        pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
        t = Take(pg, "research", fmt); t.start()
        pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(3500); t.mark("home")
        pg.get_by_role("button", name="LLM: GPT-5.4").click(); pg.wait_for_timeout(1400); t.mark("picker-open")
        opt = pg.get_by_text("GPT-5.6", exact=True).first; opt.scroll_into_view_if_needed(); pg.wait_for_timeout(700)
        opt.click(); pg.wait_for_timeout(900); t.mark("picked")
        pg.locator("textarea").first.click(); type_human(pg, Q1); pg.wait_for_timeout(600); t.mark("typed")
        pg.keyboard.press("Enter"); t.mark("sent")
        wait_turn(pg, t)
        pg.wait_for_timeout(1500)
        open(STATE, "w").write(pg.url)
        try:
            chip = pg.locator("a.not-typeset").first
            chip.scroll_into_view_if_needed(); chip.hover(); pg.wait_for_timeout(3200); t.mark("cite-hover")
        except Exception as e:
            print("cite hover failed", e)
        pg.mouse.move(400, 600); pg.wait_for_timeout(700)
        try:
            import re
            pg.get_by_role("button", name=re.compile(r"^\d+ sources$")).last.click(); pg.wait_for_timeout(2600); t.mark("sources-panel")
        except Exception as e:
            print("sources failed", e)
        pg.wait_for_timeout(1000); t.stop()
        still(pg, f"research_answer_{fmt}")
    else:
        pg.goto(open(STATE).read(), wait_until="domcontentloaded"); pg.wait_for_timeout(8000)
        if "cite" in stages:
            t = Take(pg, "cite", fmt); t.start(); pg.wait_for_timeout(1200)
            chips = pg.locator("a.not-typeset")
            for i in range(min(3, chips.count())):
                chips.nth(i).hover(); pg.wait_for_timeout(2600); t.mark(f"cite-{i}")
            pg.mouse.move(400, 700); pg.wait_for_timeout(800); t.stop()
        pg.get_by_role("button", name="LLM: GPT-5.4").click(); pg.wait_for_timeout(1000)
        o = pg.get_by_text("GPT-5.6", exact=True).first; o.scroll_into_view_if_needed(); o.click(); pg.wait_for_timeout(800)
    if "deck" in stages:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        close = pg.get_by_role("button", name="Close")
        if close.count() and close.first.is_visible(): close.first.click(); pg.wait_for_timeout(800)
        t = Take(pg, "deck", fmt); t.start()
        pg.locator("textarea").first.click(); type_human(pg, Q2); pg.wait_for_timeout(500); t.mark("typed")
        pg.keyboard.press("Enter"); t.mark("sent")
        wait_turn(pg, t, timeout=600); pg.wait_for_timeout(3000)
        try:
            prev = pg.get_by_role("button", name="Preview").last
            prev.hover(); pg.wait_for_timeout(800); prev.click(); pg.wait_for_timeout(6000); t.mark("preview-open")
        except Exception as e:
            print("preview failed", e)
        t.stop(); still(pg, f"deck_answer_{fmt}")
    if "mail" in stages:
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        t = Take(pg, "mail", fmt); t.start()
        pg.get_by_role("button", name="Add assets").click(); pg.wait_for_timeout(900)
        pg.get_by_role("menuitem", name="Apps").hover(); pg.wait_for_timeout(900); t.mark("apps-menu")
        pg.get_by_text("Outlook", exact=True).last.click(); pg.wait_for_timeout(900); t.mark("outlook-on")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(500)
        pg.locator("textarea").first.click(); type_human(pg, Q3); pg.wait_for_timeout(500); t.mark("typed")
        pg.keyboard.press("Enter"); t.mark("sent")
        wait_turn(pg, t, timeout=300); pg.wait_for_timeout(2500)
        try:
            send = pg.get_by_role("button", name="Send").last
            send.scroll_into_view_if_needed(); send.hover(); pg.wait_for_timeout(2500); t.mark("send-hover")
        except Exception as e:
            print("send hover failed", e)
        t.stop(); still(pg, f"mail_answer_{fmt}")
    b.close()
