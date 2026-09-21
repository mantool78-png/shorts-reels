from __future__ import annotations

import os
import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def ffmpeg_exe() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def ffprobe_exe() -> str:
    """imageio-ffmpeg ships ffmpeg; probe via ffmpeg -hide_banner."""
    return ffmpeg_exe()


def run_cmd(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    flags = 0
    if os.name == "nt":
        flags = subprocess.CREATE_NO_WINDOW
    return subprocess.run(
        args,
        check=kwargs.pop("check", True),
        capture_output=kwargs.pop("capture_output", True),
        **kwargs,
        creationflags=flags if os.name == "nt" else 0,
    )
