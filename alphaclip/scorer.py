from __future__ import annotations

import re
from dataclasses import dataclass

from alphaclip.models import Highlight, Preset, Segment

_WORD_RE = re.compile(r"[a-z0-9$%]+")
_MONEY_RE = re.compile(r"\$[\d,.]+|\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?x\b", re.I)
_CAPS_RE = re.compile(r"\b[A-Z]{3,}\b")
_PUNCT_ENERGY_RE = re.compile(r"[!?]{1,}")
_FILLER = {
    "um",
    "uh",
    "like",
    "you know",
    "sort of",
    "kind of",
    "anyway",
    "basically",
}


@dataclass(frozen=True)
class Window:
    start: float
    end: float
    text: str
    segment_indexes: tuple[int, ...]

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _keyword_hits(text: str, keywords: dict[str, float]) -> tuple[float, list[str]]:
    lowered = f" {text.lower()} "
    score = 0.0
    hits: list[str] = []
    for phrase, weight in keywords.items():
        token = phrase.lower()
        found = token in text.lower() if " " in token else f" {token} " in lowered
        if found:
            score += weight
            hits.append(phrase)
    return score, hits


def energy_score(text: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    money = _MONEY_RE.findall(text)
    if money:
        score += min(2.4, 0.8 * len(money))
        reasons.append(f"numbers:{','.join(money[:3])}")
    caps = [c for c in _CAPS_RE.findall(text) if c.lower() not in {"the", "and", "for", "you"}]
    if caps:
        score += min(1.5, 0.4 * len(caps))
        reasons.append("emphasis")
    bangs = _PUNCT_ENERGY_RE.findall(text)
    if bangs:
        score += min(1.2, 0.4 * len(bangs))
        reasons.append("punch")
    if text.strip().endswith("?"):
        score += 0.35
        reasons.append("question")
    filler_hits = sum(1 for f in _FILLER if f in text.lower())
    score -= 0.25 * filler_hits
    return score, reasons


def score_text(text: str, preset: Preset) -> tuple[float, list[str]]:
    kw_score, hits = _keyword_hits(text, preset.keywords)
    en_score, en_reasons = energy_score(text)
    density = 0.0
    words = tokenize(text)
    if words:
        density = kw_score / max(4.0, len(words) / 6.0)
    total = kw_score + en_score + min(1.5, density)
    reasons = [f"kw:{h}" for h in hits[:6]] + en_reasons
    if not reasons:
        reasons = ["neutral"]
    return round(total, 4), reasons


def candidate_windows(
    segments: list[Segment],
    min_duration: float,
    max_duration: float,
) -> list[Window]:
    """Build contiguous segment spans that land in the target duration band."""
    windows: list[Window] = []
    n = len(segments)
    for i in range(n):
        texts: list[str] = []
        for j in range(i, n):
            texts.append(segments[j].text.strip())
            start = segments[i].start
            end = segments[j].end
            dur = end - start
            if dur < min_duration:
                continue
            if dur > max_duration:
                break
            windows.append(
                Window(
                    start=start,
                    end=end,
                    text=" ".join(t for t in texts if t),
                    segment_indexes=tuple(range(i, j + 1)),
                )
            )
    return windows


def _overlaps(a: Window | Highlight, b: Window | Highlight, gap: float = 0.4) -> bool:
    return not (a.end + gap <= b.start or b.end + gap <= a.start)


def select_highlights(
    segments: list[Segment],
    preset: Preset,
    max_clips: int | None = None,
    media_duration: float | None = None,
) -> list[Highlight]:
    if not segments:
        return []
    max_n = max_clips if max_clips is not None else preset.max_clips
    windows = candidate_windows(segments, preset.min_duration, preset.max_duration)
    if not windows:
        # Fall back to the fullest span we have so a short fixture still exports.
        start = segments[0].start
        end = segments[-1].end
        if media_duration is not None:
            end = min(end, media_duration)
        windows = [
            Window(
                start=start,
                end=end,
                text=" ".join(s.text.strip() for s in segments if s.text.strip()),
                segment_indexes=tuple(range(len(segments))),
            )
        ]

    ranked: list[tuple[float, list[str], Window]] = []
    for window in windows:
        raw, reasons = score_text(window.text, preset)
        # Prefer windows near the preset target length.
        length_penalty = abs(window.duration - preset.target_duration) * 0.06
        ranked.append((raw - length_penalty, reasons, window))

    ranked.sort(key=lambda item: item[0], reverse=True)

    picked: list[Highlight] = []
    for score, reasons, window in ranked:
        if len(picked) >= max_n:
            break
        if any(_overlaps(window, existing) for existing in picked):
            continue
        start = max(0.0, window.start)
        end = window.end
        if media_duration is not None:
            end = min(end, media_duration)
        if end - start < 3.0:
            continue
        picked.append(
            Highlight(
                start=round(start, 3),
                end=round(end, 3),
                score=round(score, 4),
                text=window.text,
                reasons=reasons,
            )
        )
    picked.sort(key=lambda h: h.start)
    return picked
