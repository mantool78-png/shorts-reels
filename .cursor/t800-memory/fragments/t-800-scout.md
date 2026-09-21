# t-800-scout — acro-short-ending

Дата: 2026-09-20
Агент: b49d33b2-57b6-402c-881d-392d0a4d3e1a

```yaml
scout_report:
  slug: acro-short-ending
  date: 2026-09-20
  manifest_age_days: 80
  status: stale
  last_full_sync: 2026-07-02
  coverage_map_last_synced: 2026-07-06
  last_coverage_report: 2026-07-24
  last_coverage_missing: 0
  audit_coverage_rerun: false
  new_findings:
    - "Rules API 2026 intact: .cursor/rules/*.mdc; frontmatter alwaysApply|description|globs; .md ignored"
    - "alwaysApply:true ignores globs+description for activation"
    - "This workspace has no .cursor/rules/ folder; acro-routine-types.mdc does not exist"
    - "Start/hook is skill-only (SKILL.md + qa-checklist), not a project rule"
    - "wow-acro-shorts factory do_not 'не создавать rules' overridden by explicit user request"
  recommended_research: true
  recommended_maintainer: true
  block_factory: false
  rule_format_ok: true
  recommended_artifact: rule
  artifact_surface: cursor-workspace
  artifact_path_hint: .cursor/rules/acro-short-ending.mdc
  skill_companion: true
  start_hook_already_exists: skill_only
  always_apply_recommended: true
  no_globs: true
  do_not_reuse_old_brief: acro-routine-types.yaml
  fragment_written: true
```

Хук начала — только skill. Для финала нужен project rule. Factory не блокировать.
