# CLI пайплайна

Запуск из корня проекта (папка «Рилсы Шортсы»).

```text
.venv/Scripts/python.exe -m pipeline [флаги]
```

Либо `запуск.bat` с теми же флагами (после установки библиотек ставит паузу).

Исходник флагов: `pipeline/run.py` → `build_parser()`.

## Флаги

| Флаг | Смысл |
|------|--------|
| `--video` | Путь к ролику. Если нет — самый новый файл в `inbox/` |
| `--hook` | Текст хука на первом кадре. По умолчанию `WOW` |
| `--athletes` | Имена. Пара: `Фамилия/Фамилия` или как принято. Четвёрка: `A, B, C, D` |
| `--event` | Турнир / город старта — в название YouTube |
| `--city` | Город команды — крупно на плашке |
| `--element` | Элемент (бросок, сальто…) — может попасть в title рядом с хуком |
| `--music` | Свой mp3 вместо нового Kie. Только если уже есть `work/.../kie.mp3` для того же сырья |
| `--from-json` | Пересборка по готовому `highlights.json` |
| `--clips` | Ручные отрезки, первый = хук. Пример: `17-28,38-44,1:12-1:20` |
| `--style` | `tempo` / `balance` / `combined` (также русские синонимы: темп, баланс, комби) |
| `--skip-kie` | Не вызывать Kie AI |
| `--skip-music` | Собрать без музыки |
| `--self-test` | Прогон на тестовом ролике |

## Папки

| Папка | Что лежит |
|-------|-----------|
| `inbox/` | Сырьё с ковра |
| `work/` | Джобы: копия сырья, `kie.mp3`, `highlights.json` |
| `outbox/` | Готовый `WOW_*.mp4` + `.meta.json` + `.html` + `.json` |

Целевая длина: 30–50 сек (`config.yaml`: `target_min_sec` / `target_max_sec`).

## Таймкоды `--clips`

Пайплайн понимает `17`, `17.5`, `1:38`, `1:02-1:22`.

В чате тренер часто пишет `1.02` = **1:02**. Перед CLI замени точку-минуты на двоеточие.

Ручные `--clips` отключают автопоиск движения.

## Музыка

- Нет `--music` и нет `--skip-kie` → Kie instrumental (ключ из `.env`, не светить).
- То же сырьё уже собрали и есть `work/JOB/kie.mp3` → `--music "work/JOB/kie.mp3"`.
- `--skip-music` — тишина (зал и так mute на нарезке).

## Пример combined four

```text
.venv/Scripts/python.exe -m pipeline --video "inbox/FILE.mp4" --style combined --hook WOW --athletes "Makhold, Mikulin, Prokhorov, Korchagin" --city "Voronezh" --event "Yaroslavl" --clips "2:13-2:22,0:12-0:15,1:10-1:22,1:32-1:40,2:27-2:35"
```

## Что читать после прогона

`outbox/*.meta.json`: `youtube_title`, `subscribe_line`, `description`, `output`, `job`, `music`.
