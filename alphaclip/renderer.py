from __future__ import annotations

from pathlib import Path

from alphaclip.captions import (
    build_clip_captions,
    drawtext_escape,
    wrap_text,
    write_ass,
    write_srt,
)
from alphaclip.config import VERTICAL_HEIGHT, VERTICAL_WIDTH, resolve_font
from alphaclip.media import run_ffmpeg, video_size
from alphaclip.models import Cue, Preset, Segment


def _escape_filter_path(path: Path) -> str:
    return path.resolve().as_posix().replace("\\", "\\\\").replace(":", r"\:")


def _line(
    fontfile: str,
    text: str,
    *,
    color: str,
    size: int,
    y: str,
    enable: str | None = None,
) -> str:
    pieces = [
        f"drawtext=fontfile={fontfile}",
        f"text='{drawtext_escape(text)}'",
        f"fontcolor={color}:fontsize={size}",
        "x=(w-text_w)/2",
        f"y={y}",
        "box=1:boxcolor=black@0.55:boxborderw=10",
    ]
    if enable:
        pieces.append(f"enable='{enable}'")
    return ":".join(pieces)


def _stack(
    fontfile: str,
    text: str,
    *,
    width: int,
    color: str,
    size: int,
    y_expr: str,
    step: int,
    enable: str | None = None,
) -> list[str]:
    """One drawtext per wrapped line so we never put \\n inside the filter graph."""
    lines = wrap_text(text, width=width)
    filters: list[str] = []
    for index, line in enumerate(lines):
        y = y_expr if index == 0 else f"{y_expr}+{index * step}"
        filters.append(
            _line(
                fontfile,
                line,
                color=color,
                size=size,
                y=y,
                enable=enable,
            )
        )
    return filters


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
    font_name = "Liberation Sans" if "Liberation" in font.name else "Inter"
    ass_text, srt_text, cues = build_clip_captions(
        segments, start, end, preset, font_name=font_name
    )
    write_ass(work_dir / f"{output_path.stem}.ass", ass_text)
    write_srt(work_dir / f"{output_path.stem}.srt", srt_text)

    fontfile = _escape_filter_path(font)
    filters = [
        f"scale={VERTICAL_WIDTH}:{VERTICAL_HEIGHT}:force_original_aspect_ratio=increase",
        f"crop={VERTICAL_WIDTH}:{VERTICAL_HEIGHT}",
        "setsar=1",
        *_stack(
            fontfile,
            preset.cta,
            width=32,
            color="0xFFD400",
            size=28,
            y_expr="72",
            step=36,
        ),
        *_stack(
            fontfile,
            preset.disclaimer,
            width=42,
            color="0xC8C2B8",
            size=18,
            y_expr="h-th-140",
            step=26,
        ),
    ]
    for cue in cues:
        enable = f"between(t\\,{cue.start:.3f}\\,{cue.end:.3f})"
        filters.extend(
            _stack(
                fontfile,
                cue.text,
                width=preset.caption_max_chars,
                color="0xFFFFFF",
                size=52,
                y_expr="h-th-460",
                step=64,
                enable=enable,
            )
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
            ",".join(filters),
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
