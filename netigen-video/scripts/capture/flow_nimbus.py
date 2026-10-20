# Nimbus: home hero -> agent performance -> cost overview -> LLM performance. Usage: flow_nimbus.py land|port
import sys, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]
with sync_playwright() as p:
    b, ctx = context(p, fmt); pg = ctx.new_page()
    for u in ["/", "/agent/performance-v2", "/cost/efficiency", "/llm/performance", "/trust/overview"]:
        pg.goto("http://localhost:3003" + u, wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
        still(pg, "nimbus" + u.replace("/", "_").rstrip("_") + f"_{fmt}")
    t = Take(pg, "nimbus", fmt); t.start()
    pg.goto("http://localhost:3003/", wait_until="domcontentloaded"); pg.wait_for_timeout(4500); t.mark("home")
    for name, label in [("Agent Performance", "agents"), ("Cost Overview", "cost"), ("LLM Performance", "llm")]:
        pg.get_by_role("link", name=name).first.click(); pg.wait_for_timeout(4200); t.mark(label)
        pg.mouse.move(1100, 650); pg.mouse.wheel(0, 380); pg.wait_for_timeout(1500); pg.mouse.wheel(0, -380); pg.wait_for_timeout(600)
    t.stop()
    b.close()
