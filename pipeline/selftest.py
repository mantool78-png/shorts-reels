from __future__ import annotations

from pathlib import Path

from pipeline.ffmpeg_bin import ffmpeg_exe, run_cmd
from pipeline.paths import INBOX


def make_dummy_routine(dest: Path | None = None) -> Path:
    """Тестовое «выступление» ~70 сек: спокойно / вспышка / спокойно / вспышка."""
    dest = dest or (INBOX / "тест_выступление.mp4")
    dest.parent.mkdir(parents=True, exist_ok=True)
    quiet1 = dest.parent / "_t1.mp4"
    action = dest.parent / "_t2.mp4"
    quiet2 = dest.parent / "_t3.mp4"
    listing = dest.parent / "_t.txt"
    ff = ffmpeg_exe()

    def clip(out: Path, src: str, seconds: int) -> None:
        proc = run_cmd(
            [
                ff,
                "-y",
                "-f",
                "lavfi",
                "-i",
                src,
                "-t",
                str(seconds),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(out),
            ],
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or b"").decode("utf-8", errors="replace")
            raise RuntimeError(err[-1000:])

    clip(quiet1, "color=c=0x1a1a1a:s=1920x1080:r=30", 20)
    clip(action, "testsrc2=s=1920x1080:r=30", 6)
    clip(quiet2, "color=c=0x1a1a1a:s=1920x1080:r=30", 18)
    action2 = dest.parent / "_t4.mp4"
    quiet3 = dest.parent / "_t5.mp4"
    clip(action2, "testsrc2=s=1920x1080:r=30", 6)
    clip(quiet3, "color=c=0x1a1a1a:s=1920x1080:r=30", 20)
    listing.write_text(
        "file '_t1.mp4'\nfile '_t2.mp4'\nfile '_t3.mp4'\nfile '_t4.mp4'\nfile '_t5.mp4'\n",
        encoding="utf-8",
    )
    proc = run_cmd(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(dest)],
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")
        raise RuntimeError(err[-1000:])
    for extra in (quiet1, action, quiet2, action2, quiet3, listing):
        extra.unlink(missing_ok=True)
    return dest
