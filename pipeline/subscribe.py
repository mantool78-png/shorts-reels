from __future__ import annotations

import json
import random
from pathlib import Path

from pipeline.paths import WORK

STATE_FILE = WORK / "subscribe-cta-state.json"

DEFAULT_PHRASES = [
    "Новые ролики каждую неделю на этом канале.",
    "Новые программы постоянно на нашем канале.",
    "Каждую неделю новые моменты акро WOW!",
    "Регулярно новые пары, турниры и элементы только на нашем канале!",
    "Только здесь новые ролики выходят постоянно.",
    "Следующие выступления — каждую неделю на нашем канале.",
    "Новые шортсы каждую неделю, без пауз.",
    "Не пропусти",
]


def phrases_from_cfg(cfg: dict) -> list[str]:
    raw = cfg.get("subscribe_why") or DEFAULT_PHRASES
    return [str(item).strip() for item in raw if str(item).strip()]


def next_subscribe_line(cfg: dict) -> str:
    """Берёт следующую фразу из перемешанной колоды, без повтора подряд."""
    phrases = phrases_from_cfg(cfg)
    if not phrases:
        return ""

    WORK.mkdir(parents=True, exist_ok=True)
    state: dict = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    last = state.get("last")
    valid = set(phrases)
    deck = [item for item in (state.get("deck") or []) if item in valid]
    if not deck:
        pool = [item for item in phrases if item != last] or list(phrases)
        random.shuffle(pool)
        deck = pool

    line = deck.pop(0)
    STATE_FILE.write_text(
        json.dumps({"deck": deck, "last": line}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return line


def youtube_description(title: str, cfg: dict, subscribe_line: str) -> str:
    channel = (cfg.get("channel_label") or "").strip()
    handle = (cfg.get("channel_handle") or "").strip()
    brand = " ".join(part for part in (channel, handle) if part)
    blocks = [title]
    if subscribe_line:
        blocks.append(subscribe_line)
    if brand:
        blocks.append(brand)
    blocks.append("t.me/ACROTIM")
    blocks.append("#акробатика #спортивнаяакробатика #shorts")
    return "\n\n".join(blocks)
