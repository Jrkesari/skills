# Review, privacy check, and delivery

## Review: one pass, then at most one recheck

1. Extract frames at 2 fps from the **muxed masters**: `ffmpeg -i master.mp4 -vf "fps=2,scale=1280:-1" review/vN/land/f_%03d.jpg` (use `scale=720:-1` for portrait). Frame `f_NNN` sits at (NNN-1)×0.5 s.
2. Run one Workflow: reviewers split by format and frame range, each reading every frame, then one refute-verifier per finding that is not low ("default to real=false if uncertain", returning `{real, reason}`). Each reviewer covers four lenses: privacy and real values; claims against the verified research (`research/capabilities.md`, `nexus.md`, `naper.md`, `nimbus.md`, `brand.md` and the website's Neuron copy); visual quality; and audio, caption and picture sync. Reviewers must not edit files. They may pull full-resolution frames with `ffmpeg -ss <t> -i master.mp4 -frames:v 1` into `deliver/review/scratch/` and zoom 3-4× to test legibility. Quote the user's request verbatim in every prompt. The prompt must also carry the VO script, the scene times, and the **known and accepted** list: website demo data (Maya Chen, example.com, demo dollar figures), frames caught mid-dissolve, the TIME-LAPSE tag, captions highlighting word by word, and a column cut cleanly at a gap in narrow canvases.
3. Fix only the confirmed findings, rebuild, snapshot the touched moments, render once, mux, deliver. A recheck pass, if one is needed, lists the numbered earlier defects and asks fixed yes/no plus any new defects.
4. Read workflow results by `json.load` of the task output file (`d['result']`), or from `subagents/workflows/<id>/journal.jsonl`. Run Python with `-X utf8` when printing model text on Windows.

The user's patience is the constraint. Send a preview as soon as the first render exists. Never start a third review round without asking.

## Pre-render checklist (grade every film against it)

- [ ] Every shot traces to a live capture or a netigen.ai scene. Nothing is invented, and no real UI text is painted over.
- [ ] No real values: costs, tokens, latencies, ratings, counts, client data. No readable real chart shapes. Real answer figures stay out of frame where possible; public, cited research is acceptable.
- [ ] No real names, emails, avatars, tenant IDs or invite links. Forms use example.com and all-zero GUIDs.
- [ ] No feature marked "soon" or "rolling out" is shown or narrated as live.
- [ ] No product failure text on screen ("LibreOffice was unavailable", error states).
- [ ] No text cut mid-word at a window edge, and no line sliced at the top or bottom.
- [ ] No blank columns, empty lower halves, sidebar slivers or backdrop bands.
- [ ] No black or dark strips at the frame edges (probe them with PIL after the render).
- [ ] Callouts match the screen at that moment. TIME-LAPSE marks every shot sped up more than 3x and covers nothing.
- [ ] Captions: accurate to the VO, no word alone on a line, inside the safe area, no overlap at handoffs.
- [ ] Audio: brand-name onsets not clipped, VO clear over the music, -14 LUFS / -1.5 dBTP, picture cuts on the spoken words.
- [ ] Opening frame (the likely thumbnail) is clean, and the hook works with the sound off.
- [ ] Logo geometry matches netigen-mark.svg, and colour pulses ease rather than flicker.

## Privacy rules

- Never print or copy session tokens, JWTs, API keys or connection strings. Name-based redaction (SECRET, KEY, TOKEN) missed a `DATABASE_URL` with an embedded password: print env key names only.
- Blur goes into the pixels before media reaches the HyperFrames project (ffmpeg gblur for clips, PIL for stills), never as an HTML overlay.
- Delete `capture/token.txt` and `capture/state.json` after the film.

## Deliverables

- `deliver/<Name>-<ratio>.mp4` per ratio (1920×1080, 1080×1920, ...), verified with ffprobe.
- `deliver/preview/<Name>-<ratio>-preview.mp4` (crf 21, under 30 MB) to send with SendUserFile. Give the master paths for posting.
- `deliver/<name>.srt`, built from captions.json (end +0.35 s, integer-millisecond timestamps).
- `deliver/linkedin-caption.md`.

## LinkedIn caption template

```
Introducing Netigen: one AI platform that turns your team's questions into finished work.

Four layers, working as one system:

Naper: admins decide which agents, apps and models each team gets, with seats and spend limits built in.

Nexus: the AI workspace. Ask in plain words, research the live web with cited sources, turn the answer into a slide deck, and schedule it to run again.

Neuron: answers from your business. Your vocabulary and metric rules as a semantic layer, checked read-only queries, and agents that work from your data.

Nimbus: see what every answer cost, how fast it came back and how people rated it.

Every screen shows Netigen's real interface: live recordings of Nexus and Naper, plus the product scenes from netigen.ai with demo data. Voiceover and music were generated with AI.

See it at netigen.ai

#EnterpriseAI #AIAgents #Netigen
```

Rules: a strong first line, the value, one paragraph per layer or feature shown, a natural CTA, and a few hashtags. Never promise reach or virality, and never invent claims. **The provenance sentence must match this film's real sources.** Rewrite it whenever a shot's source changes. Post from the Netision LinkedIn page; the product is Netigen.

## Hand-off message

1. What was delivered: the paths, the previews sent, the caption text and the SRT.
2. Before you post: listen for the Naper and Netigen pronunciation, list scenes dropped and why, say which screens are website scenes, and flag dated UI text (old model names in the picker).
3. Services started or restarted, with an offer to stop them.
4. The last question: "Do you want another aspect ratio (16:9, 9:16, 1:1, 4:5, 16:10, other)?"
