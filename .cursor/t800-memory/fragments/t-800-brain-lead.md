# t-800-brain-lead — acro-short-ending

Дата: 2026-09-20
Агент: b1c6638a-f269-48f3-9ba9-ff0540bf0249
Domain brain: t-800-brain-context b236ad5f-4338-418d-9637-6cf004635ae3

```yaml
brief_for_factory:
  slug: acro-short-ending
  artifact_type: rule
  path: ".cursor/rules/wow-acro-shorts-bookends.mdc"
  alwaysApply: true
  no_globs: true
  frontmatter:
    description: "Рамки шортса: первый клип — хук, последний — фиксация 2–3 с"
    alwaysApply: true
  start_hook_already_exists: skill_only
  live_pass:
    source: "inbox/IMG_6832.MOV"
    last_clip: "1:43.5-1:46"
    duration_s: 2.5
  skill_companion_edits:
    - ".cursor/skills/wow-acro-shorts/SKILL.md"
    - ".cursor/skills/wow-acro-shorts/references/qa-checklist.md"
  block_factory: false
  kb_stale_days: 80
```

Вердикт: одно project-rule про начало (хук/выброс) и конец (фиксация 2–3 с). Factory не блокировать.
