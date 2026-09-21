from __future__ import annotations

import re
from pathlib import Path

from pipeline.ffmpeg_bin import ffmpeg_exe, run_cmd


def probe_video(path: Path) -> dict:
    cmd = [
        ffmpeg_exe(),
        "-hide_banner",
        "-i",
        str(path),
    ]
    proc = run_cmd(cmd, check=False)
    err = (proc.stderr or b"").decode("utf-8", errors="replace")
    width = height = None
    duration = None
    fps = 30.0

    for line in err.splitlines():
        if "Video:" in line:
            size = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if size:
                width, height = int(size.group(1)), int(size.group(2))
            fps_m = re.search(r"(\d+(?:\.\d+)?)\s*fps", line)
            if fps_m:
                fps = float(fps_m.group(1))
        if "Duration:" in line:
            dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", line)
            if dur:
                duration = (
                    int(dur.group(1)) * 3600
                    + int(dur.group(2)) * 60
                    + float(dur.group(3))
                )

    if not width or not height or not duration:
        raise RuntimeError(
            f"Не удалось прочитать видео. FFmpeg ответил:\n{err[-1500:]}"
        )
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "duration": duration,
        "fps": fps,
    }


def crop_scale_filter(src_w: int, src_h: int, cx_ratio: float, out_w: int, out_h: int) -> str:
    """Вертикальное окно 9:16, сдвинутое к центру движения."""
    target_ratio = out_w / out_h
    src_ratio = src_w / src_h
    if src_ratio <= target_ratio + 0.02:
        # Уже вертикальный или почти: заполняем кадр
        return (
            f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
            f"crop={out_w}:{out_h},setsar=1"
        )

    crop_h = src_h
    crop_w = int(round(src_h * target_ratio))
    if crop_w % 2:
        crop_w -= 1
    crop_w = max(2, min(crop_w, src_w))
    cx = cx_ratio * src_w
    x = int(round(cx - crop_w / 2))
    x = max(0, min(x, src_w - crop_w))
    if x % 2:
        x -= 1
        x = max(0, x)
    return f"crop={crop_w}:{crop_h}:{x}:0,scale={out_w}:{out_h}:flags=lanczos,setsar=1"
