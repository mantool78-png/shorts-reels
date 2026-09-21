from __future__ import annotations

import json
import re
from pathlib import Path


def slug(text: str, fallback: str = "short") -> str:
    text = (text or "").strip()
    text = re.sub(r"[^\w\s\-а-яА-ЯёЁ]+", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text).strip("_")
    return text[:60] or fallback


def ff_text(text: str) -> str:
    """Экранирование текста для ffmpeg drawtext."""
    cleaned = (
        (text or "")
        .replace("\\", " ")
        .replace(":", " ")
        .replace("'", " ")
        .replace('"', " ")
        .replace("%", " ")
        .replace("\n", " ")
    )
    return cleaned.strip()


def ff_font() -> str:
    return ff_fontfile(None, [
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
    ])


def ff_fontfile(preferred: str | Path | None, fallbacks: list[Path] | None = None) -> str:
    candidates: list[Path] = []
    if preferred:
        candidates.append(Path(preferred))
    candidates.extend(fallbacks or [])
    for path in candidates:
        if path.exists():
            return str(path).replace("\\", "/").replace(":", "\\:")
    return "Arial"


def overlay_name_lines(names: str) -> list[str]:
    """Четвёрка — две строки, тот же кегль что город, без «&»."""
    text = (names or "").strip()
    if not text:
        return []
    if " / " in text:
        return [ff_text(part) for part in text.split(" / ") if part.strip()]
    parts = [p.strip() for p in text.replace(" & ", ", ").split(",") if p.strip()]
    if len(parts) >= 4:
        return [
            ff_text(f"{parts[0]} · {parts[1]}"),
            ff_text(f"{parts[2]} · {parts[3]}"),
        ]
    return [ff_text(text)]


def split_cta_lines(text: str, max_len: int = 32) -> list[str]:
    raw = ff_text(text)
    if not raw:
        return []
    if len(raw) <= max_len:
        return [raw]
    for sep in (" — ", ". ", ", "):
        idx = raw.find(sep)
        if 8 <= idx <= max_len + 6:
            left = raw[:idx].strip(" .,—")
            right = raw[idx + len(sep) :].strip()
            if left and right:
                return [ff_text(left), ff_text(right)]
    space = raw.rfind(" ", 0, max_len)
    if space > 10:
        return [ff_text(raw[:space]), ff_text(raw[space + 1 :])]
    return [raw]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_timestamp(text: str) -> float:
    """'17', '17.5', '1:38', '1:38.0' → секунды."""
    text = (text or "").strip().replace(",", ".")
    if not text:
        raise ValueError("пустой таймкод")
    if ":" in text:
        parts = [float(p) for p in text.split(":")]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        raise ValueError(f"непонятный таймкод: {text}")
    return float(text)


def parse_clip_ranges(text: str) -> list[tuple[float, float]]:
    """'17-28,38-44,1:12-1:20' → список (start, end). Первый кусок — хук."""
    ranges: list[tuple[float, float]] = []
    for chunk in (text or "").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" not in chunk:
            raise ValueError(f"нужен диапазон вида 17-28, получено: {chunk}")
        left, right = chunk.rsplit("-", 1)
        start, end = parse_timestamp(left), parse_timestamp(right)
        if end <= start:
            raise ValueError(f"конец раньше начала: {chunk}")
        ranges.append((start, end))
    if not ranges:
        raise ValueError("нет ни одного отрезка")
    return ranges
