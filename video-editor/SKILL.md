---
name: video-editor
description: Edit the user's own videos and photos into one finished video cut to a song they provide - beat-synced cuts, Ken Burns moves on stills, dissolves, titles and an end card, optional voiceover and captions - rendered in any aspect ratio (16:9, 9:16, 1:1, 4:5, 16:10, ...). Use when the user asks to make a montage, reel, slideshow, travel or event video, highlight video, music video or social clip from clips and images plus a music track. For Netigen product films use netigen-video instead.
---

# Video editor (any footage + the user's song)

Turns a folder of the user's clips and photos into a cinematic, beat-cut video scored with **the song they give you**. Same toolchain as netigen-video: Python + ffmpeg to prepare media and audio, HyperFrames (HTML + GSAP) to compose, one project per aspect ratio, a two-pass loudnorm, a mux of the exact mix.

The working code is in [scripts/](scripts/README.md). Editing and render rules: [reference/edit-render.md](reference/edit-render.md). Audio, voiceover and delivery: [reference/audio-deliver.md](reference/audio-deliver.md).

## Hard rules

1. **Only the user's media and song.** Never add stock or AI-generated footage, images or music unless the user asks. If a slot has no good shot, reuse or shorten; say so.
2. **Never touch the originals.** Everything is read from the user's paths and written under `$FILM_ROOT`. Never delete or overwrite input files.
3. **The song is the master clock.** Never time-stretch or pitch the song. Trim it (`song_in`) and fade it; cuts land on its beats (`beats.json`). Hard cuts on beats, dissolves for slow songs.
4. **Frame each ratio on purpose.** Each aspect ratio is prepared natively from the source with a focus point. When the source aspect is far from the canvas (a landscape clip in 9:16), use `contain` (sharp picture over a blurred fill) rather than cropping away faces or text. Never cut a face or a line of on-screen text at an edge.
5. **Privacy.** If media shows strangers' faces in close-up, number plates, addresses, documents or screens with personal data, point it out and offer a blur box (`blur` on the shot); blur goes into the pixels in prepare.py.
6. **Copyright note, once.** Commercial songs may be muted or claimed on YouTube/Instagram/LinkedIn. Mention it in one line at hand-off; it is the user's call, never a blocker.
7. **Be fast.** Send an early preview, do one review pass and one fix pass, deliver, and ask before any further round. "Just change X" changes only X.
8. **Standing preferences:** reply in English, no commits unless asked, never commit to master, no co-author trailer, never force push. Ask before installing anything system-wide (ffmpeg goes in `<film>/bin`).

## Step 0: Intake (ask before anything else)

Use AskUserQuestion, and **ask only what the request leaves open**. If the user has not given the media folder or the song file, ask for the paths in plain text first (they are not multiple-choice). Round 1:

| Question | Options (first is the default) |
|---|---|
| Landscape ratios? (multi-select) | 16:9 · 16:10 · 4:3 · None |
| Vertical or square ratios? (multi-select) | 9:16 · 1:1 · 4:5 · None |
| How long? | Fit to the media (about 2 s a shot) · 30 s · 15 s · The whole song |
| Pace / feel? | Medium: cut every 2 bars, soft dissolves · Slow & cinematic: long dissolves · Fast: hard cut on every beat or two |

Round 2 (only what is still open):

| Question | Options |
|---|---|
| Text on screen? | Title + end card · Title only · None · Captions from a voiceover |
| Which part of the song? | From the start · The loudest part (auto) · End on the song's real ending |
| Clip sound? | Mute clips, song only (default) · Keep sound on chosen clips, under the song |
| Order? | As the files are named · By date taken · I'll pick the order |
| Look? | Full-bleed, dark (default) · Framed on dark · Light |

Then show the plan as one table (shots in order with their source, length and move; the song window; ratios; ETA) and ask the user to confirm. Typical time: 20-40 min for a 30 s film in two ratios, mostly render time.

## Step 1: Preflight and scaffold

1. Tooling: Python 3.11 with numpy, scipy, PIL; Node 22+ for `npx`. ffmpeg: use `$FFMPEG` or PATH if present; otherwise ask, then fetch the BtbN build into `<film>/bin` (query `https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest` for the real asset name, never guess it). An `imageio_ffmpeg` binary from any venv works too (probe.py falls back to parsing `ffmpeg -i` when there is no ffprobe), but HyperFrames renders want ffprobe as well.
2. Scaffold `<film>` (default: under the session scratchpad) as in [scripts/README.md](scripts/README.md): copy `scripts/tools`, `scripts/edit`, `scripts/audio` into it, and export `FILM_ROOT`, `FILM_NAME`, `FFMPEG`.
3. Per ratio: `npx -y hyperframes@0.8.134 init videos/$FILM_NAME-<ratio> --non-interactive --example=blank`, then copy `scripts/shared/{gsap.min.js,grain.png}` into `assets/lib/` and `scripts/shared/fonts/*` into `assets/fonts/`. Without GSAP the timeline renders blank. **Always pin 0.8.134.**

## Step 2: Look at the media

`python -I tools/probe.py <folder or files...>` writes `edit/media_index.json` and numbered contact sheets `edit/contact-N.jpg`. **Read every contact sheet.** Note per item: the subject and where it sits (for `focus`), which clips have the best moment and when (for `in`), rotated or dark shots, and anything private. Drop broken files and say so.

## Step 3: The song

Convert the user's song once: `ffmpeg -i <song> -ar 48000 -ac 2 -c:a pcm_s16le audio/song.wav`. Then `python -I tools/beats.py audio/song.wav` writes `audio/beats.json` (tempo, beats, downbeats, bar loudness, lifts). Sanity-check the tempo against the feel of the song; if it is doubled or halved, re-run with `--bpm <n>`. Details: [reference/audio-deliver.md](reference/audio-deliver.md).

## Step 4: Plan the cut

`python -I tools/plan.py [--duration 30|song] [--pace slow|medium|fast] [--song-in 0|auto|end|<s>] [--order as-listed|date|name] [--title "Line one\n*serif line*"] [--end-card "..."] [--theme dark|light] [--look fullbleed|framed] [--name "..."]` writes `edit/timeline.json` and prints the shot table and NOTES (reused inputs, dropped inputs, clips shorter than their slot).

Then **edit timeline.json by hand** from what you saw on the contact sheets. It is the only source of timing:
- Order the shots into a story: an opening shot that works as a thumbnail, build, the strongest shots on the song's lifts, a calm closing shot before the end card.
- Per shot: `focus` [x, y] (0-1, where the subject is), `move` (push-in, push-out, pan-left/right/up/down, still), `amount`, `fit` (auto, cover, contain), `xf` (dissolve length; 0 is a hard cut), `blur` boxes; for clips `in` (seconds into the source), `speed` (0.5-2; never speed up faces talking), `keep_audio` and `audio_gain`.
- Keep `start`/`end` on beats from `beats.json` when you move a cut. Put big moments on downbeats or `lifts`.
- Texts: `{"text", "style": "title"|"lower"|"caption", "start", "end"}`; in a title, a line wrapped in `*...*` is set in italic serif.

## Step 5: Prepare, build, audio

```
python -I edit/prepare.py <fmt> [shot ids]   # per ratio; pass ids to redo only those
python -I edit/build.py <fmt>                 # writes videos/$FILM_NAME-<ratio>/index.html
python -I audio/build_audio.py --diag && (cd audio && bash norm.sh)   # song (+VO, clip sound, SFX) -> mix.wav at -14 LUFS
cp audio/mix.wav videos/$FILM_NAME-<ratio>/assets/mix.wav
```

Format keys: `land` 16:9, `port` 9:16, `1x1`, `4x5`, `16x10`, `4x3`, `21x9`. Rebuild from the first stage that changed: timeline -> prepare -> build; timeline or song -> build_audio -> norm -> copy.

## Step 6: Check, preview, render

- In each project: `npx -y hyperframes@0.8.134 check` (0 errors needed; `container_overflow` infos on plates are expected, since plates are larger than the window by design). Fix contrast warnings by changing `accent`.
- `snapshot --describe false --no-end --timeout 20000 --at <one moment per shot + each text>`; read every contact sheet. Look for faces or text cut at edges, wrong focus, dark shots, text over busy areas.
- Send an early preview: render the first ratio, mux, make a crf 21 preview under 30 MB and send it with SendUserFile.
- Render: `render --crf 16 --fps 30 --workers 2 --output renders/<name>-vN.mp4` in the background. Then mux the exact `mix.wav` (commands in [reference/edit-render.md](reference/edit-render.md)); portrait renders need `fillborders=right=8:mode=smear`.

## Step 7: Review once, then deliver

Extract frames at 2 fps from the muxed master and check them against the checklist in [reference/edit-render.md](reference/edit-render.md). Fix only real defects, re-render once, deliver:
- `deliver/<Name>-<ratio>.mp4` masters, `deliver/preview/*-preview.mp4` (sent), `deliver/<name>.srt` if there is text or VO (`python -I tools/srt.py deliver/<name>.srt`), and an optional post caption if the user wants one.
- Hand-off notes: what was left out and why, any shot reused or held on its last frame, the song window used, the copyright line, and file paths.
- **Last question, always:** "Do you want this in another aspect ratio (16:9, 9:16, 1:1, 4:5, 16:10, other)?" A new ratio reuses timeline.json and mix.wav: prepare, build, check, render, mux.
