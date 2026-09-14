from __future__ import annotations

from alphaclip.models import Segment
from alphaclip.scorer import candidate_windows, score_text, select_highlights


def test_liquidation_outscores_filler(trench):
    hot, hot_reasons = score_text(
        "Three liquidations cascaded. The whale got wrecked on 40x leverage.",
        trench,
    )
    cold, _ = score_text("Um, like, anyway, we were just talking about lunch.", trench)
    assert hot > cold + 2
    assert any(r.startswith("kw:") for r in hot_reasons)
    assert any("40x" in r or "numbers" in r for r in hot_reasons)


def test_preset_keywords_rerank(protocol, security):
    text = "Revoke that unlimited approval before the drainer hits your wallet."
    sec, _ = score_text(text, security)
    proto, _ = score_text(text, protocol)
    assert sec > proto

    mech = "Deposits go into a vault, then the AMM, and the oracle updates."
    proto2, reasons = score_text(mech, protocol)
    sec2, _ = score_text(mech, security)
    assert proto2 > sec2
    assert "kw:amm" in reasons or "kw:oracle" in reasons or "kw:vault" in reasons


def test_candidate_windows_respect_duration_band(demo_segments, trench):
    windows = candidate_windows(demo_segments, trench.min_duration, trench.max_duration)
    assert windows
    assert all(trench.min_duration <= w.duration <= trench.max_duration + 1e-6 for w in windows)


def test_select_highlights_non_overlapping(demo_segments, trench):
    picks = select_highlights(demo_segments, trench, max_clips=3, media_duration=32.0)
    assert picks
    assert len(picks) <= 3
    ordered = sorted(picks, key=lambda h: h.start)
    for prev, nxt in zip(ordered, ordered[1:]):
        assert prev.end <= nxt.start + 0.41
    assert all(10 <= h.duration <= 32 for h in picks)


def test_trench_highlight_mentions_tape(demo_segments, trench):
    picks = select_highlights(demo_segments, trench, max_clips=2, media_duration=32.0)
    blob = " ".join(h.text.lower() for h in picks)
    assert "liquidation" in blob or "airdrop" in blob or "runner" in blob


def test_security_highlight_mentions_drain(demo_segments, security):
    picks = select_highlights(demo_segments, security, max_clips=1, media_duration=32.0)
    assert picks
    blob = picks[0].text.lower()
    assert "drain" in blob or "approval" in blob or "seed" in blob


def test_short_source_still_yields_a_clip(trench):
    segments = [
        Segment(0, 2.0, "The whale just got liquidated."),
        Segment(2.0, 4.5, "That airdrop runner is unhinged."),
    ]
    picks = select_highlights(segments, trench, max_clips=1, media_duration=4.5)
    assert len(picks) == 1
    assert picks[0].end <= 4.5
