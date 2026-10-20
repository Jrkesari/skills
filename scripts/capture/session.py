# Waits for the user's session cookie in token.txt, injects it into the capture profile and checks it signs in.
import os, sys, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder

HERE = os.path.join(ROOT, r"capture")
TOKEN = os.path.join(HERE, "token.txt")
deadline = time.time() + 60 * 60
while not (os.path.exists(TOKEN) and open(TOKEN).read().strip()):
    if time.time() > deadline:
        sys.exit("TIMEOUT")
    time.sleep(2)
time.sleep(1)
value = open(TOKEN).read().strip().strip('"')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_cookies([{"name": "better-auth.session_token", "value": value, "domain": "localhost", "path": "/", "httpOnly": True, "sameSite": "Lax"}])
    page = ctx.new_page()
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=90000)
    print("URL", page.url)
    ok = page.url.startswith("http://localhost:3000")
    page.screenshot(path=os.path.join(HERE, "check.png"))
    if ok:
        ctx.storage_state(path=os.path.join(HERE, "state.json"))
    print("SIGNED_IN" if ok else "NOT_SIGNED_IN")
    browser.close()
