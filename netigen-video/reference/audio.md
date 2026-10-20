# Audio: voiceover, music, SFX, mix, loudness

Scripts: `scripts/tools/` (tts_gemini, align, lyria_rt_cue, sfx, mix) and `scripts/audio/` (build_audio, norm.sh, lines and cue examples). Run them from a separate venv (`<film>/tools/audio-venv`) that has numpy, scipy, openai-whisper and google-genai. The Gemini key comes from `GEMINI_API_KEY`, or from the netigen-draft `.env` named by `ENV_FILE`. Never print it.

## Voiceover (Gemini TTS)

- Endpoint: `POST https://generativelanguage.googleapis.com/v1beta/interactions`, header `x-goog-api-key`. The body sets model `gemini-3.8-flash-tts`, an audio response format, a text input with a `speech_metadata` style annotation, and `speech_config` voice `Charon`. The audio is base64 in `steps[].content[]`: 24 kHz mono 16-bit.
- Style note: "Calm, confident, premium enterprise narrator. Unhurried, measured pace with deliberate pauses; warm low register; crisp, precise diction; quiet authority, never salesy or excited."
- Other voices: Sadaltager, Gacrux and Alnilam (male); Kore and Sulafat (female). Fallback models: gemini-3.8-flash-lite-tts, gemini-3.1-flash-tts-preview.
- **Make one take of the whole script** (lines joined with ` <long pause> `): `tts_gemini.py lines.json vo/ [voice] [model]` writes `all.wav` only. The free tier allows 10 requests a day, and one call per line burned it on a single draft. Warn the user, or ask for a paid key, before a long session. `--retake l05,l07` redoes named lines. Files are written only after a call succeeds, so a 429 leaves no empty WAV. When the script changes, regenerate the whole take; never patch single lines, or the voice changes between lines. One sentence takes about 20 s to generate.
- Tested no-quota fallback: Kokoro local TTS (it worked, but it is not shipped in `scripts/tools`).
- Script style: short declarative lines, one per proven feature, no figures, no promises. Ask the user to listen for "Naper" and "Netigen".

## Alignment (Whisper)

- `align.py <wav> "<script>" small.en`: resample to 16 kHz, transcribe with word timestamps, `initial_prompt` set to the brand names ("Netigen, Nexus, Naper, Nimbus, Neuron"), `condition_on_previous_text=False`, then match the words to the script with difflib. Whisper heard "hours" as "ours"; matching keeps the script's spelling.
- `align.py vo/all.wav --lines lines.json --out vo_timing.json` slices the aligned words per line by word count into the records `build_audio.py` reads (`id, text, start, end, words`). Whisper runs with `fp16=False`.
- A 0 s gap between two lines is a missed boundary. Find the real silence in a 10 ms RMS envelope and record it in `timeline.json` under `vo_fix`.
- Splice each line at **start − 0.22 s to end + 0.24 s**, with a 15 ms fade-in and a 120 ms fade-out. Aligners report word starts 90-170 ms late, and a tighter pre-roll clipped both "Netigen" onsets.

## Music (Lyria RealTime)

- `lyria_rt_cue.py out.wav cue.json`: model `models/lyria-realtime-exp` via google-genai (`api_version v1beta`), steered by weighted prompts and `LiveMusicGenerationConfig` (bpm 100, scale D_MAJOR_B_MINOR, guidance 4, density, brightness, mute_drums). Steps fire on the audio time received, so sections line up with the file. Output is 48 kHz stereo.
- Time the cue steps to the scene boundaries: an intro, a build at the reveal, the main section, a lift before the unify beat, and a resolve on the end card. The 61 s example is `scripts/audio/cue3.json`.
- Prompt for airy, crisp timbres (shimmering pad, felt piano, plucked arpeggio, brightness 0.6-0.75). A "deep warm analog pad, sub bass" cue came out muddy, with a spectral centroid of 100-300 Hz.
- Make **two takes**. Analyse each in 3 s windows (RMS dB, spectral centroid by STFT nperseg 2048, energy below 120 Hz) and pick the one that builds through the middle and resolves at the end. Then listen.
- Paid alternative: `lyria-3.5` with a timestamped structure prompt, about $0.08 per song.

## SFX (procedural, numpy only)

`sfx.py`: whoosh(0.8, 400, 5000), whoosh_soft(0.6, 600, 3500), riser(dur), impact(2.4), click, shimmer(1.8). Gains run -10 to -16 dB. Put a whoosh about 0.15 s before each scene cut, a riser into the reveal and into the end card, and an impact plus shimmer on the end card. Positions live in `timeline.json` under `sfx`.

## Mix (`build_audio.py`)

- Reads `timeline.json`: `vo_take`, `vo_timing`, `vo` (line start times), `vo_fix`, `music`, `music_offset` and `sfx`. Writes `mix_raw.wav` and `edit/captions.json` (word times in film time).
- Music at -4 dB, starting at `music_offset` so its outro lands on the end card, with a 0.25 s fade-in and a 3 s fade-out (^1.5 curve). Ducked by `duck_curve(vo, -10, 0.06, 0.5)`. Peak-scaled to 0.89.
- `--diag` reference values: VO RMS in speech about -15.9 dB, music under speech about -30 dB, music in gaps about -27 dB, SFX about -26 dB, peak -1.0 dB.
- Use forward slashes in JSON paths (`"vo_v2/all.wav"`): backslashes gave `Invalid \escape`.

## Loudness (`norm.sh`)

Two-pass loudnorm: pass 1 measures, pass 2 applies `loudnorm=I=-14:TP=-1.5:LRA=11:measured_*...:linear=true,aresample=48000` and writes pcm_s16le `mix.wav`. That gave -14.5 LUFS and -1.5 dBTP. Copy `mix.wav` into every format's project. All formats share **one** mix. Check the muxed master with `ffmpeg -i master.mp4 -af ebur128=peak=true -f null -` (target about -14.4 LUFS, LRA about 3).
