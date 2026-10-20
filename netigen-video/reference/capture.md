# Capture: sign-in, live takes, stills, website scenes

All scripts are in `scripts/capture/`. Run them as `python -I <script> <fmt> [stages]` with `FILM_ROOT=<film>` set. `fmt` is a key of `lib.FORMATS`: `land` 1920×1080, `port` 1080×1920, `16x10`, `4x3`, `1x1`, `4x5`, `21x9`.

## Sign-in (Better Auth: Microsoft or Google only, no passwords)

- Automated OAuth in a fresh Playwright browser failed with Microsoft `invalid_code`. What works is reusing the user's own session, with their consent.
- Ask the user to copy the `better-auth.session_token` cookie value from their signed-in browser (DevTools > Application > Cookies > localhost) into `<film>/capture/token.txt`. **Never paste it in chat.**
- `session.py` polls token.txt, injects the cookie (domain localhost, path /, httpOnly, sameSite Lax), opens Nexus, checks the URL stayed on `localhost:3000`, then saves `capture/state.json` (storage_state) and prints SIGNED_IN. Keep only the session_token cookie in state.json and strip the `better-auth.session_data.*` cache cookies.
- The session lasts 7 days. Before filming, re-check it with `curl -H "Cookie: better-auth.session_token=$T" http://localhost:3100/api/auth/get-session`, and check that `/api/auth/token` returns the Convex JWT Nexus server components use. That tells an expired session apart from a broken API. Never echo `$T`; redact any JWT in printed output (pipe through `sed` to `<redacted>`).
- Connector flows: after the user signs in to a connector again, record that flow **first**, before its token lapses.
- Delete token.txt and state.json when the film is done.

## Capture context (`lib.context`)

- Headless Chromium with `--disable-renderer-backgrounding --disable-background-timer-throttling`, storage_state, the viewport from `FORMATS[fmt]`, `device_scale_factor=dpr`, and `color_scheme=CAP_THEME`. An init script sets `localStorage.theme` (the Netigen apps read it) and hides the Next.js dev badge (`nextjs-portal{display:none!important}`).
- Theme: `export CAP_THEME=light` (or dark). One switch re-records everything.
- First hits compile slowly in dev (6-18 s), so warm each route with a `goto` and wait 7-9 s before interacting. Check `pg.url` and the expected element first: a bounce to `localhost:3001` looks like a missing element.
- After a menu or panel, press Escape three times and click the textarea with `force=True`.
- More flags raise the screencast rate on animated pages (48.5 to 54.8 fps): `--disable-backgrounding-occluded-windows --run-all-compositor-stages-before-draw`.
- **Clean content.** Film in a clean workspace with neutral prompts and documents. Before stills, pick or create a clean chat per format (screenshot candidate `/chats/<id>` pages with explore.py) and save its URL. Older chats hold personal or messy content.

## Live takes (`Take` + `rec.Recorder`)

- The recorder is the CDP `Page.startScreencast` (JPEG q88-92). It delivers frames **only when the page repaints**: about 10 fps while typing, 15-25 fps while streaming, about 2 fps when idle. The frames are rebuilt into a constant 30 fps MP4 from their timestamps (concat with per-frame durations, crf 12). A low frame count means a static screen, not a broken recorder.
- Record motion at **DPR 1**. DPR 2, or `--force-device-scale-factor=2`, cut the rate to 2.6-6 fps and added nothing. For zoom-ins, take **2x stills** with `new_context(device_scale_factor=2)`, which gives true 3840×2160 or 2160×3840 PNGs.
- `t.mark(label)` logs `[t, label]` and, at the same moment, the privacy boxes. Mark every beat. The edit cuts clips by `label±offset` (`'sent+0.3'`, `'confirm-card+1.0'`) and times overlays from events. Use lowercase-hyphenated labels.
- `wait_turn(pg, t, timeout)` waits for the Stop button to appear, then for it to be gone for 4 s. It marks `error-state` on "This page couldn't" or "Couldn't generate a response". Check every take's events for error-state before using it.
- Make optional beats (citation hover, sources panel, send hover) non-fatal with try/except.
- Save the chat URL to `takes/<k>_<fmt>.url` right after a good take. Stills can then be retaken without a new LLM turn.
- Back up good takes (`takes/keep/`, or `takes_<theme>_backup/`) before re-running: every flow overwrites `takes/<name>_<fmt>.*`.
- Run long batches as one background script that starts with `cd`, ends with `echo ALL_DONE`, and writes a log. Check it with `grep -E "^\[|failed|Error|ALL_DONE|Traceback" run.log`.
- Portrait takes carry a dark 8-10 px band at the right edge. `prepare_media.py` smear-fills it for tall formats.
- Re-record any take with a very low rate (one Nimbus take came out at 1.8 fps). Do not slow down 7-13 fps takes; speed them up instead.
- Capture-side defects to avoid: the deck's "LibreOffice was unavailable" line, tooltips running off the frame, blank lead-ins before a turn starts, a citation card opening over the prompt (hover a lower chip), and dated picker entries.

## Flows (scripts/capture)

| Script | Records |
|---|---|
| `flow_chat.py <fmt> research[,cite,deck,mail]` | Model pick, typed question, web research, citation hover, sources panel; then deck and mail stages |
| `flow_deck.py <fmt> deck` | A research-plus-deck turn, Preview, slide scroll (900 s timeout) |
| `flow_sched.py <fmt>` | Scheduled page, templates hover, typed task, TaskConfirm card, Create task hover |
| `flow_naper.py <fmt>` | Group dialog: name, inherit off, agents, connectors, Save hover, Cancel; then the features pan |
| `flow_nimbus.py <fmt>` | Route stills plus a nav take (live data: prefer the website scenes) |
| `flow_mail.py`, `flow_extras.py`, `flow_neuron.py` | Mail draft (needs a fresh Microsoft sign-in), extra beats, the early Neuron attempt |
| `stills2x.py <fmt>` | 2x stills of every zoomed state, from the saved chat URLs (no new turns) |
| `stills_org.py <fmt>` | Naper Add Organization dialog filled with fictional data, then cancelled |
| `stills_dense.py <Scene> 13` | A website scene swept at DPR 3 every 180 ms over one loop, clipped to the stage box |
| `stills_neuron.py <fmt>` | The website `/platform` Neuron scene, step by step, plus the layer diagram |
| `stills_scenes.py`, `survey.py`, `explore.py` | Website scene stills; survey of every route; `explore.py <url> <w> <h> <out.png> [code]` prints every button, input and link with its accessible name and box |

## Website scenes

- Start the site on port 3107. Open `/dev/scenes?only=<Scene>` with a 1920×1080 viewport at DPR 3 (DPR 2 was too soft for push-ins). Clip to the stage box (366,106,796,440).
- **Light mode:** the site has dark tokens only, so `color_scheme='light'` alone does nothing. Inject `scripts/shared/light-theme.css`, the product's shadcn light tokens mapped onto the site's `--color-*` variables, on DOMContentLoaded. Never edit the website repo for a film.
- Dense sweep, then a numbered contact sheet (300×166 tiles, 8 columns, index stamped on each) to pick the exact step frames. **Frame indices change between runs and themes.** Re-pick the `WEB` map in `gen_media.py` after every capture.
- Patch out the site's pause button with the neighbouring colour (`patch` boxes: website scene [748,393,38,38], Neuron stills [1864,782,40,40], in CSS px).

## Privacy during capture

- `CAP_SENSITIVE` holds the signed-in user's and teammates' names plus the company email domain, joined with `|`. The DOM text boxes that match it, plus small avatar images, are logged per mark and blurred into the pixels by `prepare_media.py` (gblur sigma 10). Never put real names in the skill or a repo; keep them in the env var for the run.
- A box logged at one event stays blurred for the whole clip. `after_send` drops boxes with y≤60 once the chat title takes the greeting's place.
- Check every still by eye for anything the regex missed: sidebar chat titles, org switcher, user chip, greeting.
- Use @example.com and all-zero GUIDs in any form. acme.com is a real domain.

## Gotchas

- Placeholder and name matching is by substring: use `exact=True` (the "Add" button and the "Acme" placeholder both matched several elements).
- Windows: write generated scripts with `encoding='utf-8'`, use forward slashes in paths (`\t` and `\n` inside `r"c:\..."` strings got mangled through heredocs and sed), and avoid non-ASCII characters (·) in selectors.
- Guard a flow's body with `if __name__ == '__main__':` before importing a helper from it.
