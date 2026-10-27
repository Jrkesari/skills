# Audio and delivery

Scripts: `scripts/tools/beats.py`, `mix.py`, `sfx.py`, `tts_gemini.py`, `align.py`, `srt.py`; `scripts/audio/build_audio.py`, `norm.sh`.

## The user's song

- Convert once to `audio/song.wav` (48 kHz stereo PCM). Keep the user's original file untouched.
- `beats.py` (numpy/scipy, no extra installs): log-band spectral flux, tempo by autocorrelation (60-180 bpm, mild prior near 115), dynamic-programming beat tracker, then a half-beat phase check against the kick band (so it locks on kicks, not hats), downbeats from the strongest kick phase, bar loudness, and `lifts` (bars ≥ 3 dB louder than the 4 before). Tested on a synthetic 100 bpm track: 99.8 bpm, beats within ~12 ms of the kicks, downbeats correct.
- If the tempo reads double or half (common on ballads and trap), re-run with `--bpm`. For songs with tempo changes or no drums, cut on `bars` loudness and phrases by ear instead of the grid.
- `song_in`: `0` (from the start), `auto` (loudest stretch that fits, starting on a downbeat), `end` (finish on the song's real ending; best for short films of songs with a clean outro), or seconds.
- Shorter than the song section allows: lift out one whole repeat (a verse, a chorus pass) rather than trimming mid-phrase. Find the song's cycle length by matching the spectrogram just before a cut point P against the one just before P + D (the best D wins; on a chanted shloka it was 16.3 s where word timings suggested 15.8), cut at P inside a held note or gap, join at P + D with an 80 ms crossfade into `audio/song_edit.wav`, set `song` to it and `song_in` to 0, and re-check the lyrics across the join with whisper. Cuts after the join move by -D in film time.
- Fades: `fade_in` 0 from the start, 0.25 s otherwise; `fade_out` 1.0 s when ending on the real ending, else about 2.5 s. The picture dips with it (`video_fade_out`).

## Mix (build_audio.py)

- Song at `song_gain` dB, never stretched. Optional voiceover, kept clip sound (`keep_audio` shots, extracted by prepare.py into `audio/clips/<id>.wav`, placed at the shot's start with `audio_gain`), and SFX from `timeline.json` `sfx` (`whoosh`, `whoosh_soft`, `riser` with `dur`, `impact`, `shimmer`, `click`; gains -10 to -16 dB). Most music edits need no SFX: the song carries it.
- Ducking: the song dips -10 dB under voiceover and `clip_duck` dB (default -8) under kept clip sound.
- `norm.sh`: two-pass loudnorm to -14 LUFS / -1.5 dBTP into `audio/mix.wav` (the test came out at -14.7 LUFS / -1.4 dBTP). One mix serves every ratio; copy it into each project's `assets/mix.wav`.

## Optional voiceover

Only when the user asks. Write short lines in `audio/lines.json`, generate the whole script as **one** take (`tts_gemini.py lines.json audio/vo/`; Gemini free tier is 10 requests a day; `TTS_STYLE` sets the delivery), align it (`align.py audio/vo/all.wav --lines lines.json --out audio/vo_timing.json`, needs openai-whisper; `VO_NAMES` lists proper names), then set `vo_take`, `vo_timing` and `vo` (line id -> film start time) in timeline.json. Captions are built from the word times and show on screen automatically; list line ids in `no_captions` to skip some. The user's own recorded voiceover works the same way: put it at `audio/vo/all.wav` and align it.

## Deliver

- `deliver/<Name>-<ratio>.mp4` masters (verified with ffprobe), `deliver/preview/*-preview.mp4` under 30 MB (sent with SendUserFile; check it actually arrived), `deliver/<name>.srt` when there is text or voiceover (`srt.py`).
- Optional post caption, only if asked: a strong first line, one or two lines of story, a few hashtags; never invent facts about the people or places shown.
- Hand-off: paths; shots dropped, reused or frozen and why; the song window used; any blur applied; the copyright line (commercial songs may be muted or claimed by platforms); then the aspect-ratio question.
