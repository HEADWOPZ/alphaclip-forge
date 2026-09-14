from __future__ import annotations

import re
from alphaclip.models import Highlight, Preset, Segment

_TOPIC_STOP = {
    "this",
    "that",
    "with",
    "from",
    "your",
    "have",
    "just",
    "into",
    "about",
    "them",
    "they",
    "what",
    "when",
    "where",
    "which",
    "while",
    "then",
    "than",
    "because",
    "really",
    "actually",
    "going",
    "gonna",
    "want",
    "need",
}


def extract_topic(text: str, preset: Preset) -> str:
    lowered = text.lower()
    ranked: list[tuple[float, str]] = []
    for phrase, weight in preset.keywords.items():
        if phrase in lowered:
            ranked.append((weight, phrase))
    if ranked:
        ranked.sort(reverse=True)
        return ranked[0][1]
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text) if w.lower() not in _TOPIC_STOP]
    if words:
        return words[0]
    return preset.name.lower()


def _fill(template: str, topic: str) -> str:
    try:
        return template.format(topic=topic)
    except (KeyError, IndexError, ValueError):
        return template


def generate_hook_variants(text: str, preset: Preset, count: int = 6) -> list[str]:
    topic = extract_topic(text, preset)
    variants: list[str] = []
    for hook in preset.hooks:
        variants.append(hook)
    for template in preset.title_templates:
        variants.append(_fill(template, topic))
    # Dedup, preserve order, keep punchy length.
    seen: set[str] = set()
    unique: list[str] = []
    for item in variants:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item.strip())
        if len(unique) >= count:
            break
    return unique


def generate_titles(text: str, preset: Preset, count: int = 5) -> list[str]:
    topic = extract_topic(text, preset)
    titles = [_fill(t, topic) for t in preset.title_templates]
    punch = _first_sentence(text)
    if punch and 12 <= len(punch) <= 72:
        titles.insert(0, punch)
    seen: set[str] = set()
    out: list[str] = []
    for title in titles:
        key = title.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(title.strip())
        if len(out) >= count:
            break
    return out


def _first_sentence(text: str) -> str:
    bit = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return bit.strip().strip('"')


def decorate_highlights(highlights: list[Highlight], preset: Preset) -> list[Highlight]:
    for highlight in highlights:
        titles = generate_titles(highlight.text, preset)
        hooks = generate_hook_variants(highlight.text, preset)
        highlight.titles = titles
        highlight.hooks = hooks
        highlight.title = titles[0] if titles else preset.name
        highlight.hook = hooks[0] if hooks else preset.hooks[0]
    return highlights


def transcript_blurb(segments: list[Segment], limit: int = 400) -> str:
    text = " ".join(s.text.strip() for s in segments if s.text.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"
