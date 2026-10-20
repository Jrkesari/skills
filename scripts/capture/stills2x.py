# Crisp 2x stills of every state the film zooms into, in both viewports, from existing chats and pages (no new turns).
import sys, os, json, re
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
sys.path.insert(0, os.path.join(ROOT, r"capture"))
os.environ["CAP_SCALE"] = "2"
from playwright.sync_api import sync_playwright
import lib
lib.OUT = os.path.join(ROOT, r"capture\stills2x_root")
T = os.path.join(ROOT, r"capture\takes")
fmt = sys.argv[1]
def url(k):
    f = os.path.join(T, f"{k}_{fmt}.url")
    return open(f if k != "sched" and os.path.exists(f) else os.path.join(T, f"{k}_land.url")).read().strip()
U = {k: url(k) for k in ["chat", "deckchat", "sched"]}
def go(pg, url, wait=7000):
    pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(wait)
def shot(pg, name): lib.still(pg, f"{name}_{fmt}")
with sync_playwright() as p:
    b, ctx = lib.context(p, fmt, dpr=2); pg = ctx.new_page()
    go(pg, "http://localhost:3000/"); shot(pg, "nx_home")
    pg.get_by_role("button", name=re.compile(r"^LLM: ")).first.click(); pg.wait_for_timeout(1500); shot(pg, "nx_picker"); pg.keyboard.press("Escape")
    pg.get_by_role("button", name="Add assets").click(); pg.wait_for_timeout(900); pg.get_by_role("menuitem", name="Apps").hover(); pg.wait_for_timeout(1200); shot(pg, "nx_appsmenu")
    for k in range(3): pg.keyboard.press("Escape")
    go(pg, "http://localhost:3000/agents"); shot(pg, "nx_agents")
    go(pg, "http://localhost:3000/apps"); shot(pg, "nx_apps")
    go(pg, "http://localhost:3000/scheduled"); shot(pg, "nx_scheduled")
    go(pg, U["chat"], 9000); shot(pg, "nx_research")
    chips = pg.locator("a.not-typeset")
    if chips.count():
        chips.nth(1 if chips.count() > 1 else 0).hover(); pg.wait_for_timeout(3500); shot(pg, "nx_research_cite")
        pg.mouse.move(300, 700); pg.wait_for_timeout(500)
    try:
        pg.get_by_role("button", name=re.compile(r"^\d+ sources$")).last.click(); pg.wait_for_timeout(2500); shot(pg, "nx_research_sources")
    except Exception as e: print("sources", e)
    go(pg, U["deckchat"], 9000); shot(pg, "nx_deck")
    try:
        pg.get_by_role("button", name="Preview").last.click(); pg.wait_for_timeout(16000); shot(pg, "nx_deck_preview")
    except Exception as e: print("preview", e)
    go(pg, U["sched"], 9000); shot(pg, "nx_sched")
    go(pg, "http://localhost:3002/"); shot(pg, "np_overview")
    go(pg, "http://localhost:3002/groups"); pg.get_by_role("button", name="Add").first.click(); pg.wait_for_timeout(1500)
    d = pg.get_by_role("dialog"); d.get_by_placeholder("Finance").fill("Finance"); d.get_by_placeholder("Who is in it and what they work on").fill("Monthly close, forecasting and spend reviews")
    shot(pg, "np_group_a")
    d.locator("[role=switch], [data-slot=switch]").first.click(); pg.wait_for_timeout(1500)
    for n in ["Aggregator IQ", "Location Feasibility", "Geo Analyst", "Social Analyst", "Zoho Mail", "Zoho Calendar", "Zoho WorkDrive"]:
        d.get_by_text(n, exact=True).click(); pg.wait_for_timeout(200)
    pg.wait_for_timeout(600); shot(pg, "np_group_b")
    d.get_by_role("button", name="Cancel").click(); pg.wait_for_timeout(500)
    go(pg, "http://localhost:3002/settings/features"); shot(pg, "np_features")
    go(pg, "http://localhost:3002/members"); shot(pg, "np_members")
    go(pg, "http://localhost:3002/platform/limits"); shot(pg, "np_limits")
    go(pg, "http://localhost:3002/settings/limits"); shot(pg, "np_costlimits")
    for u, n in [("/", "nb_home"), ("/agent/performance-v2", "nb_agents"), ("/cost/efficiency", "nb_cost"), ("/llm/performance", "nb_llm"), ("/trust/overview", "nb_trust"), ("/user/feedback-overview", "nb_feedback")]:
        go(pg, "http://localhost:3003" + u, 8000); shot(pg, n)
    b.close()
