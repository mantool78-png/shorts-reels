from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from pipeline.analyze import analyze_video, highlights_from_ranges
from pipeline.assemble import assemble
from pipeline.config import load_config
from pipeline.paths import INBOX, MUSIC, OUTBOX, WORK
from pipeline.preview import write_preview
from pipeline.subscribe import next_subscribe_line, youtube_description
from pipeline.textutil import parse_clip_ranges, slug, write_json


VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}
STYLE_ALIASES = {
    "tempo": "tempo",
    "темп": "tempo",
    "темповое": "tempo",
    "динамическое": "tempo",
    "balance": "balance",
    "баланс": "balance",
    "балансовое": "balance",
    "combined": "combined",
    "комби": "combined",
    "комбо": "combined",
    "комбинированное": "combined",
}
STYLE_RU = {
    "tempo": "темповое",
    "balance": "балансовое",
    "combined": "комбинированное",
}


def normalize_style(raw: str | None) -> str | None:
    if not raw:
        return None
    return STYLE_ALIASES.get(raw.strip().lower())


def ensure_folders() -> None:
    for folder in (INBOX, OUTBOX, WORK, MUSIC):
        folder.mkdir(parents=True, exist_ok=True)
        keep = folder / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")


def newest_inbox() -> Path | None:
    files = [p for p in INBOX.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def find_local_music() -> Path | None:
    files = [
        p
        for p in MUSIC.iterdir()
        if p.is_file() and p.suffix.lower() in {".mp3", ".wav", ".m4a", ".aac"}
    ]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def youtube_title(meta: dict) -> str:
    hook = meta.get("hook") or "WOW"
    if meta.get("element"):
        hook = f"{hook} {meta['element']}"
    athletes = meta.get("athletes") or ""
    event = meta.get("event") or ""
    parts = [hook]
    if athletes:
        parts.append(athletes)
    if event:
        parts.append(event)
    return " — ".join(parts) + " #Shorts"


def run_job(args: argparse.Namespace) -> Path:
    ensure_folders()
    cfg = load_config()
    style = normalize_style(getattr(args, "style", None))
    if style:
        cfg["routine_style"] = style
        print(f"Тип выступления: {STYLE_RU[style]}")
    source = Path(args.video) if args.video else newest_inbox()
    if source is None or not source.exists():
        raise SystemExit(
            "Положите ролик выступления в папку inbox и снова запустите запуск.bat"
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_dir = WORK / f"{stamp}_{slug(source.stem)}"
    job_dir.mkdir(parents=True, exist_ok=True)
    source_copy = job_dir / f"source{source.suffix.lower()}"
    shutil.copy2(source, source_copy)
    original = source
    source = source_copy

    meta = {
        "hook": args.hook or "WOW",
        "athletes": args.athletes or "",
        "event": args.event or "",
        "city": getattr(args, "city", "") or "",
        "element": args.element or "",
        "source": str(original),
    }

    print(f"1/4 Анализ движения: {original.name}")
    if args.clips:
        ranges = parse_clip_ranges(args.clips)
        highlights = highlights_from_ranges(source, ranges, job_dir)
        print("   Режим: ручные таймкоды (не автопоиск)")
        if style:
            highlights["routine_style"] = style
            highlights["note"] = f"Ручные таймкоды, тип: {STYLE_RU[style]}."
    elif args.from_json:
        import json

        highlights = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    else:
        highlights = analyze_video(source, job_dir, cfg)
        print(f"   Режим: авто ({highlights.get('note', '')})")
    print(f"   Найдено кусков: {len(highlights['clips'])}, длина ~ {highlights['total_sec']} сек")

    music_path = Path(args.music) if args.music else None
    if args.skip_music:
        music_path = None
        print("2/4 Музыка: без звука")
    elif music_path:
        print(f"2/4 Музыка: {music_path.name}")
    elif not args.skip_kie:
        try:
            from pipeline.music_kie import generate_instrumental, load_api_key

            if load_api_key():
                print("2/4 Музыка Kie AI…")
                music_path = generate_instrumental(
                    job_dir / "kie.mp3", cfg, float(highlights["total_sec"])
                )
            else:
                music_path = find_local_music()
                print("2/4 Ключа Kie нет — " + (f"беру {music_path.name}" if music_path else "без музыки"))
        except Exception as exc:
            print(f"2/4 Музыка Kie не получилась ({exc}). Собираю без неё.")
            music_path = find_local_music()
    else:
        music_path = find_local_music()
        print(f"2/4 Музыка: {music_path.name if music_path else 'нет'}")

    subscribe_line = next_subscribe_line(cfg)
    meta["subscribe_line"] = subscribe_line

    print("3/4 Сборка вертикального шортса 9:16…")
    short = assemble(source, highlights, job_dir, music_path, meta, cfg)

    name = slug("_".join(x for x in [meta["hook"], meta["athletes"], meta["event"]] if x), source.stem)
    dest = OUTBOX / f"{name}_{stamp}.mp4"
    shutil.copy2(short, dest)
    write_json(job_dir / "highlights.json", highlights)
    shutil.copy2(job_dir / "highlights.json", dest.with_suffix(".json"))

    suggested = youtube_title(meta)
    write_json(
        dest.with_suffix(".meta.json"),
        {
            "youtube_title": suggested,
            "subscribe_line": subscribe_line,
            "description": youtube_description(suggested, cfg, subscribe_line),
            "output": str(dest),
            "job": str(job_dir),
            "music": str(music_path) if music_path else None,
        },
    )
    preview = write_preview(job_dir, highlights, meta, dest)
    shutil.copy2(preview, dest.with_suffix(".html"))
    print("4/4 Готово")
    print(f"Файл: {dest}")
    print(f"Название для YouTube: {suggested}")
    if subscribe_line:
        print(f"Зачем подписываться: {subscribe_line}")
    print(f"Просмотр таймкодов: {dest.with_suffix('.html')}")
    return dest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Конвейер шортсов: выступление → 30–50 сек вертикальный ролик"
    )
    p.add_argument("--video", help="Путь к ролику (иначе берётся самый новый из inbox)")
    p.add_argument("--hook", default="WOW", help="Текст-хук на первом кадре")
    p.add_argument("--athletes", default="", help="Имена спортсменов")
    p.add_argument("--event", default="", help="Турнир / город старта (в название YouTube)")
    p.add_argument("--city", default="", help="Город команды (крупно на плашке)")
    p.add_argument("--element", default="", help="Элемент (бросок, баланс…)")
    p.add_argument("--music", help="Свой mp3 вместо Kie AI")
    p.add_argument("--from-json", help="Пересобрать по готовому highlights.json")
    p.add_argument(
        "--clips",
        help="Ручные отрезки, первый = хук. Пример: 17-28,38-44,1:12-1:20,1:38-1:51,2:02-2:08",
    )
    p.add_argument(
        "--style",
        help="Тип упражнения: tempo / balance / combined (темповое, балансовое, комбинированное)",
    )
    p.add_argument("--skip-kie", action="store_true", help="Не вызывать Kie AI")
    p.add_argument("--skip-music", action="store_true", help="Собрать совсем без музыки")
    p.add_argument("--self-test", action="store_true", help="Прогон на тестовом ролике")
    return p


def main() -> None:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = build_parser().parse_args()
    if args.self_test:
        from pipeline.selftest import make_dummy_routine

        dummy = make_dummy_routine()
        args.video = str(dummy)
        args.hook = args.hook or "WOW"
        args.athletes = args.athletes or "Тест / Конвейер"
        args.event = args.event or "Проверка"
        args.skip_kie = True
        args.skip_music = True
    run_job(args)


if __name__ == "__main__":
    main()
