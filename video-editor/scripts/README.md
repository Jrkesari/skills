# Scripts

Generic versions of the netigen-video pipeline: the same engine, formats, mix and loudness code, with product capture replaced by media inventory, beat detection and an automatic beat-cut plan.

## Scaffold a film

```
<film>/                      any folder, exported as $FILM_ROOT (default: the session scratchpad)
  bin/                       ffmpeg(.exe) + ffprobe(.exe), unless they are on PATH or in $FFMPEG
  tools/                     <- scripts/tools/*
  edit/                      <- scripts/edit/*      (+ media_index.json, contact-N.jpg, timeline.json, prepared_<fmt>.json, captions.json)
  audio/                     <- scripts/audio/*     (+ song.wav, beats.json, clips/, vo/, mix_raw.wav, mix.wav)
  videos/$FILM_NAME-<ratio>/ one HyperFrames project per ratio (assets/{lib,fonts,shots}, mix.wav)
  deliver/                   masters, preview/, review/, .srt
```

```bash
export FILM_ROOT=<film> FILM_NAME=<name> FFMPEG=<film>/bin/ffmpeg.exe
cd $FILM_ROOT
python -I tools/probe.py <media folder>                  # -> edit/media_index.json, edit/contact-N.jpg
$FFMPEG -i <song> -ar 48000 -ac 2 -c:a pcm_s16le audio/song.wav
python -I tools/beats.py audio/song.wav                  # -> audio/beats.json
python -I tools/plan.py --pace medium --title "..." --end-card "..."   # -> edit/timeline.json (then hand-edit)
python -I edit/prepare.py land && python -I edit/build.py land         # per ratio
python -I audio/build_audio.py --diag && (cd audio && bash norm.sh)
```

## Files

| File | Role |
|---|---|
| tools/ffbin.py | Finds ffmpeg/ffprobe ($FFMPEG, <film>/bin, PATH) |
| tools/probe.py | Inventory of images and clips (rotation-corrected size, duration, audio, date) and numbered contact sheets; works without ffprobe |
| tools/beats.py | Tempo, beats, downbeats, bar loudness and lifts of the song |
| tools/plan.py | Beat-aligned slots, moves, dissolves, title and end card -> timeline.json |
| edit/formats.py | Canvas per ratio key, window rect per look, text zones |
| edit/prepare.py | Per ratio: images (EXIF rotate, size, contain blur-fill, blur boxes), clips (trim, speed, focus crop, blur, freeze-pad), kept clip audio |
| edit/engine.py | `Film`: window, camera-moved plates (dissolve or hard cut), kinetic words, text, VO captions, page |
| edit/build.py | timeline.json -> index.html for one ratio |
| edit/style.css, style_light.css | Dark (default) and light film themes; `accent` comes from timeline.json |
| audio/build_audio.py, norm.sh | Song + optional VO, clip sound, SFX with ducking; two-pass loudnorm to -14 LUFS |
| tools/mix.py, sfx.py | Mix helpers; procedural SFX |
| tools/tts_gemini.py, align.py | Optional voiceover and its word timing (captions) |
| tools/srt.py | .srt from VO captions or on-screen texts |
| shared/ | gsap.min.js, grain.png, fonts; copy into each project's assets |

Tested in October 2026 on synthetic media (3 photos of different aspects, a 16:9 clip with sound, a short 9:16 clip) and a 100 bpm song: probe, beats, plan, prepare and build for 16:9, 9:16 and 1:1, the mix and loudnorm all ran, and `hyperframes check` passed with 0 errors. A full render was not run (no ffprobe on that machine), so expect small fixes on the first real render.
