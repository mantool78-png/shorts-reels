# Windows / PowerShell

Корень проекта часто с пробелами и кириллицей (`Рабочий стол`, `Рилсы Шортсы`). Все такие пути — в кавычках.

## Python пайплайна

```powershell
.venv/Scripts/python.exe -m pipeline --video "inbox/файл с пробелом.mp4" --athletes "Medvedeva/Mayorov"
```

В PowerShell обратный слэш тоже работает, если путь в кавычках:

```powershell
".venv\Scripts\python.exe" -m pipeline --video "inbox\FILE.mp4"
```

Предпочтительно в skill и командах: слэш `/`, кавычки вокруг аргументов с пробелами.

## Drive → inbox

```powershell
.venv/Scripts/python.exe -m gdown "https://drive.google.com/..." -O "inbox/source.mp4"
```

Файл должен появиться в `inbox/` до запуска пайплайна.

## Рабочая папка

Сначала `cd` в корень проекта (там лежат `inbox`, `outbox`, `pipeline`, `.venv`). Не запускай `-m pipeline` из чужой папки.

## Кавычки `--clips`

Весь список отрезков — одна строка в кавычках:

```text
--clips "17-28,38-44,1:12-1:20,1:38-1:51,2:02-2:08"
```

Не разбивай запятые на отдельные аргументы.

## Не делать

- В markdown-ссылках skill только прямой слэш: `references/windows-shell.md`
- Ключ Kie в команду и в чат не вставлять
- Не полагаться на незакавыченный путь с пробелами или кириллицей
