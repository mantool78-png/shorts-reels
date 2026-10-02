# Для агентов

Главная спецификация новых роликов — [docs/CLEAN_BASE_SPEC.md](docs/CLEAN_BASE_SPEC.md). Она важнее шагов вшитого WOW-оверлея в `.cursor/skills/wow-acro-shorts`.

На каждый ролик Cursor отдаёт только два файла: `<slug>_kie.mp4` и `<slug>_facts.json`. Трек Kie генерируется один раз; `<slug>_kie.mp4` — основной файл для YouTube, VK и Дзен. `<slug>_orig.mp4` и `<slug>_nomusic.mp4` не делать. Боты площадок свою музыку не делают.
