from __future__ import annotations

import re
from pathlib import Path

from alphaclip.models import Cue, Preset, Segment

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "").strip())


def wrap_text(text: str, width: int = 28) -> list[str]:
    """Greedy wrap for vertical captions. Keeps words intact."""
    words = normalize_text(text).split(" ")
    if not words or words == [""]:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if current and len(trial) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def srt_timestamp(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    whole = int(secs)
    millis = int(round((secs - whole) * 1000))
    if millis == 1000:
        whole += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{whole:02d},{millis:03d}"


def ass_timestamp(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def explode_cues(segments: list[Segment], max_words: int = 7, max_chars: int = 42) -> list[Cue]:
    """Turn long transcript segments into bite-size caption cues."""
    cues: list[Cue] = []
    for segment in segments:
        text = normalize_text(segment.text)
        if not text:
            continue
        words = text.split(" ")
        if len(words) <= max_words and len(text) <= max_chars:
            cues.append(Cue(segment.start, segment.end, text))
            continue
        duration = max(segment.duration, 0.01)
        idx = 0
        word_count = len(words)
        while idx < word_count:
            chunk: list[str] = []
            while idx < word_count:
                candidate = chunk + [words[idx]]
                if chunk and (len(candidate) > max_words or len(" ".join(candidate)) > max_chars):
                    break
                chunk = candidate
                idx += 1
            if not chunk:
                chunk = [words[idx]]
                idx += 1
            # Interpolate timing by word coverage inside the segment.
            already = idx - len(chunk)
            start_frac = already / word_count
            end_frac = idx / word_count
            cues.append(
                Cue(
                    start=segment.start + duration * start_frac,
                    end=segment.start + duration * end_frac,
                    text=" ".join(chunk),
                )
            )
    return cues


def shift_cues_to_clip(
    cues: list[Cue],
    clip_start: float,
    clip_end: float,
    pad: float = 0.0,
) -> list[Cue]:
    """Keep cues that overlap the cut, then shift times so the clip starts at 0."""
    shifted: list[Cue] = []
    for cue in cues:
        if cue.end <= clip_start or cue.start >= clip_end:
            continue
        start = max(cue.start, clip_start) - clip_start + pad
        end = min(cue.end, clip_end) - clip_start + pad
        if end - start < 0.12:
            continue
        shifted.append(Cue(start=start, end=end, text=cue.text))
    return shifted


def cues_to_srt(cues: list[Cue], width: int = 28) -> str:
    blocks: list[str] = []
    for i, cue in enumerate(cues, start=1):
        lines = wrap_text(cue.text, width=width)
        if not lines:
            continue
        blocks.append(
            f"{i}\n{srt_timestamp(cue.start)} --> {srt_timestamp(cue.end)}\n" + "\n".join(lines)
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _ass_escape(text: str) -> str:
    """Escape ASS specials. Spaces become hard-spaces so libass cannot collapse them."""
    return (
        text.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace(" ", r"\h")
    )


def _ass_multiline(text: str, width: int) -> str:
    lines = wrap_text(text, width=width)
    return r"\N".join(_ass_escape(line) for line in lines if line)


def cues_to_ass(
    cues: list[Cue],
    preset: Preset,
    clip_duration: float,
    font_name: str = "Inter",
    width: int = 28,
) -> str:
    """Styled 1080x1920 ASS: CTA header, captions, disclaimer footer."""
    caption_lines: list[str] = []
    for cue in cues:
        body = _ass_multiline(cue.text, width=width)
        if not body:
            continue
        caption_lines.append(
            f"Dialogue: 0,{ass_timestamp(cue.start)},{ass_timestamp(cue.end)},"
            f"Caption,,0,0,0,,{body}"
        )

    end = ass_timestamp(max(clip_duration, 0.2))
    cta = _ass_multiline(preset.cta, width=36)
    disclaimer = _ass_multiline(preset.disclaimer, width=48)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font_name},68,{preset.caption_fill},&H000000FF,{preset.caption_outline},&H64000000,-1,0,0,0,100,100,0,0,1,5,0,2,70,70,520,1
Style: CTA,{font_name},34,{preset.cta_fill},&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,3,0,0,8,48,48,72,1
Style: Disclaimer,{font_name},20,&H00B8B4AE,&H000000FF,&H00101010,&H90000000,0,0,0,0,100,100,0,0,3,0,0,2,36,36,36,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,{end},CTA,,0,0,0,,{cta}
Dialogue: 0,0:00:00.00,{end},Disclaimer,,0,0,0,,{disclaimer}
"""
    return header + "\n".join(caption_lines) + ("\n" if caption_lines else "")


def write_ass(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_srt(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def drawtext_escape(text: str) -> str:
    """Escape a single line for ffmpeg drawtext=text='…'.

    Apostrophes become a typographic quote so they cannot break the filter
    graph's single-quoted text= argument.
    """
    return (
        text.replace("'", "’")
        .replace("\\", r"\\\\")
        .replace(":", r"\:")
        .replace("%", r"\%")
    )


def drawtext_multiline(text: str, width: int) -> str:
    lines = wrap_text(text, width=width)
    return r"\n".join(drawtext_escape(line) for line in lines if line)


def build_clip_captions(
    segments: list[Segment],
    clip_start: float,
    clip_end: float,
    preset: Preset,
    font_name: str = "Inter",
) -> tuple[str, str, list[Cue]]:
    cues = shift_cues_to_clip(explode_cues(segments), clip_start, clip_end)
    duration = max(0.2, clip_end - clip_start)
    ass = cues_to_ass(
        cues,
        preset,
        clip_duration=duration,
        font_name=font_name,
        width=preset.caption_max_chars,
    )
    srt = cues_to_srt(cues, width=preset.caption_max_chars)
    return ass, srt, cues
