import os
# Screenshots every main route of nexus, naper and nimbus, dark theme, for planning.
import sys
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
HERE = os.path.join(ROOT, r"capture")
ROUTES = {
 "nexus": ["/", "/agents", "/apps", "/assets", "/notebook", "/scheduled", "/workspaces"],
 "naper": ["/", "/members", "/groups", "/platform/organizations", "/platform/plans", "/platform/limits", "/platform/personal-users", "/power-agent/report-master", "/power-agent/new-report", "/settings/connector-apps", "/settings/features", "/settings/guests", "/settings/identity", "/settings/limits"],
 "nimbus": ["/", "/agent/performance-v2", "/cost/efficiency", "/llm/performance", "/trust/overview", "/user/feedback-overview", "/user/logs", "/user/token-usage"],
}
PORT = {"nexus": 3000, "naper": 3002, "nimbus": 3003}
HIDE = "nextjs-portal{display:none!important}"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(storage_state=HERE + r"\state.json", viewport={"width": 1600, "height": 1000}, color_scheme="dark")
    ctx.add_init_script("try{localStorage.setItem('theme','dark')}catch(e){}")
    page = ctx.new_page()
    for app, routes in ROUTES.items():
        for r in routes:
            url = f"http://localhost:{PORT[app]}{r}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(6000)
                page.add_style_tag(content=HIDE)
                name = (app + r.replace("/", "_")).rstrip("_")
                page.screenshot(path=os.path.join(HERE, "survey", f"{name}.png"))
                print("OK", url, "->", page.url)
            except Exception as e:
                print("FAIL", url, str(e)[:150])
    b.close()
