# Для агентов

Главная спецификация новых роликов — [docs/CLEAN_BASE_SPEC.md](docs/CLEAN_BASE_SPEC.md). Она важнее шагов вшитого WOW-оверлея в `.cursor/skills/wow-acro-shorts`.

На каждый ролик Cursor отдаёт три файла: `<slug>_orig.mp4`, `<slug>_nomusic.mp4` и `<slug>_kie.mp4`. Трек Kie генерируется один раз; `<slug>_kie.mp4` — основной файл для YouTube, VK и Дзен. Боты площадок свою музыку не делают.
