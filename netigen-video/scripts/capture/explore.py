import os
import sys, json
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FILM_ROOT") or os.getcwd()  # the film project folder
S = os.path.join(ROOT, r"capture")
url = sys.argv[1]; w, h = int(sys.argv[2]), int(sys.argv[3]); shot = sys.argv[4]
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(storage_state=S + r"\state.json", viewport={"width": w, "height": h}, color_scheme="dark")
    ctx.add_init_script("try{localStorage.setItem('theme','dark')}catch(e){}")
    pg = ctx.new_page()
    pg.goto(url, wait_until="domcontentloaded"); pg.wait_for_timeout(8000)
    for js in sys.argv[5:]:
        exec(js)
    pg.screenshot(path=S + "\\" + shot)
    els = pg.evaluate("""() => [...document.querySelectorAll('button,[role=button],a,[role=menuitem],[role=option],textarea,input,[role=switch],[role=tab]')].filter(e=>e.offsetParent).map(e=>{const r=e.getBoundingClientRect();return [e.tagName, (e.getAttribute('aria-label')||e.innerText||e.placeholder||'').trim().slice(0,50), Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]})""")
    for e in els: print(e)
    b.close()
