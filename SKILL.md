---
name: netigen-video
description: Make a Netigen product video (a launch film, one feature, one layer, or the whole Naper/Nexus/Neuron/Nimbus platform) from real product UI, with AI voiceover, music, captions and a LinkedIn caption, in any aspect ratio (16:9, 9:16, 1:1, 4:5, 16:10, ...). Use when the user asks for a Netigen, Nexus, Naper, Neuron or Nimbus video, demo film, launch film, feature reel or promo.
---

# Netigen product video

Makes a premium, cinematic product film from **real Netigen UI**: live recordings of the local stack plus the netigen.ai website's product scenes. It is narrated by a Gemini TTS voice, scored with Lyria music, cut in HyperFrames (HTML + GSAP), rendered per aspect ratio and delivered with captions and a LinkedIn caption.

This skill is the October 2026 launch film turned into a procedure. Every learning from that session is in [reference/session-learnings.md](reference/session-learnings.md). The working code is in [scripts/](scripts/README.md).

## Hard rules (the user's own words, never relaxed)

1. **Real UI only.** "Never fabricate the missing interface." Every shot must trace to a capture file from the live app or a netigen.ai website product scene. If a screen cannot be reached, drop the shot and say so. Never paint over or alter real UI text.
2. **Features, not figures.** "We don't show real value output ... our main motive is to show the feature and working and UI." No real costs, tokens, latencies, ratings, counts or client data (never a client knowledge pack such as jb). Blur does not hide chart shapes or proportions.
3. **Website scenes instead of blur.** "Instead of the blurred things, take videos from the netision-website repo." Any screen that would need blurring comes from the website's demo-data scenes.
4. **Light mode by default.** "I want the video in light mode, not dark mode." Ask, but default to light.
5. **All four layers** in any whole-platform film: Naper, Nexus, Neuron, Nimbus. Never claim a feature the website marks "rolling out" or "soon".
6. **No real side effects.** Hover Send, Create task and Save Group; never click them. Use @example.com addresses and all-zero GUIDs only.
7. **Never expose secrets.** Session cookies, JWTs, API keys and connection strings stay in local files. Never print them, never put them in chat, and delete the session files after capture.
8. **Ask before touching the user's processes.** Starting, stopping or restarting their services needs a yes. At the end, offer to stop everything you started.
9. **Be fast.** The user lost patience with repeated review rounds ("bro it's being too long, we need the final result"). Send an early preview, then do one review pass and one fix pass, deliver, and ask before any further round. Give a step/time table when asked for an ETA.
10. **A small change stays small.** When the user says "the video is perfect, just add X", change only X and keep the rest of the approved film.
11. **Look:** premium and cinematic, with restrained highlights and refined type. No generic AI visuals, heavy gradients or static slides. Report every tooling limitation in the hand-off.
12. Standing preferences: reply in English, no commits unless asked, never commit to master, no co-author trailer, never force push.

## Step 0: Intake (ask before anything else)

Use AskUserQuestion. **Ask only what the request leaves open.** "A 30 s Nexus scheduled-tasks video in 1:1 and 9:16" already answers scope, length and ratios. Each question allows 2-4 options, and the tool adds "Other" by itself. Round 1:

| Question | Options (first is the default) |
|---|---|
| What is the video about? | Whole platform (all four layers) · One layer · One feature or flow · Re-cut an existing film (new ratio or length) |
| Landscape ratios? (multi-select) | 16:9 · 16:10 · 4:3 · None |
| Vertical or square ratios? (multi-select) | 9:16 · 1:1 · 4:5 · None |
| How long? | 45-60 s · 30 s · 15-20 s teaser · 90 s+ |

The theme defaults to light; ask only if the request hints at dark. For a single layer or feature, ask which one in the next round. For a re-cut, ask for the existing film folder (`FILM_ROOT`), which holds mix.wav, the VO take, `takes/*.json` and `media.json`. Without that folder, a re-cut becomes a full rebuild with new VO and music.

Round 2 (only what Round 1 leaves open):

| Question | Options |
|---|---|
| Where will it be posted? | LinkedIn (caption + SRT) · Website · Internal / sales · Other |
| Voiceover? | Gemini TTS, voice Charon (male, calm) · Kore / Sulafat (female) · Music and captions only |
| Audience or market for the demo prompts? | GCC/UAE enterprise (default) · Other |
| Screens that would show real data? | Use netigen.ai website scenes (default) · Record live and blur |

Then state the plan in one table: the scenes, which source each uses (live / website), the formats and an ETA. Ask the user to confirm the features to show. A first film takes about 2-3 h. Re-cutting an existing film into a new ratio takes about 45-60 min.

## Step 1: Repos, services, preflight

Repos (find the local clone with `git remote get-url origin`; ask if one is missing). The full map is in [reference/repos-and-services.md](reference/repos-and-services.md).

| Repo | What the film uses it for |
|---|---|
| https://github.com/netisionhq/netigen | Nexus (3000), auth (3001), Naper (3002), Nimbus (3003), api (3100), Convex (3210/3211); brand (packages/ui logo.tsx, shadcn.css light tokens, fonts) |
| https://github.com/netisionhq/netigen-draft | Agent backend (8001); every Nexus turn runs through it |
| https://github.com/netisionhq/netigen-mcp | Tool server (8004): web search, decks, files |
| https://github.com/netisionhq/netigen-backend-core | Shared LLM library (models.yaml names in the picker) |
| https://github.com/netisionhq/netision-website | netigen.ai: product scenes (`/dev/scenes?only=<Scene>`), `/platform` layer pages, layer copy in `src/content.ts` and `public/llms.txt` |
| https://github.com/heygen-com/hyperframes | Video framework (pinned `hyperframes@0.8.134`) and its skills |

Preflight, in order:
1. Tooling, with the versions tested in October 2026: Node 22.22 (the monorepo asks for 24+; check before `pnpm dev`), Python 3.11.4, Playwright for Python 1.58, uv 0.5.7, numpy, scipy, PIL, pydub, openai-whisper and google-genai. Fetch ffmpeg into `<film>/bin`: query the BtbN release API for the real asset name (never guess it), then check that `ffmpeg -filters` lists loudnorm, sidechaincompress, afade and alimiter. Run `npx -y hyperframes@0.8.134 doctor --json`.
2. Scaffold `<film>` (see [scripts/README.md](scripts/README.md)), install the HyperFrames skills into `<film>/.claude/skills`, and **copy `scripts/shared/` assets into each project's `assets/lib` and `assets/fonts`**. Without GSAP the timeline renders blank. Ask before running `hyperframes skills update`.
3. Services: run the health checks in [reference/repos-and-services.md](reference/repos-and-services.md). Check every port for more than one listening PID (the IPv4 vs `::1` clash on 3100 cost hours). Ask before starting anything. Run the website on **3107**, never on a netigen port.
4. Sign-in: inject the user's own session cookie (see [reference/capture.md](reference/capture.md)). The cookie goes into a local file, never into chat. Check it with `/api/auth/get-session`.
5. Connector flows (Outlook, Gmail, Zoho): ask the user to sign in again first, test one turn, and grep the api log for `refresh-token failed` / `AADSTS7000222`. If a connector is broken, cut its scene rather than fake it.
6. Re-run `explore.py` on every screen you will film: UI copy changes between films.

## Step 2: Research and claims (one parallel fan-out)

Run one workflow of read-only agents (nexus, naper, nimbus, neuron/website, capabilities, brand, trends, audio). Quote the user's request verbatim in every agent prompt, or the agents decline. Tell each agent: no editing, building or restarting anything; never run `next build`; never copy secrets; flag any client or personal data it sees. Trends agents tag each source OFFICIAL / CREDIBLE / VENDOR / DERIVED. WebFetch cannot watch YouTube or X videos, so craft notes come from write-ups and the agent says so. Never promise reach. Each agent writes `research/<key>.md` with a file path cited for every claim. `capabilities.md` holds a film-safe phrasing column and a claims-to-avoid list. The script may only use that phrasing, or narrower. For a single-feature film, research only that feature plus the brand. Product facts already verified are in [reference/product-map.md](reference/product-map.md).

## Step 3: Script and storyboard

- Structure: hook on the business outcome (works with the sound off), then an ecosystem or feature reveal, one beat per proven feature, a unify beat, and an end card with the netigen.ai CTA. Both templates are in [reference/edit-render.md](reference/edit-render.md): the approved 61 s whole-platform film and a 30 s single-feature film.
- One line per feature you can actually film. Drop any line whose feature could not be recorded (the mail line was dropped this way).
- Write demo prompts for the audience's market and name the tool in them ("search the web for ..."). Vague prompts stall the scheduled-task composer.

## Step 4: Capture

Details and gotchas: [reference/capture.md](reference/capture.md). In short:
- Capture **each aspect ratio natively at its own viewport** (`lib.FORMATS`), so the real UI reflows. Never crop a landscape take for portrait.
- Motion takes run at DPR 1 with the CDP screencast recorder (`Take`), logging a labelled event at every beat. Zoom-in shots are 2x stills (`device_scale_factor=2`). Website scenes are dense 3x sweeps (`stills_dense.py`) or stepped stills (`stills_neuron.py`).
- Theme: set `CAP_THEME=light`. Website scenes get `shared/light-theme.css` injected.
- Privacy: set `CAP_SENSITIVE` to the signed-in user's and teammates' names plus the company email domain, joined with `|`. Boxes are logged automatically and blurred into the pixels.
- Save every chat URL (`takes/*.url`), back up good takes to `takes/keep/` before re-running, and check each take's events for `error-state`.
- Before the edit, send the user a raw capture reel and the voice-and-music draft (an MP3 of the mix), so they can change direction while it is still cheap. The reel: about 30 s of sped-up real captures, 720p, crf 22. Check that SendUserFile actually delivered it.

## Step 5: Audio

Details: [reference/audio.md](reference/audio.md). Tell the user about the Gemini TTS free-tier quota (10 requests a day) before a long session. Generate the whole script as **one** take: `tts_gemini.py lines.json vo/` (`gemini-3.8-flash-tts`, voice Charon); `--retake l05` redoes a single line. Align it with `align.py vo/all.wav --lines lines.json --out vo_timing.json` (Whisper small.en, brand names in the prompt). Generate two Lyria RealTime takes steered by `cue.json` to the scene times, and pick one by RMS and spectral centroid. Add procedural SFX and mix with ducking (-10 dB, 60 ms / 500 ms). Then run two-pass loudnorm to -14 LUFS / -1.5 dBTP. Splice lines with 220 ms of pre-roll and 240 ms of post-roll, or brand-name onsets get clipped.

## Step 6: Edit

Details: [reference/edit-render.md](reference/edit-render.md). `timeline.json` is the only source of timing. The chain is:

```
audio/build_audio.py -> audio/norm.sh -> copy mix.wav into each project
edit/gen_media.py -> edit/prepare_media.py <fmt> [names] -> edit/build.py <fmt>
```

Time every cut to a spoken word (`t(line, word)`) and every overlay to a recorded take event (`clip_at`). Frame from a 100 px grid drawn over each still. Follow the framing rules: no text cut mid-word at a window edge, nothing sliced at the top or bottom, crop on column gaps, keep a 12 px margin through the whole push-in, label any shot sped up more than 3x TIME-LAPSE, and put that tag at the bottom-right.

**Any aspect ratio:** `scripts/edit/formats.py` and `capture/lib.py` share the format keys `land`, `port`, `16x10`, `4x3`, `1x1`, `4x5` and `21x9`. Every script takes the key: `flow_*.py 1x1`, `gen_media.py 1x1 port`, `prepare_media.py 1x1`, `build.py 1x1`. The project goes in `videos/$FILM_NAME-<ratio>`. `build.py` picks the `land` layout for wide canvases and the `port` layout for square and tall ones. Its window, header, caption and per-scene positions are written for 1920×1080 and 1080×1920, so for any other canvas re-place them for its W×H and check every scene in snapshots. Capture again at that viewport; never crop. Website scenes in a narrow canvas get a page-shaped window, not a crop that cuts columns.

## Step 7: Check, render, mux

- Before the final render, confirm the ratio list with the user once more.
- Before each render: `hyperframes@0.8.134 check` (0 errors needed; warnings are advisory), then a snapshot of about 30 moments per format (`--describe false --no-end --timeout 20000`). Read every contact sheet.
- Render: `render --crf 14 --fps 30 --workers 2`, in the background (about 5 min per format for 61 s).
- Mux the exact `mix.wav` in afterwards (the renderer's own audio drifts to about -15.3 LUFS). For portrait renders, add `fillborders=right=8:mode=smear`: HyperFrames 0.8.134 leaves a black 8 px strip there. Probe the last columns of a frame with PIL after every render.
- Make a crf 21 preview under 30 MB of each master to send. SendUserFile refuses anything larger.

## Step 8: Review (one pass, then one recheck at most)

Details and the checklist: [reference/review-deliver.md](reference/review-deliver.md). Extract frames at 2 fps from the muxed masters and run one workflow: reviewers split by frame range and format, then a refute-verifier on each finding. Give the reviewers a "known and accepted" list (website demo data, mid-dissolve frames, the TIME-LAPSE tag, captions highlighting word by word) to stop false positives. Fix only what is confirmed, re-render once, and deliver.

## Step 9: Deliver

- The masters `deliver/<Name>-<ratio>.mp4`, their previews, `linkedin-caption.md` (template in [reference/review-deliver.md](reference/review-deliver.md)) and `<name>.srt`.
- The caption's provenance sentence must match the real sources exactly: which screens are live recordings, which are netigen.ai scenes with demo data, and that the voice and music are AI-generated. Never promise reach or invent claims.
- "Before you post" notes: check the brand-name pronunciation (Naper, Netigen), list any dropped scenes and why, say which screens are website scenes, and flag any dated UI text such as old model names in the picker.
- List the services you started and offer to stop them.
- **Last question, always:** "Do you want this in another aspect ratio (16:9, 9:16, 1:1, 4:5, 16:10, other)?" A new ratio reuses the audio, `timeline.json` and story. It needs new captures at that viewport, a layout branch, a render and a mux.
