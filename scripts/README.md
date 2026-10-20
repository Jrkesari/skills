# Scripts: the working code of the October 2026 launch film

These are copies of the scripts that made the film, with machine paths turned into `ROOT = $FILM_ROOT` (the film folder) and personal names moved into the `CAP_SENSITIVE` env var. Copy them into a new film folder and adapt them; `edit/build.py` especially is the full story of that film.

## Scaffold a new film

```
<film>/                      any folder you choose, exported as $FILM_ROOT (e.g. under the session scratchpad)
  bin/                       ffmpeg.exe, ffprobe.exe (BtbN win64 gpl build; query the release API for the asset name)
  capture/                   <- scripts/capture/*   (takes/, stills2x_root/ are created by the scripts)
  audio/                     <- scripts/audio/*     (VO takes, music takes, mix.wav)
  tools/                     <- scripts/tools/*     (+ audio-venv/ with numpy scipy openai-whisper google-genai)
  edit/                      <- scripts/edit/*      (timeline.json, media.json, captions.json, build.py)
  shared/                    <- scripts/shared/*    (+ gsap.min.js, grain.png, fonts/)
  research/                  research agents write <key>.md here
  videos/$FILM_NAME-<ratio>/ one HyperFrames project per aspect ratio (assets/{lib,fonts,clips,stills,mix.wav});
                             after `hyperframes init`, copy shared/{gsap.min.js,grain.png,netigen-mark*.svg} -> assets/lib/ and shared/fonts/* -> assets/fonts/
  deliver/                   masters, preview/, review/vN/, caption, srt
  .claude/skills/            the HyperFrames skills (installed with `npx skills add heygen-com/hyperframes ...`)
```

Environment for every run:

```bash
export FILM_ROOT=<film>
export FILM_NAME=netigen-<topic>          # project folders become videos/$FILM_NAME-16x9, -9x16, -1x1 ...
export FFMPEG=$FILM_ROOT/bin/ffmpeg.exe
export CAP_THEME=light                       # or dark
export CAP_SENSITIVE='First|Last|@company\.com|Teammate'   # the recording account's and visible people's names; never commit it
export GEMINI_API_KEY=...                    # or ENV_FILE=<netigen-draft>/.env ; never print it
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_FFMPEG_PATH=$FILM_ROOT/bin/ffmpeg.exe HYPERFRAMES_FFPROBE_PATH=$FILM_ROOT/bin/ffprobe.exe
```

## What each file does

| File | Role |
|---|---|
| capture/lib.py | `FORMATS` (one viewport per aspect ratio), `context()` (headless Chromium, the session, the theme, no dev badge), `Take` (recorder, labelled events, privacy boxes), `still()`, `type_human()`, `wait_turn()` |
| capture/rec.py | CDP screencast recorder that rebuilds a constant-30-fps MP4 from frame timestamps |
| capture/session.py | Injects the user's own `better-auth.session_token` from token.txt and saves state.json |
| capture/flow_*.py | One live flow per script: chat/research/deck/mail, sched, naper, nimbus, extras |
| capture/stills*.py | 2x stills from saved chat URLs; the Naper org dialog; website Neuron steps; dense 3x website-scene sweeps |
| capture/explore.py, survey.py | Accessible names and boxes of every control; screenshots of every route |
| tools/tts_gemini.py | Gemini TTS (whole script in one take plus per-line retakes) |
| tools/align.py | Whisper word timestamps matched to the script |
| tools/lyria_rt_cue.py | Lyria RealTime music steered by cue.json |
| tools/sfx.py, mix.py | Procedural SFX; mix helpers (place, duck_curve, fade) |
| audio/build_audio.py, norm.sh | Mix from timeline.json plus captions.json; two-pass loudnorm to -14 LUFS |
| audio/lines_v2.json, cue3.json | The film's VO script and music cue, as examples |
| edit/formats.py | Canvas size, layout family (land or port) and project folder for every aspect-ratio key |
| edit/engine.py | `Film`: windows, camera-moved plates, kinetic words, captions, page writer |
| edit/build.py | The story, with land and port layouts. Copy it and edit the scenes |
| edit/gen_media.py, prepare_media.py | Which take slice fills which plate; cutting, speed, blur, patch, edge fill |
| edit/timeline.json | Duration, VO placements, scenes, SFX: the only source of timing |
| edit/style.css, style_dark.css | Light and dark film themes (Netigen tokens and fonts) |
| shared/light-theme.css | The product's light tokens, mapped onto the website's scene variables |
| shared/netigen-mark*.svg | The real mark, from netigen packages/ui logo.tsx |

Every Python file passes pyflakes, and the edit chain (gen_media, prepare_media, build) was re-run against the original film and reproduced its index.html byte for byte. The capture and audio scripts were not re-run in a fresh folder, so expect small path fixes on first use. Check before any flow that the repos' UI copy still matches the locators (`explore.py`).
