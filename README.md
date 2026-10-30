# skills

My personal Claude Code skills. This repo is cloned as `~/.claude/skills`, so every skill folder here is loaded by Claude Code in every session.

| Skill | What it does |
|---|---|
| [netigen-video](netigen-video/SKILL.md) | Makes Netigen product videos (one feature, one layer, or the whole platform) from real UI, in any aspect ratio, with AI voiceover, music, captions and a LinkedIn caption |
| [video-editor](video-editor/SKILL.md) | Edits your own clips and photos into one video cut to a song you provide: beat-synced cuts, Ken Burns moves, titles, optional voiceover and captions, any aspect ratio |

## Set up on a new machine

```bash
git clone https://github.com/Jrkesari/skills ~/.claude/skills   # into an empty ~/.claude/skills
# or, when ~/.claude/skills already holds other skills:
cd ~/.claude/skills && git init -b main && git remote add origin https://github.com/Jrkesari/skills && git fetch origin && git checkout main
```

## Add a skill

1. Create `~/.claude/skills/<name>/SKILL.md` (frontmatter `name` and `description`, then the instructions).
2. Allow it in `.gitignore` with two lines: `!/<name>/` and `!/<name>/**`. Skills installed by other tools stay ignored.
3. Add a row to the table above, then commit and push.
