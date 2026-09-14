from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class Cue:
    """A caption cue with times relative to the clip (or source, if unshifted)."""

    start: float
    end: float
    text: str


@dataclass
class Highlight:
    start: float
    end: float
    score: float
    text: str
    reasons: list[str] = field(default_factory=list)
    title: str = ""
    hook: str = ""
    titles: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    description: str
    hooks: list[str]
    title_templates: list[str]
    cta: str
    disclaimer: str
    keywords: dict[str, float]
    caption_max_chars: int = 28
    target_duration: float = 18.0
    min_duration: float = 10.0
    max_duration: float = 32.0
    max_clips: int = 3
    caption_fill: str = "&H00FFFFFF"
    caption_outline: str = "&H00000000"
    cta_fill: str = "&H0000D4FF"
    accent_hex: str = "F0B429"


@dataclass
class Transcript:
    language: str
    segments: list[Segment]
    source: str = ""
    engine: str = "mock"

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "source": self.source,
            "engine": self.engine,
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text} for s in self.segments
            ],
        }


@dataclass
class RenderedClip:
    path: str
    filename: str
    start: float
    end: float
    duration: float
    width: int
    height: int
    score: float
    title: str
    hook: str
    titles: list[str]
    hooks: list[str]
    cta: str
    disclaimer: str
    reasons: list[str]
    text: str


@dataclass
class JobResult:
    job_id: str
    source: str
    preset_id: str
    work_dir: str
    clips: list[RenderedClip]
    zip_path: str
    metadata_path: str
    transcript_engine: str
    mock: bool
