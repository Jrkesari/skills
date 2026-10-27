# Edit and render (HyperFrames)

Scripts: `scripts/edit/` (formats.py, prepare.py, engine.py, build.py, style.css dark, style_light.css). `timeline.json` is the only source of timing; `prepared_<fmt>.json` says which plate file and size each shot got for that canvas.

## Setup

```bash
export FILM_ROOT=<film> FILM_NAME=<name> FFMPEG=<film>/bin/ffmpeg.exe
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_FFMPEG_PATH=$FFMPEG HYPERFRAMES_FFPROBE_PATH=<film>/bin/ffprobe.exe
npx -y hyperframes@0.8.134 init videos/$FILM_NAME-16x9 --non-interactive --example=blank
cp scripts/shared/gsap.min.js scripts/shared/grain.png videos/$FILM_NAME-16x9/assets/lib/
cp scripts/shared/fonts/*.woff2 videos/$FILM_NAME-16x9/assets/fonts/
```

- **Pin `hyperframes@0.8.134`.** A bare `npx hyperframes` pulled a newer build mid-session and moved its snapshot folder.
- `render` needs **ffprobe** as well as ffmpeg. An imageio-ffmpeg binary alone is enough for probe/prepare/audio, not for render.
- Vendored assets: GSAP 3.14.2, a 512 px noise texture, latin woff2 of Inter (variable), Instrument Serif (regular + italic), JetBrains Mono 500.

## How the page is built

- One window (`fullbleed` = the whole canvas; `framed` = an inset rounded window with room for text). Every shot is a plate inside it, in order, so later plates sit on top.
- A plate with `xf > 0` fades in over the previous one from `start - xf` to `start` (a dissolve); `xf = 0` is a hard cut set on the beat. The plate below is hidden just after the cut, never faded, so no frame ever shows the background.
- Plates are prepared 12% larger than the window (`HEAD`), so pushes and pans never reveal an edge. Camera keys are `(t, cx, cy, zoom)` in plate px; the engine clamps them so the plate always covers the window.
- `fit`: `cover` crops to fill on the `focus` point; `contain` puts the whole picture at 90% over a blurred, darkened copy of itself. `auto` picks `contain` when the source aspect is more than ~1.4x off the canvas (portrait photo in 16:9, landscape clip in 9:16).
- Moves: `push-in`/`push-out` zoom by `amount` (default 2.5% per second of shot, 4-10%); pans travel 0.4 x amount so they never stall on an edge; `still` holds. Video plates move with ease `none`, images with `sine.inOut`.
- Text: `title` is kinetic (each word rises out of a blur), centred, with a soft radial scrim; `lower` and `caption` get a bottom gradient scrim. Every scrim has its own in/out tweens.
- The last `video_fade_out` seconds dip to the background colour; `video_fade_in` (default 0) fades in from it. Leave the fade-in at 0 so frame 1 is a clean thumbnail.

## Editing rules (from real defects)

- Cut on the song: shot boundaries on beats, big moments on downbeats or `lifts`. Each shot at least ~0.8 s; at fast pace keep faces on screen ≥ 1.2 s.
- Set `focus` from the contact sheet for every shot whose subject is off-centre; a centred crop of a portrait group photo in 16:9 cuts heads.
- Never cut a face, a sign or a caption at a window edge; switch that shot to `contain` or move `focus`.
- Don't stack two dissolves on very different pictures faster than 0.2 s; use a hard cut instead.
- Text over a busy shot: move the text to a calmer shot or use `framed` look. Fix contrast warnings from `check` by changing `accent` (default `#EAC873` passes on dark).
- A clip shorter than its slot holds its last frame (`tpad`); prefer moving `in`, lowering `speed` to ≥ 0.7, or giving it a shorter slot.
- Patch scripts with exact replacements; open and write files with `encoding='utf-8', newline='\n'`; use forward slashes in generated paths.
- Two clips of the same action back to back (a card lifted in one take, lifted again in the next) read as a stuck or repeated shot. Keep one take per action.
- Handheld phone clips: set `"stabilize": true` on the shot (two-pass vidstab in prepare.py; `stab_smooth` frames, default 24 = 0.8 s). It removes the jitter and keeps slow reveals and pull-backs. Users notice the shake once the edit is otherwise clean.
- Per-format overrides: any shot key can be overridden per canvas, e.g. `"land": {"focus": [0.5, 0.4]}`, or a different `src`/`kind`/`w`/`h` (a landscape photo in place of a vertical clip in 16:9). prepare.py and build.py both apply them.
- Film-specific layers (particles, a light flash, a letterbox, a custom end card): put a module in `edit/` with `apply(film, TL, fmt, W, H)` and name it in `timeline.json` as `"fx"`; build.py calls it after the shots and texts.

## Phone footage and the renderer (from real defects)

- **iPhone video is HDR (HLG, BT.2020, 10-bit HEVC).** If any plate keeps those tags, HyperFrames 0.8.134 auto-promotes the whole render to HDR: the output is HEVC Main10 HLG (washed out or unplayable on WhatsApp), the render takes ~5x longer (it pre-extracts ~20 GB of 16-bit frames), and DOM text, scrims and blend-mode layers go missing from most frames although snapshots look fine. prepare.py now tone-maps HLG/PQ clips to SDR BT.709 (zscale + `tonemap=hable`, which matches the phone's look; `mobius` is brighter) and tags the plates bt709. Pass `--sdr` to `render` as a guard too, and check the master with ffprobe (h264, yuv420p, bt709) before sending.
- Plates are encoded with a keyframe every 30 frames (`-g 30`); with sparse keyframes the renderer warns about seek failures and frozen frames.
- `check` rejects tweens on `letterSpacing` (it snaps to whole pixels); animate scale, x or opacity instead. It also warns past ~40 elements carrying `filter: blur`, `radial-gradient` or `clip-path` (capture can go black). Use a PNG for repeated glows (particles, light leaks), not a CSS gradient on every element.
- Overlapping opacity tweens on one element are flagged; when looping a particle, start the next cycle only after the previous fade-out ends.
- Non-Latin text (Devanagari and others) needs its own `@font-face`: the renderer does not supply system fonts. On Windows, subset a face out of `C:/Windows/Fonts/Nirmala.ttc` with fontTools (`TTCollection(...).fonts[0]`, `Subsetter.populate(text=...)`) into `assets/fonts/`.

## Check, snapshot, render

```bash
cd videos/<project>
npx -y hyperframes@0.8.134 check          # 0 errors; container_overflow infos on plates are by design
rm -rf snapshots && npx -y hyperframes@0.8.134 snapshot --describe false --no-end --timeout 20000 --at 0.5,2.1,...   # one moment per shot and per text
npx -y hyperframes@0.8.134 render --sdr --crf 16 --fps 30 --workers 2 --output renders/<project>-vN.mp4   # background; ~5 min for 50 s at 1080p
```

## Mux and finish

```bash
# landscape and square
ffmpeg -i render.mp4 -i audio/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart deliver/<Name>-16x9.mp4
# portrait (HyperFrames 0.8.134 leaves a black 8 px strip at the right edge)
ffmpeg -i render.mp4 -i audio/mix.wav -map 0:v -map 1:a -vf "fillborders=right=8:mode=smear" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart deliver/<Name>-9x16.mp4
# preview under 30 MB to send (SendUserFile refuses larger)
ffmpeg -i master.mp4 -c:v libx264 -crf 21 -preset slow -c:a copy -movflags +faststart deliver/preview/<Name>-<ratio>-preview.mp4
```

Always mux the exact `mix.wav`: the renderer's own audio drifts about 1 dB quieter. After each render, sample the last 10 pixel columns of a frame with PIL for a black strip, and verify duration and size with ffprobe.

## Review checklist

- [ ] Every shot is the user's own media; nothing generated or stock.
- [ ] Master is h264 / yuv420p / bt709 (not HEVC HLG), and every text and overlay is in the rendered frames, not only in snapshots.
- [ ] No two shots show the same action; handheld shots are stabilised.
- [ ] Cuts land on beats; nothing drifts against the music by the end.
- [ ] No face, sign or text cut at an edge; focus is on the subject in every ratio.
- [ ] No black frames between shots, no black edge strips, no visible plate edge during a push or pan.
- [ ] Text readable (scrim, contrast), inside the safe area (portrait: out of the top ~8% and bottom ~13%), never over a face.
- [ ] Opening frame is a clean thumbnail; the ending fades with the song, not after it.
- [ ] Audio: -14 LUFS / -1.5 dBTP, no clicks at song_in, kept clip sound audible over the ducked song.
- [ ] Private details blurred where the user agreed.
