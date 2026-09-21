from __future__ import annotations

from pathlib import Path

from pipeline.ffmpeg_bin import ffmpeg_exe, run_cmd
from pipeline.media import crop_scale_filter
from pipeline.textutil import ff_font, ff_fontfile, ff_text, overlay_name_lines, split_cta_lines


def _cut_clip(
    source: Path,
    dest: Path,
    start: float,
    end: float,
    src_w: int,
    src_h: int,
    cx_ratio: float,
    out_w: int,
    out_h: int,
    fps: int,
) -> None:
    vf = crop_scale_filter(src_w, src_h, cx_ratio, out_w, out_h) + f",fps={fps},format=yuv420p"
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe(),
        "-y",
        "-i",
        str(source),
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-an",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]
    proc = run_cmd(cmd, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"Не удалось вырезать кусок {start:.1f}-{end:.1f} сек:\n{err[-1200:]}")


def _concat(clips: list[Path], dest: Path) -> None:
    listing = dest.parent / "concat.txt"
    lines = [f"file '{p.name}'" for p in clips]
    listing.write_text("\n".join(lines), encoding="utf-8")
    cmd = [
        ffmpeg_exe(),
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(listing),
        "-c",
        "copy",
        str(dest),
    ]
    proc = run_cmd(cmd, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"Не удалось склеить куски:\n{err[-1200:]}")


def _drawtext_filters(meta: dict, cfg: dict, duration: float = 0.0) -> str:
    overlay = cfg.get("overlay") or {}
    hook = ff_text(meta.get("hook") or "WOW")
    if overlay.get("names_uppercase", True):
        hook = hook.upper()
    name_lines = overlay_name_lines(meta.get("athletes") or "")
    if overlay.get("names_uppercase", True):
        name_lines = [line.upper() for line in name_lines]
    event = ff_text(meta.get("event") or "")
    city = ff_text(meta.get("city") or "")
    place = city or event
    if overlay.get("names_uppercase", True):
        event = event.upper()
        city = city.upper()
        place = place.upper()
    channel = ff_text(cfg.get("channel_label") or "")
    hook_t = float(cfg.get("hook_seconds", 2.6))
    names_t = float(cfg.get("names_seconds", 6.0))
    yellow = overlay.get("hook_color", "0xFFD60A")
    font_hook = ff_fontfile(
        overlay.get("font_hook"),
        [Path(r"C:\Windows\Fonts\impact.ttf"), Path(r"C:\Windows\Fonts\seguibl.ttf"), Path(r"C:\Windows\Fonts\arialbd.ttf")],
    )
    font_names = ff_fontfile(
        overlay.get("font_names"),
        [
            Path(r"C:\Windows\Fonts\NotoSans-CondensedBold.ttf"),
            Path(r"C:\Windows\Fonts\seguibl.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ],
    )
    font_event = ff_fontfile(
        overlay.get("font_event"),
        [
            Path(r"C:\Windows\Fonts\NotoSans-CondensedBold.ttf"),
            Path(r"C:\Windows\Fonts\NotoSans-Condensed.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ],
    )
    hook_size = int(overlay.get("hook_size", 118))
    names_size = int(overlay.get("names_size", 52))
    event_size = int(overlay.get("event_size", 52))
    bar_h = int(overlay.get("bar_height", 10))
    plate_y = int(overlay.get("plate_y", 236))
    plate_margin = int(overlay.get("plate_margin", 40))
    plate_opacity = float(overlay.get("plate_opacity", 0.72))
    hook_y = int(overlay.get("hook_y", 108))
    names_y = int(overlay.get("names_y", 250))
    event_gap = int(overlay.get("event_gap", 18))
    event_y = names_y + max(1, len(name_lines)) * (names_size + 6) + event_gap
    plate_bottom = event_y + event_size + 16 if place else names_y + names_size + 16
    plate_h = max(int(overlay.get("plate_h", 118)), plate_bottom - plate_y)

    parts = [
        f"drawbox=x=0:y=0:w=iw:h={bar_h}:color={yellow}:t=fill",
    ]
    if name_lines or place:
        parts.append(
            f"drawbox=x={plate_margin}:y={plate_y}:w=iw-{plate_margin * 2}:h={plate_h}:"
            f"color=black@{plate_opacity}:t=fill:enable='lt(t,{names_t})'"
        )
    parts.append(
        f"drawtext=fontfile='{font_hook}':text='{hook}':fontsize={hook_size}:"
        f"fontcolor={yellow}:x=(w-text_w)/2:y={hook_y}:enable='lt(t,{hook_t})'"
    )
    for i, line in enumerate(name_lines):
        y = names_y + i * (names_size + 6)
        parts.append(
            f"drawtext=fontfile='{font_names}':text='{line}':fontsize={names_size}:"
            f"fontcolor=white:borderw=2:bordercolor=black:"
            f"x=(w-text_w)/2:y={y}:enable='lt(t,{names_t})'"
        )
    if place:
        parts.append(
            f"drawtext=fontfile='{font_event}':text='{place}':fontsize={event_size}:"
            f"fontcolor={yellow}:borderw=2:bordercolor=black:"
            f"x=(w-text_w)/2:y={event_y}:enable='lt(t,{names_t})'"
        )
    cta_lines = split_cta_lines(meta.get("subscribe_line") or "")
    cta_sec = float(overlay.get("cta_seconds", 3.4))
    if cta_lines and duration > 0:
        cta_start = max(0.0, duration - cta_sec)
        cta_size = int(overlay.get("cta_size", 46))
        cta_pad = 22
        cta_h = cta_pad * 2 + len(cta_lines) * (cta_size + 10) - 10
        cta_y = plate_y + cta_pad
        parts.append(
            f"drawbox=x={plate_margin}:y={plate_y}:w=iw-{plate_margin * 2}:h={cta_h}:"
            f"color=black@{plate_opacity}:t=fill:enable='gte(t,{cta_start:.2f})'"
        )
        for i, line in enumerate(cta_lines):
            y = cta_y + i * (cta_size + 10)
            parts.append(
                f"drawtext=fontfile='{font_names}':text='{line}':fontsize={cta_size}:"
                f"fontcolor={yellow}:borderw=3:bordercolor=black:"
                f"x=(w-text_w)/2:y={y}:enable='gte(t,{cta_start:.2f})'"
            )
    if channel and overlay.get("show_channel", False):
        font = ff_font()
        parts.append(
            f"drawtext=fontfile='{font}':text='{channel}':fontsize={overlay.get('channel_size', 28)}:"
            f"fontcolor=white@0.85:borderw=2:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-360"
        )
    return ",".join(parts)


def pack_short(
    silent: Path,
    dest: Path,
    music: Path | None,
    meta: dict,
    cfg: dict,
    duration: float,
) -> None:
    freeze = 0.45
    vf = _drawtext_filters(meta, cfg, duration) + f",tpad=stop_mode=clone:stop_duration={freeze}"
    out_dur = duration + freeze
    cmd = [
        ffmpeg_exe(),
        "-y",
        "-i",
        str(silent),
    ]
    if music and music.exists():
        cmd += [
            "-i",
            str(music),
            "-filter_complex",
            (
                f"[0:v]{vf}[v];"
                f"[1:a]afade=t=in:st=0:d=0.4,afade=t=out:st={max(0.5, out_dur - 0.7):.2f}:d=0.65,volume=0.9[a]"
            ),
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-t",
            f"{out_dur:.3f}",
            "-shortest",
        ]
    else:
        cmd += ["-vf", vf, "-an"]

    cmd += [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
    ]
    if music and music.exists():
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-movflags",
        "+faststart",
        str(dest),
    ]
    proc = run_cmd(cmd, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"Не удалось собрать финальный ролик:\n{err[-1500:]}")


def assemble(source: Path, highlights: dict, job_dir: Path, music: Path | None, meta: dict, cfg: dict) -> Path:
    out_w = int(cfg.get("output_width", 1080))
    out_h = int(cfg.get("output_height", 1920))
    fps = int(cfg.get("output_fps", 30))
    src_w = int(highlights["width"])
    src_h = int(highlights["height"])
    clip_paths: list[Path] = []
    clips = [c for c in highlights["clips"] if c.get("keep", True)]
    if not clips:
        raise RuntimeError("В highlights.json нет кусков с keep: true")

    for i, clip in enumerate(clips):
        dest = job_dir / f"clip_{i:02d}.mp4"
        _cut_clip(
            source,
            dest,
            float(clip["start"]),
            float(clip["end"]),
            src_w,
            src_h,
            float(clip.get("cx_ratio", 0.5)),
            out_w,
            out_h,
            fps,
        )
        clip_paths.append(dest)

    silent = job_dir / "silent_concat.mp4"
    _concat(clip_paths, silent)
    duration = sum(float(c["end"]) - float(c["start"]) for c in clips)
    final = job_dir / "short.mp4"
    pack_short(silent, final, music, meta, cfg, duration)
    return final
