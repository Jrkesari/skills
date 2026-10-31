# skills

[Claude Code](https://claude.com/claude-code) skills, MIT licensed.

| Skill | What it does |
|---|---|
| [video-editor](video-editor/SKILL.md) | Edits your own clips and photos into one finished video cut to a song you provide: beat-synced cuts, Ken Burns moves on stills, dissolves, titles and an end card, optional voiceover and captions, in any aspect ratio (16:9, 9:16, 4:5, 1:1, 21:9 or custom) |
| [fix-android-tv-lag](fix-android-tv-lag/README.md) | Finds out why an Android TV or Google TV is slow or keeps restarting (crash, freeze or power loss; memory pressure; damage checks) and fixes what can be fixed over Wi-Fi ADB: removes apps you never open, switches off features you don't use, optimises apps, then restarts and verifies, with every change logged and undoable |

## Install

As a Claude Code plugin marketplace, installing only the skills you want:

```
/plugin marketplace add Jrkesari/skills
/plugin install fix-android-tv-lag@jrkesari-skills
/plugin install video-editor@jrkesari-skills
```

In OpenAI Codex, which reads the same marketplace file:

```bash
codex plugin marketplace add Jrkesari/skills
codex plugin add fix-android-tv-lag@jrkesari-skills
```

Or clone the repo as your user-level skills folder, so every skill loads in every Claude Code session:

```bash
git clone https://github.com/Jrkesari/skills ~/.claude/skills   # into an empty ~/.claude/skills
# or, when ~/.claude/skills already holds other skills:
cd ~/.claude/skills && git init -b main && git remote add origin https://github.com/Jrkesari/skills && git fetch origin && git checkout main
```

To use one skill in one project instead, copy its folder into that project's `.claude/skills/`.

Then ask Claude Code for what you want, for example "make a 30 second 9:16 reel from ~/Videos/goa cut to ~/Music/song.mp3". The skill asks for anything the request leaves open (ratios, length, pace) before it renders.

## Requirements (video-editor)

- Python 3.11 with numpy, scipy and Pillow
- Node 22+ (HyperFrames runs through `npx`)
- ffmpeg on `PATH` or in `$FFMPEG`; if neither is there, the skill asks before fetching a local build into the project folder
- Optional: `GEMINI_API_KEY` for an AI voiceover

## Requirements (fix-android-tv-lag)

- Python 3.8+ (standard library only)
- Android SDK Platform-Tools (`adb`); the skill asks before installing it
- The TV on the same network, with USB debugging on (the skill walks you through it)

## Add a skill

1. Create `<name>/SKILL.md`: frontmatter with `name` and `description`, then the instructions.
2. Allow it in `.gitignore` with two lines, `!/<name>/` and `!/<name>/**`. Skills installed by other tools stay ignored.
3. Add a row to the table above.
4. Add a plugin entry to [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) (`"source": "./"`, `"skills": ["./<name>"]`), then check it with `claude plugin validate .`.

## Licence

[MIT](LICENSE). Bundled third-party files keep their own licences: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
