# Nexus extras: home reveal take, agent mode list, agents, apps, assets stills. Usage: flow_extras.py land|port
import sys, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]
with sync_playwright() as p:
    b, ctx = context(p, fmt); pg = ctx.new_page()
    pg.goto("http://localhost:3000/agents", wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
    t = Take(pg, "home", fmt); t.start()
    pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(4000); t.mark("home")
    pg.get_by_role("button", name="Agent", exact=True).first.click(); pg.wait_for_timeout(2500); t.mark("agent-mode")
    pg.get_by_role("button", name="Chat", exact=True).first.click(); pg.wait_for_timeout(1200); t.mark("chat-mode")
    t.stop()
    for u, n in [("/", "home"), ("/agents", "agents"), ("/apps", "apps"), ("/assets", "assets"), ("/scheduled", "scheduled")]:
        pg.goto("http://localhost:3000" + u, wait_until="domcontentloaded"); pg.wait_for_timeout(6000)
        still(pg, f"nexus_{n}_{fmt}")
    pg.goto("http://localhost:3000/", wait_until="domcontentloaded"); pg.wait_for_timeout(5000)
    pg.get_by_role("button", name="Agent", exact=True).first.click(); pg.wait_for_timeout(2000)
    still(pg, f"nexus_agentmode_{fmt}")
    b.close()
