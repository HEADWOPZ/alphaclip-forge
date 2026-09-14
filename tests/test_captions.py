from __future__ import annotations

from alphaclip.captions import (
    ass_timestamp,
    build_clip_captions,
    cues_to_ass,
    cues_to_srt,
    drawtext_escape,
    drawtext_multiline,
    explode_cues,
    shift_cues_to_clip,
    srt_timestamp,
    wrap_text,
)
from alphaclip.models import Cue, Segment


def test_srt_timestamp_padding():
    assert srt_timestamp(0) == "00:00:00,000"
    assert srt_timestamp(61.5) == "00:01:01,500"
    assert srt_timestamp(3661.234) == "01:01:01,234"


def test_ass_timestamp_format():
    assert ass_timestamp(0) == "0:00:00.00"
    assert ass_timestamp(12.5) == "0:00:12.50"
    assert ass_timestamp(75.04) == "0:01:15.04"


def test_wrap_text_keeps_words():
    lines = wrap_text("Revoke that unlimited approval tonight", width=18)
    assert lines
    assert all(len(line) <= 22 for line in lines)
    assert "unlimited" in " ".join(lines)


def test_explode_cues_splits_long_segments():
    segments = [
        Segment(0, 8, "one two three four five six seven eight nine ten eleven twelve"),
    ]
    cues = explode_cues(segments, max_words=5, max_chars=40)
    assert len(cues) >= 2
    assert cues[0].start == 0
    assert abs(cues[-1].end - 8) < 1e-6
    assert all(c.end > c.start for c in cues)


def test_shift_cues_clips_and_rebases():
    cues = [Cue(3.0, 7.0, "hello"), Cue(9.0, 12.0, "outside"), Cue(6.5, 10.0, "overlap")]
    shifted = shift_cues_to_clip(cues, clip_start=5.0, clip_end=9.0)
    assert [c.text for c in shifted] == ["hello", "overlap"]
    assert abs(shifted[0].start - 0.0) < 1e-6  # 5.0 - 5.0, clamped from 3
    assert shifted[0].end <= 4.0
    assert all(c.start >= 0 for c in shifted)


def test_cues_to_srt_roundtrip():
    srt = cues_to_srt([Cue(0.0, 1.25, "Don't fade this tape")], width=28)
    assert "00:00:00,000 --> 00:00:01,250" in srt
    assert "Don't fade this tape" in srt
    assert srt.startswith("1\n")


def test_ass_contains_cta_disclaimer_and_caption(trench):
    ass = cues_to_ass(
        [Cue(0.2, 2.0, "The whale got wrecked")],
        trench,
        clip_duration=10.0,
    )
    assert "PlayResX: 1080" in ass
    assert "PlayResY: 1920" in ass
    assert "Style: Caption" in ass
    assert "Style: CTA" in ass
    assert "Style: Disclaimer" in ass
    assert "Follow" in ass
    assert r"Not\hfinancial\hadvice" in ass
    assert "whale" in ass
    assert r"\N" in ass
    assert r"\\N" not in ass
    assert "CTA,," in ass


def test_drawtext_keeps_spaces_and_escapes():
    assert "Follow for daily" in drawtext_escape("Follow for daily")
    assert r"\:" in drawtext_escape("watch: this")
    multi = drawtext_multiline("Follow for daily trench recaps — next clip in the stack.", width=28)
    assert "Follow for" in multi
    assert r"\n" in multi


def test_build_clip_captions_from_demo(demo_segments, trench):
    ass, srt, cues = build_clip_captions(demo_segments, 4.0, 16.0, trench)
    assert cues
    assert "-->" in srt
    assert "Dialogue:" in ass
    # Times are clip-relative, so nothing should start before 0.
    assert all(c.start >= 0 for c in cues)
    assert all(c.end <= 12.01 for c in cues)
