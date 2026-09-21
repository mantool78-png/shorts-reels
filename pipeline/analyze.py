from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from pipeline.ffmpeg_bin import ffmpeg_exe
from pipeline.media import probe_video
from pipeline.textutil import write_json


@dataclass
class Clip:
    start: float
    end: float
    score: float
    role: str = "peak"
    keep: bool = True
    cx_ratio: float = 0.5
    kind: str = "tempo"

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def _rolling_median(values: np.ndarray, window: int) -> np.ndarray:
    if len(values) < window or window < 3:
        return values
    half = window // 2
    out = np.empty_like(values)
    for i in range(len(values)):
        a = max(0, i - half)
        b = min(len(values), i + half + 1)
        out[i] = float(np.median(values[a:b]))
    return out


def _clip_around(
    t: float,
    duration: float,
    centroids: np.ndarray,
    times: np.ndarray,
    i: int,
    pre: float,
    post: float,
    min_len: float,
    max_len: float,
    score: float,
    kind: str,
) -> Clip:
    start = max(0.0, t - pre)
    end = min(duration, t + post)
    if end - start < min_len:
        end = min(duration, start + min_len)
    if end - start > max_len:
        end = start + max_len
    cx = float(np.median(centroids[max(0, i - 4) : i + 8])) if len(centroids) else 0.5
    return Clip(start, end, score, "peak", True, cx, kind)


def _spawn_gray_frames(video: Path, fps: int, width: int, height: int) -> subprocess.Popen:
    vf = f"fps={fps},scale={width}:{height},format=gray"
    cmd = [
        ffmpeg_exe(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-vf",
        vf,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def _smooth(values: np.ndarray, window: int = 5) -> np.ndarray:
    if len(values) < window:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")


def read_motion(video: Path, fps: int, width: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    info = probe_video(video)
    src_w, src_h = info["width"], info["height"]
    height = int(round(src_h * width / src_w))
    height -= height % 2
    height = max(2, height)
    frame_bytes = width * height
    proc = _spawn_gray_frames(video, fps, width, height)
    assert proc.stdout is not None

    energies = []
    centroids = []
    prev = None
    try:
        while True:
            buf = proc.stdout.read(frame_bytes)
            if len(buf) < frame_bytes:
                break
            frame = np.frombuffer(buf, dtype=np.uint8).reshape((height, width))
            if prev is None:
                energies.append(0.0)
                centroids.append(0.5)
            else:
                diff = np.abs(frame.astype(np.int16) - prev.astype(np.int16))
                energies.append(float(diff.mean()))
                mask = diff > 18
                if mask.any():
                    ys, xs = np.nonzero(mask)
                    centroids.append(float(xs.mean()) / width)
                else:
                    centroids.append(centroids[-1] if centroids else 0.5)
            prev = frame
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

    return np.array(energies), np.array(centroids), np.arange(len(energies)) / fps, info


def _windows_from_peaks(
    energy: np.ndarray,
    centroids: np.ndarray,
    times: np.ndarray,
    duration: float,
    cfg: dict,
) -> list[Clip]:
    if len(energy) < 8:
        return [Clip(0.0, min(duration, cfg["target_max_sec"]), 1.0, "full", True, 0.5, "tempo")]

    smooth = _smooth(energy, 5)
    fps = 8 if len(times) < 2 else max(1.0, 1.0 / float(times[1] - times[0]))
    baseline = _rolling_median(smooth, max(5, int(fps * 2.4)))
    residual = np.clip(smooth - baseline, 0, None)
    mx = float(np.max(residual)) if len(residual) else 0.0
    if mx < 0.25:
        return [Clip(0.0, min(duration, cfg["target_max_sec"]), 1.0, "full", True, 0.5, "tempo")]

    thr = max(float(np.percentile(residual, 90)), mx * 0.42)
    peak_idx = []
    for i in range(2, len(residual) - 2):
        if residual[i] >= thr and residual[i] >= residual[i - 1] and residual[i] >= residual[i + 1]:
            if not peak_idx or i - peak_idx[-1] >= int(fps * 1.6):
                peak_idx.append(i)
    if not peak_idx:
        peak_idx = [int(np.argmax(residual))]

    clips: list[Clip] = []
    pre = float(cfg.get("clip_pre_sec", 1.2))
    post = float(cfg.get("clip_post_sec", 5.5))
    min_len = float(cfg.get("clip_min_sec", 3.5))
    max_len = float(cfg.get("clip_max_sec", 8.0))
    for i in peak_idx:
        score = float(residual[i])
        after = residual[i : min(len(residual), i + int(fps * 1.2))]
        if len(after) > 3 and after[-1] < residual[i] * 0.45:
            score *= 1.3
        clips.append(
            _clip_around(
                float(times[i]), duration, centroids, times, i, pre, post, min_len, max_len, score, "tempo"
            )
        )
    return _merge_clips(clips, float(cfg.get("merge_gap_sec", 0.7)), max_len)


def _windows_from_holds(
    energy: np.ndarray,
    centroids: np.ndarray,
    times: np.ndarray,
    duration: float,
    cfg: dict,
) -> list[Clip]:
    smooth = _smooth(energy, 5)
    fps = 8 if len(times) < 2 else max(1.0, 1.0 / float(times[1] - times[0]))
    low_thr = float(np.percentile(smooth, 38))
    min_hold = int(fps * 1.8)
    clips: list[Clip] = []
    i = int(fps * 6)
    end_limit = len(smooth) - int(fps * 3)
    while i < end_limit:
        if smooth[i] > low_thr:
            i += 1
            continue
        j = i
        while j < end_limit and smooth[j] <= low_thr:
            j += 1
        if j - i >= min_hold:
            before = smooth[max(0, i - int(fps * 2)) : i]
            if len(before) and float(np.max(before)) > low_thr * 1.8:
                hold_t = float(times[(i + j) // 2])
                start = max(0.0, float(times[i]) - 1.0)
                end = min(duration, start + 7.0, float(times[min(j, len(times) - 1)]))
                if end - start >= 3.2:
                    score = (end - start) * (1.0 / (float(np.mean(smooth[i:j])) + 0.15))
                    cx = float(np.median(centroids[i:j])) if j > i else 0.5
                    clips.append(Clip(start, end, score, "peak", True, cx, "hold"))
            i = j + int(fps)
        else:
            i = j + 1
    return clips


def _merge_clips(clips: list[Clip], gap: float, max_len: float) -> list[Clip]:
    clips.sort(key=lambda c: c.start)
    merged: list[Clip] = []
    for clip in clips:
        if merged and clip.kind == merged[-1].kind and clip.start <= merged[-1].end + gap:
            prev = merged[-1]
            prev.end = max(prev.end, clip.end)
            if prev.end - prev.start > max_len:
                prev.end = prev.start + max_len
            if clip.score > prev.score:
                prev.score = clip.score
                prev.cx_ratio = clip.cx_ratio
        else:
            merged.append(clip)
    return merged


def pick_combined(
    throws: list[Clip],
    holds: list[Clip],
    duration: float,
    cfg: dict,
) -> list[Clip]:
    """Комби = баланс (первая часть) + темп (вторая). Оба обязательны."""
    target_min = float(cfg.get("target_min_sec", 30))
    target_max = float(cfg.get("target_max_sec", 50))
    intro = 14.0
    balance_until = duration * 0.58
    bow = 8.0

    def overlaps(a: Clip, b: Clip) -> bool:
        return not (a.end <= b.start + 0.2 or b.end <= a.start + 0.2)

    def skip_intro(clip: Clip) -> bool:
        return clip.end <= intro or clip.start < 8.0

    balance_pool: list[Clip] = []
    for clip in list(holds) + list(throws):
        if skip_intro(clip):
            continue
        if clip.start < balance_until:
            balance_pool.append(
                Clip(clip.start, clip.end, clip.score, "peak", True, clip.cx_ratio, "hold")
            )
    tempo_pool = [
        clip
        for clip in throws
        if not skip_intro(clip)
        and clip.start >= balance_until - 12
        and clip.end < duration - bow
    ]
    if not tempo_pool:
        tempo_pool = [clip for clip in throws if not skip_intro(clip) and clip.start >= duration * 0.42]

    if not tempo_pool and not balance_pool:
        return pick_highlights(throws or holds, duration, cfg)

    hook_pool = tempo_pool or balance_pool
    hook = max(hook_pool, key=lambda c: c.score)
    hook = Clip(hook.start, hook.end, hook.score, "hook", True, hook.cx_ratio, "tempo")
    chosen = [hook]
    total = hook.duration
    balance_sec = 0.0
    tempo_sec = hook.duration

    for hold in sorted(balance_pool, key=lambda c: c.score, reverse=True):
        if any(overlaps(hold, x) for x in chosen):
            continue
        leftover = target_max - total
        if leftover < 3.2:
            break
        piece = Clip(hold.start, hold.end, hold.score, "peak", True, hold.cx_ratio, "hold")
        if piece.duration > leftover:
            piece.end = piece.start + leftover
        chosen.append(piece)
        total += piece.duration
        balance_sec += piece.duration
        if balance_sec >= 12 and total >= target_min - 8:
            break

    for throw in sorted(tempo_pool, key=lambda c: c.score, reverse=True):
        if any(overlaps(throw, x) for x in chosen):
            continue
        leftover = target_max - total
        if leftover < 3.2:
            break
        piece = Clip(throw.start, throw.end, throw.score, "peak", True, throw.cx_ratio, "tempo")
        if piece.duration > leftover:
            piece.end = piece.start + leftover
        chosen.append(piece)
        total += piece.duration
        tempo_sec += piece.duration
        if total >= target_min and tempo_sec >= 10 and balance_sec >= 10:
            break

    if total < target_min:
        need = target_min - total
        stretch = need / max(1, len(chosen))
        cap = float(cfg.get("clip_max_sec", 8.0)) + 4
        for clip in chosen:
            clip.end = min(duration, clip.end + stretch)
            if clip.end - clip.start > cap:
                clip.end = clip.start + cap

    hook_clip = next(c for c in chosen if c.role == "hook")
    others = sorted([c for c in chosen if c is not hook_clip], key=lambda c: c.start)
    return [hook_clip, *others]


def pick_highlights(clips: list[Clip], duration: float, cfg: dict) -> list[Clip]:
    target_min = float(cfg.get("target_min_sec", 30))
    target_max = float(cfg.get("target_max_sec", 50))
    if duration <= target_max + 4:
        cx = clips[0].cx_ratio if clips else 0.5
        return [Clip(0.0, duration, 1.0, "full", True, cx, "tempo")]

    ranked = sorted(clips, key=lambda c: c.score, reverse=True)
    if not ranked:
        return [Clip(0.0, min(duration, target_max), 1.0, "full", True, 0.5, "tempo")]
    floor = max(ranked[0].score * 0.25, 0.5)
    ranked = [c for c in ranked if c.score >= floor] or ranked[:1]
    hook = ranked[0]
    hook.role = "hook"
    chosen = [hook]
    total = hook.duration
    rest = sorted(ranked[1:], key=lambda c: c.score, reverse=True)

    def overlaps(a: Clip, b: Clip) -> bool:
        return not (a.end <= b.start + 0.15 or b.end <= a.start + 0.15)

    for clip in rest:
        if total >= target_min:
            break
        if any(overlaps(clip, x) for x in chosen):
            continue
        piece = Clip(clip.start, clip.end, clip.score, "peak", True, clip.cx_ratio)
        leftover = target_max - total
        if leftover < 2.5:
            break
        if piece.duration > leftover:
            piece.end = piece.start + leftover
        chosen.append(piece)
        total += piece.duration

    if total < target_min:
        need = target_min - total
        stretch = need / max(1, len(chosen))
        for clip in chosen:
            clip.end = min(duration, clip.end + stretch)
            if clip.end - clip.start > float(cfg.get("clip_max_sec", 8.0)) + 3:
                clip.end = clip.start + float(cfg.get("clip_max_sec", 8.0)) + 3

    hook_clip = [c for c in chosen if c.role == "hook"][0]
    others = sorted([c for c in chosen if c is not hook_clip], key=lambda c: c.start)
    return [hook_clip, *others]


def analyze_video(video: Path, job_dir: Path, cfg: dict) -> dict:
    fps = int(cfg.get("analyze_fps", 8))
    width = int(cfg.get("analyze_width", 320))
    energy, centroids, times, info = read_motion(video, fps, width)
    duration = float(info["duration"])
    style = cfg.get("routine_style") or "tempo"
    throws = _windows_from_peaks(energy, centroids, times, duration, cfg)
    holds = _windows_from_holds(energy, centroids, times, duration, cfg)
    if style == "balance":
        picked = pick_highlights(holds or throws, duration, cfg)
        note = "Авто: балансовое (ищем стойки/пирамиды, не дорожку)."
    elif style == "combined":
        picked = pick_combined(throws, holds, duration, cfg)
        note = "Авто: комбинированное. В нарезке и пирамиды/стойки, и полёты/выбросы."
    else:
        picked = pick_highlights(throws, duration, cfg)
        note = "Авто: темповое (броски/винты по всплеску, танец отфильтрован)."
    payload = {
        "source": str(video),
        "duration_source": round(duration, 3),
        "width": info["width"],
        "height": info["height"],
        "routine_style": style,
        "clips": [asdict(c) | {"duration": round(c.duration, 3)} for c in picked],
        "total_sec": round(sum(c.duration for c in picked), 3),
        "note": note,
    }
    write_json(job_dir / "highlights.json", payload)
    return payload


def _cx_in_window(times: np.ndarray, centroids: np.ndarray, start: float, end: float) -> float:
    if len(times) == 0:
        return 0.5
    mask = (times >= start) & (times <= end)
    if not np.any(mask):
        idx = int(np.argmin(np.abs(times - (start + end) / 2)))
        return float(np.clip(centroids[idx], 0.15, 0.85))
    return float(np.clip(np.median(centroids[mask]), 0.15, 0.85))


def highlights_from_ranges(video: Path, ranges: list[tuple[float, float]], job_dir: Path) -> dict:
    info = probe_video(video)
    duration = float(info["duration"])
    try:
        _, centroids, times, _ = read_motion(video, 8, 320)
    except Exception:
        centroids = times = None
    clips = []
    for i, (start, end) in enumerate(ranges):
        start = max(0.0, min(start, duration - 0.2))
        end = max(start + 0.2, min(end, duration))
        cx = 0.5
        if centroids is not None and times is not None:
            cx = round(_cx_in_window(times, centroids, start, end), 3)
        clips.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "score": 1.0,
                "role": "hook" if i == 0 else "peak",
                "keep": True,
                "cx_ratio": cx,
                "duration": round(end - start, 3),
            }
        )
    payload = {
        "source": str(video),
        "duration_source": round(duration, 3),
        "width": info["width"],
        "height": info["height"],
        "clips": clips,
        "total_sec": round(sum(c["duration"] for c in clips), 3),
        "note": "Нарезка по ручным таймкодам. Первый кусок — хук.",
    }
    write_json(job_dir / "highlights.json", payload)
    return payload
