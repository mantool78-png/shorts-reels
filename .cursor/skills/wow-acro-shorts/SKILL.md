---
name: wow-acro-shorts
description: >-
  Builds 30–50s vertical YouTube Shorts/Reels from sports acrobatics routines
  via the local pipeline (inbox → outbox WOW_*.mp4). Use when the user drops
  a Drive link or inbox video, asks for рилс/шортс/Shorts/Reels, WOW overlay,
  tempo/balance/combined cuts, Kie music, or «сделай такой же ролик».
---

> ⚠️ С 2026-10-02 для новых роликов действует docs/CLEAN_BASE_SPEC.md. Три звука: `<slug>_orig.mp4`, `<slug>_nomusic.mp4`, `<slug>_kie.mp4` (основной для YouTube, VK и Дзен; трек Kie один раз). Вшитый WOW-оверлей устарел.

# WOW акро-шортсы

Проектный skill: сырьё из зала → вертикальный ролик 30–50 сек (9:16) в `outbox/`.
Речь с пользователем — простой русский. Не копируй пайплайн и ffmpeg в эту папку.
Типы упражнений (tempo / balance / combined) уже есть в правиле проекта — не дублируй его целиком.

Подробности: [pipeline-cli.md](references/pipeline-cli.md), [qa-checklist.md](references/qa-checklist.md), [windows-shell.md](references/windows-shell.md), [hook-templates.md](assets/hook-templates.md).

## Когда читать этот skill

Ссылка Google Drive, файл в `inbox/`, «рилс / шортс / Shorts / Reels», плашка WOW, нарезка tempo/balance/combined, музыка Kie, «сделай такой же».

## Чеклист агента

1. **Сырьё.** Ссылка Drive → скачай в `inbox/` (`.venv/Scripts/python.exe -m gdown "URL" -O "inbox/имя.mp4"`). Иначе бери самый новый ролик в `inbox/` (`--video` можно не ставить). Форматы: mp4, mov, mkv, avi, m4v, webm.
2. **Уточни у человека.** Стиль `tempo` / `balance` / `combined`; имена `--athletes`; `--city` (плашка / родина команды); `--event` (название для YouTube / место старта). Канал на видео не писать (`show_channel: false`).
3. **Таймкоды тренера.** Точка в чате `1.02` = минута 1, секунда 02 → в CLI пиши `1:02`, не `1.02` (иначе это ~1 секунда). Ручные `--clips` важнее автоанализа. Первый клип = хук. Для combined/tempo хук — выброс/сальто, не спокойный заход. Последний клип = фиксация композиции 2–3 с (поза / салют судьям).
4. **Команда** (из корня проекта, кавычки если пробелы или кириллица):

```text
.venv/Scripts/python.exe -m pipeline --video "inbox/FILE" --style combined --hook WOW --element "..." --athletes "..." --city "..." --event "..." --clips "..." --music "work/JOB/kie.mp3"
```

> С 2026-10-02 для новых роликов `--music` / Kie снова используется: один трек на ролик, файл `<slug>_kie.mp4` (оригинальный звук убран). Рядом обязательны `<slug>_orig.mp4` и `<slug>_nomusic.mp4`. Боты площадок свою музыку не генерируют. См. docs/CLEAN_BASE_SPEC.md.

`--music` ставь **только** если для того же сырья уже есть `kie.mp3` в `work/`. Иначе не передавай `--music` — пайплайн сам вызовет Kie. Можно `запуск.bat` с теми же флагами.
5. **Покажи человеку.** Файл `outbox/*.mp4`, из соседнего `.meta.json` поля `youtube_title` и `subscribe_line`. Есть ещё `.html` (таймкоды) и `.json`.
6. **Жди ок.** Не публикуй на YouTube без явной просьбы. Не рисуй название канала на кадрах.
7. **Каденс.** Ориентир: около одного шортса в день.

## Overlay (золото)

> **Устарело с 2026-10-02** для новых роликов (см. docs/CLEAN_BASE_SPEC.md): вшитый оверлей и WOW-брендинг (жёлтая полоса, хук WOW, имена и город, CTA). Раздел оставлен для старых заданий. Музыка Kie не устарела: один трек на `<slug>_kie.mp4`. Строка «звук зала mute» в таблице — старая схема одного саундтрека.

| Что | Как |
|-----|-----|
| Полоса сверху | жёлтая `#FFD60A` / `0xFFD60A` |
| Хук WOW | Impact, кегль 118 |
| Имена и город | один кегль 52; имена ЗАГЛАВНЫМИ |
| CTA в конце | 46; фразы из `config.yaml` → `subscribe_why` |
| Запрет в CTA | слово «подписка» / «подпишись»; двоеточие `:` |
| Четвёрка | `--athletes "A, B, C, D"` → две строки через middot `·`, без `&` |
| Звук зала | mute; музыка — инструментал Kie |

Город на плашке = `--city`. Турнир в title = `--event`.

## Золотые ролики (ориентир нарезки)

- **tempo:** Medvedeva / Mayorov — `17-28,38-44,1:12-1:20,1:38-1:51,2:02-2:08`
- **balance:** Aisina / Petrovsky (Russia Champs 2025) — в том ролике **без** dance connectors; на **следующих** баланс — дорожка шагов 2–3 с
- **combined pair:** Koteneva / Platonov — `1:02-1:22,0:15-0:17,0:27-0:39,0:43-0:47,1:27-1:33,2:02-2:07`
- **combined four:** Makhold Mikulin Prokhorov Korchagin; `--city Voronezh` `--event Yaroslavl`; клипы `2:13-2:22,0:12-0:15,1:10-1:22,1:32-1:40,2:27-2:35`; эталон `outbox/WOW_..._20260915_112814.mp4`

«Сделай такой же» — повтори стиль и логику хука, не копируй чужие лица на новый ролик.

## После сборки — человеку

- Где лежит mp4 (папка `outbox`).
- Предложенное название YouTube.
- Строка «зачем смотреть дальше» (еженедельный выход, не призыв «подпишись»).
- Спроси ок. Публикация — только если попросили.

## Запреты

- Секреты и `KIE_API_KEY` в чат и в skill не писать.
- Не класть копии пайплайна в `.cursor/skills/`.
- Не перезаписывать `acro-routine-types.yaml` и правило типов упражнений.
- Не ставить `disable-model-invocation`, `paths`, `globs` в этот skill.
- Не создавать агентов, commands, hooks и user rules «ради шортсов». Project-правила `.cursor/rules/wow-acro-shorts-bookends.mdc` (рамки: хук + фиксация) и `.cursor/rules/clean-base-spec.mdc` (чистая основа) — можно; другие rules не плодить.
