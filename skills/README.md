# Agent skills

Claude Code loads `.claude/skills/` automatically.

For Hermes (or any other agent host), copy or symlink these folders into that
host's skills directory:

- `alphaclip-hooks` — title / hook variants for the three presets
- `alphaclip-disclaimers` — financial-content and copyright templates

Both skills assume the operator owns the source media and that the clip is
**not financial advice**.
