# Naper: overview -> groups -> "What this group gets" (never saved) ; features catalog pan. Usage: flow_naper.py land|port
import sys, os
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
from playwright.sync_api import sync_playwright
from lib import *
fmt = sys.argv[1]
with sync_playwright() as p:
    b, ctx = context(p, fmt); pg = ctx.new_page()
    pg.goto("http://localhost:3002/", wait_until="domcontentloaded"); pg.wait_for_timeout(7000)
    still(pg, f"naper_overview_{fmt}")
    t = Take(pg, "naper_group", fmt); t.start()
    pg.goto("http://localhost:3002/", wait_until="domcontentloaded"); pg.wait_for_timeout(3500); t.mark("overview")
    pg.get_by_role("link", name="Groups").first.click(); pg.wait_for_timeout(2500); t.mark("groups")
    pg.get_by_role("button", name="Add").first.click(); pg.wait_for_timeout(1400); t.mark("dialog")
    d = pg.get_by_role("dialog")
    d.get_by_placeholder("Finance").click(); type_human(pg, "Finance", cps=12); pg.wait_for_timeout(300)
    d.get_by_placeholder("Who is in it and what they work on").click(); type_human(pg, "Monthly close, forecasting and spend reviews", cps=22)
    pg.wait_for_timeout(600); t.mark("named")
    sw = d.locator("[role=switch], [data-slot=switch]").first
    sw.click(); pg.wait_for_timeout(1600); t.mark("inherit-off")
    for name in ["Aggregator IQ", "Location Feasibility", "Geo Analyst", "Social Analyst"]:
        d.get_by_text(name, exact=True).click(); pg.wait_for_timeout(420)
    t.mark("agents-picked")
    for name in ["Zoho Mail", "Zoho Calendar", "Zoho WorkDrive"]:
        d.get_by_text(name, exact=True).click(); pg.wait_for_timeout(380)
    t.mark("connectors-picked")
    pg.mouse.move(940, 700); pg.mouse.wheel(0, 500); pg.wait_for_timeout(1500); t.mark("scrolled")
    d.get_by_role("button", name="Save Group").hover(); pg.wait_for_timeout(1500); t.mark("save-hover")
    t.stop(); still(pg, f"naper_group_{fmt}")
    d.get_by_role("button", name="Cancel").click(); pg.wait_for_timeout(800)
    t = Take(pg, "naper_features", fmt); t.start()
    pg.get_by_role("link", name="Features").first.click(); pg.wait_for_timeout(3000); t.mark("features")
    for i in range(6):
        pg.mouse.move(1000, 600); pg.mouse.wheel(0, 260); pg.wait_for_timeout(700)
    pg.wait_for_timeout(800); t.stop()
    pg.goto("http://localhost:3002/settings/features", wait_until="domcontentloaded"); pg.wait_for_timeout(5000)
    still(pg, f"naper_features_full_{fmt}", full=True)
    b.close()
