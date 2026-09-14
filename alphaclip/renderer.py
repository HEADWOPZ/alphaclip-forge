from __future__ import annotations

from pathlib import Path

from alphaclip.captions import build_clip_captions, write_ass, write_srt
from alphaclip.config import VERTICAL_HEIGHT, VERTICAL_WIDTH, resolve_font
from alphaclip.media import run_ffmpeg, video_size
from alphaclip.models import Cue, Preset, Segment


def _escape_subtitles_path(path: Path) -> str:
    """Escape a path for ffmpeg's subtitles filter."""
    text = path.resolve().as_posix()
    return (
        text.replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )


def render_vertical_clip(
    source: Path,
    start: float,
    end: float,
    segments: list[Segment],
    preset: Preset,
    output_path: Path,
    work_dir: Path,
) -> tuple[Path, list[Cue]]:
    """Cut [start, end], crop/pad to 9:16 1080x1920, burn captions + CTA + disclaimer."""
    if end <= start:
        raise ValueError("Clip end must be after start.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font = resolve_font()
    font_name = "Inter" if "Inter" in font.name else "Liberation Sans"
    ass_text, srt_text, cues = build_clip_captions(
        segments, start, end, preset, font_name=font_name
    )
    ass_path = write_ass(work_dir / f"{output_path.stem}.ass", ass_text)
    write_srt(work_dir / f"{output_path.stem}.srt", srt_text)

    fontsdir = _escape_subtitles_path(font.parent)
    ass_escaped = _escape_subtitles_path(ass_path)
    vf = (
        f"scale={VERTICAL_WIDTH}:{VERTICAL_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VERTICAL_WIDTH}:{VERTICAL_HEIGHT},"
        f"subtitles='{ass_escaped}':fontsdir='{fontsdir}'"
    )
    run_ffmpeg(
        [
            "-ss",
            f"{start:.3f}",
            "-to",
            f"{end:.3f}",
            "-i",
            str(source),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    width, height = video_size(output_path)
    if (width, height) != (VERTICAL_WIDTH, VERTICAL_HEIGHT):
        raise RuntimeError(
            f"Rendered clip is {width}x{height}, expected "
            f"{VERTICAL_WIDTH}x{VERTICAL_HEIGHT}."
        )
    return output_path, cues
