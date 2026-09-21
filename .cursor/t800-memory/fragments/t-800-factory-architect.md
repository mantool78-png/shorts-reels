=== T-800 FACTORY-ARCHITECT (spec) ===

**Статус:** PASS
**Агент:** t-800-factory-architect
**Этап:** architect
**Дата:** 2026-09-20
**Slug:** acro-short-ending
**Agent ID:** 318aa402-fce2-4f26-8547-7d112536bcd7

Старый fragment (wow-acro-shorts, 2026-09-15) перезаписан. Spec не reuse.

## Сделано
- artifact = rule, surface = cursor-workspace
- path = .cursor/rules/wow-acro-shorts-bookends.mdc
- frontmatter: description exact + alwaysApply true; no globs
- body ru ≤25: MUST/NEVER/pointer/analogy
- companion: 2 replace_once в SKILL.md + 1 checkbox в qa-checklist.md
- registry_patch: null; browser_capability: forbidden
- spec YAML записан parent lead после Ask-mode architect

## Артефакты
- factory-briefs/acro-short-ending.spec.yaml
- .cursor/rules/wow-acro-shorts-bookends.mdc (planned, builder)
- SKILL.md + qa-checklist.md (planned patches, builder)

## Handoff
summary: Builder создаёт .mdc и минимальные diffs. Integrator без registry. Auditor обязателен.
registry_patch: null
browser_capability: forbidden

## kb_usage
- knowledge-base/13-agent-factory/agent-vs-skill-vs-command.md
- knowledge-base/13-agent-factory/subagent-creation-guide.md (Rule)
- knowledge-base/03-kontekst/rules.md
- shared/t-800-factory-contract.md
- shared/artifact-surfaces-contract.md
- templates/rule.mdc.template

## kb_write
- (пусто)

## Блокеры
- нет (spec и fragment на диске)
