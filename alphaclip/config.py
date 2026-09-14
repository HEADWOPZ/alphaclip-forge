from __future__ import annotations

import os
import shutil
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"
DEFAULT_WORK_ROOT = Path(os.environ.get("ALPHACLIP_WORK", REPO_ROOT / "var"))

VERTICAL_WIDTH = 1080
VERTICAL_HEIGHT = 1920

# Caption burn prefers Inter (present on this image) then Liberation Sans.
FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def work_root() -> Path:
    root = Path(os.environ.get("ALPHACLIP_WORK", DEFAULT_WORK_ROOT))
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_font() -> Path:
    override = os.environ.get("ALPHACLIP_FONT")
    if override:
        path = Path(override)
        if path.is_file():
            return path
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "No caption font found. Set ALPHACLIP_FONT to a .ttf/.otf path."
    )


def which_or_none(name: str) -> str | None:
    return shutil.which(name)


def ffmpeg_bin() -> str:
    path = os.environ.get("FFMPEG_BIN") or which_or_none("ffmpeg")
    if not path:
        raise RuntimeError("ffmpeg is required. Install ffmpeg and ensure it is on PATH.")
    return path


def ffprobe_bin() -> str:
    path = os.environ.get("FFPROBE_BIN") or which_or_none("ffprobe")
    if not path:
        raise RuntimeError("ffprobe is required. Install ffmpeg (includes ffprobe).")
    return path


def ytdlp_bin() -> str | None:
    return os.environ.get("YTDLP_BIN") or which_or_none("yt-dlp")


def whisper_cli() -> str | None:
    return os.environ.get("WHISPER_BIN") or which_or_none("whisper")


def default_whisper_model() -> str:
    """CPU-friendly default. Override with ALPHACLIP_WHISPER_MODEL."""
    return os.environ.get("ALPHACLIP_WHISPER_MODEL", "tiny")


WHISPER_MODELS = {
    "tiny": "Fastest CPU option. Good enough for mock-adjacent testing and rough hooks.",
    "base": "Better accuracy, still OK on CPU for short sources.",
    "small": "Recommended CPU quality if you can wait a few minutes.",
    "medium": "Heavy on CPU. Prefer a GPU.",
    "large-v3": "Best quality. GPU strongly recommended.",
}
