from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from alphaclip.config import ytdlp_bin

YOUTUBE_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/",
    re.I,
)
X_RE = re.compile(r"(https?://)?(www\.)?(x\.com|twitter\.com)/", re.I)
LOOM_RE = re.compile(r"(https?://)?(www\.)?loom\.com/", re.I)


class IngestError(RuntimeError):
    pass


def classify_source(source: str) -> str:
    raw = (source or "").strip()
    if not raw:
        raise IngestError("No source provided.")
    path = Path(raw).expanduser()
    if path.exists() and path.is_file():
        return "local"
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"}:
        if YOUTUBE_RE.search(raw):
            return "youtube"
        if X_RE.search(raw):
            return "x"
        if LOOM_RE.search(raw):
            return "loom"
        return "url"
    if path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".m4v"}:
        raise IngestError(f"Local video not found: {path}")
    raise IngestError(
        f"Unrecognized source '{source}'. Pass a local video path or a YouTube / X / Loom URL."
    )


def probe_kind(source: str) -> str:
    return classify_source(source)


def ingest_source(source: str, dest_dir: Path) -> Path:
    """Copy a local file or download a remote URL into dest_dir. Returns the media path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    kind = classify_source(source)
    if kind == "local":
        src = Path(source).expanduser().resolve()
        dest = dest_dir / src.name
        if src != dest:
            shutil.copy2(src, dest)
        return dest
    return _download(source, dest_dir)


def _download(url: str, dest_dir: Path) -> Path:
    ytdlp = ytdlp_bin()
    if not ytdlp:
        raise IngestError(
            "yt-dlp is required to ingest remote URLs. Install it (`pip install yt-dlp`) "
            "or pass a local video file / --mock-transcript demo run."
        )
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Keep filenames boring so ffmpeg filter paths stay easy to escape.
    outtmpl = str(dest_dir / "source.%(ext)s")
    cmd = [
        ytdlp,
        "--no-playlist",
        "--no-warnings",
        "-f",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format",
        "mp4",
        "-o",
        outtmpl,
        url,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise IngestError(
            "yt-dlp failed to download the source. "
            "Confirm you have rights to the media and that the URL is public.\n"
            f"{detail[-800:]}"
        ) from exc

    matches = sorted(dest_dir.glob("source.*"))
    if not matches:
        raise IngestError("yt-dlp finished but no media file landed in the work directory.")
    # Prefer muxed video files over thumbnails/subs.
    for candidate in matches:
        if candidate.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov", ".m4v"}:
            return candidate
    return matches[0]
