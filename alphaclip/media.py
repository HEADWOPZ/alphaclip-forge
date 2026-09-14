from __future__ import annotations

import json
import subprocess
from pathlib import Path

from alphaclip.config import ffmpeg_bin, ffprobe_bin


class MediaError(RuntimeError):
    pass


def probe_media(path: Path) -> dict:
    cmd = [
        ffprobe_bin(),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise MediaError(f"ffprobe failed on {path}: {exc.stderr[-400:]}") from exc
    return json.loads(completed.stdout or "{}")


def media_duration(path: Path) -> float:
    info = probe_media(path)
    fmt = info.get("format") or {}
    if fmt.get("duration"):
        return float(fmt["duration"])
    for stream in info.get("streams") or []:
        if stream.get("duration"):
            return float(stream["duration"])
    raise MediaError(f"Could not determine duration for {path}")


def video_size(path: Path) -> tuple[int, int]:
    info = probe_media(path)
    for stream in info.get("streams") or []:
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise MediaError(f"No video stream in {path}")


def run_ffmpeg(args: list[str]) -> None:
    cmd = [ffmpeg_bin(), "-y", *args]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise MediaError(f"ffmpeg failed:\n{detail[-1200:]}") from exc
