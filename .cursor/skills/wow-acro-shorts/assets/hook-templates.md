# Шаблоны хука и CTA

## Хук на кадре

Обычно `--hook WOW`. Можно добавить элемент в title через `--element` (бросок, сальто, пирамида) — на плашке хук всё равно короткий.

Не ставь двоеточие в текст, который идёт в ffmpeg drawtext.

## Имена

| Состав | `--athletes` | На экране |
|--------|----------------|-----------|
| Пара | `Koteneva/Platonov` или `Koteneva / Platonov` | одна или две строки по `/` |
| Четвёрка | `Makhold, Mikulin, Prokhorov, Korchagin` | `MAKHOLD · MIKULIN` / `PROKHOROV · KORCHAGIN` |

Не пиши `&` между фамилиями четвёрки.

## Плашка vs YouTube

- `--city Voronezh` → город на плашке
- `--event Yaroslavl` → в `youtube_title`, не обязан дублировать канал

## CTA (конец ролика)

Пайплайн сам берёт следующую фразу из `subscribe_why` **до** сборки (`next_subscribe_line`). Не подменяй на «Подпишись:».

Колода (еженедельный выход):

- Новые ролики каждую неделю.
- Такие выступления выходят регулярно.
- Следующие WOW уже на этой неделе.
- Новые программы постоянно.
- Каждую неделю новые моменты с ковров.
- Регулярно новые пары, турниры и элементы.
- Здесь новые ролики идут постоянно.
- Следующие выступления — каждую неделю.
- Новые шортсы каждую неделю, без пауз.

Тире `—` в фразе допустимо; двоеточие нет (drawtext).

## Золотые `--clips`

**Tempo Medvedeva/Mayorov**

```text
--style tempo --athletes "Medvedeva/Mayorov" --clips "17-28,38-44,1:12-1:20,1:38-1:51,2:02-2:08"
```

**Balance Aisina/Petrovsky** — без dance connectors в том ролике.

**Combined pair Koteneva/Platonov**

```text
--style combined --athletes "Koteneva/Platonov" --clips "1:02-1:22,0:15-0:17,0:27-0:39,0:43-0:47,1:27-1:33,2:02-2:07"
```

Первый отрезок `1:02-1:22` — хук (сильный кусок).

**Combined four Makhold 20260915_112814**

```text
--style combined --athletes "Makhold, Mikulin, Prokhorov, Korchagin" --city "Voronezh" --event "Yaroslavl" --clips "2:13-2:22,0:12-0:15,1:10-1:22,1:32-1:40,2:27-2:35"
```
