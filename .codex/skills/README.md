# Codex Team Skills

This folder is the Team Config location for **shared skills**.

## How skills work (practical)

- Each skill lives in its own folder and must contain a `SKILL.md`.
- Skills committed here are available to everyone who runs Codex in this repo (CLI + IDE).

## Suggested workflow for Sirvist

1. Prototype machine-local skills in `~/.codex/skills/`.
2. When a skill stabilizes, copy it into `.codex/skills/<SkillName>/SKILL.md` so the team shares it.
3. Use `[[skills.config]]` in `.codex/config.toml` to disable/enable specific skills without deleting them.
