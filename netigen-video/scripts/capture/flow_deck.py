# Nexus: one turn that researches and builds a deck (sources become footnotes), then a mail draft. Usage: flow_deck.py land|port [stages]
import sys, os, re
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]; stages = sys.argv[2].split(",") if len(sys.argv) > 2 else ["deck", "mail"]
STATE = os.path.join(OUT, f"deckchat_{fmt}.url")
QD = "Research the three biggest shifts in GCC retail this quarter and turn them into a 5-slide deck for our leadership team, with sources."
QM = "Draft an email to leadership@example.com sharing the deck, in two short lines."

def pick_model(pg, name="GPT-5.6"):
    pg.get_by_role("button", name=re.compile(r"^LLM: ")).first.click(); pg.wait_for_timeout(1300)
    o = pg.get_by_text(name, exact=True).first; o.scroll_into_view_if_needed(); pg.wait_for_timeout(500); o.click(); pg.wait_for_timeout(900)
    assert pg.get_by_role("button", name=f"LLM: {name}").count(), "model not picked"

if __name__ == "__main__":
  with sync_playwright() as p:
        b, ctx = context(p, fmt)
        pg = ctx.new_page()
        if "deck" in stages:
            pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
            t = Take(pg, "deck2", fmt); t.start()
            pick_model(pg); t.mark("picked")
            pg.locator("textarea").first.click(); type_human(pg, QD, cps=18); pg.wait_for_timeout(500); t.mark("typed")
            pg.keyboard.press("Enter"); t.mark("sent")
            wait_turn(pg, t, timeout=900); pg.wait_for_timeout(2500)
            open(STATE, "w").write(pg.url)
            still(pg, f"deck2_answer_{fmt}")
            try:
                prev = pg.get_by_role("button", name="Preview").last
                prev.hover(); pg.wait_for_timeout(900); prev.click(); pg.wait_for_timeout(15000); t.mark("preview-open")
                still(pg, f"deck2_preview_{fmt}")
                for i in range(4):
                    pg.mouse.move(1550 if fmt == "land" else 540, 600 if fmt == "land" else 1300); pg.mouse.wheel(0, 700); pg.wait_for_timeout(1600); t.mark(f"slide-scroll-{i}")
            except Exception as e:
                print("preview failed", e)
            t.stop()
        else:
            pg.goto(open(STATE).read(), wait_until="domcontentloaded"); pg.wait_for_timeout(8000)
        if "mail" in stages:
            for _ in range(3): pg.keyboard.press("Escape"); pg.wait_for_timeout(250)
            close = pg.get_by_role("button", name="Close")
            if close.count() and close.first.is_visible(): close.first.click(); pg.wait_for_timeout(800)
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
                send.scroll_into_view_if_needed(); pg.wait_for_timeout(600); send.hover(); pg.wait_for_timeout(2500); t.mark("send-hover")
            except Exception as e:
                print("send hover failed", e)
            t.stop(); still(pg, f"mail_answer_{fmt}")
        b.close()
