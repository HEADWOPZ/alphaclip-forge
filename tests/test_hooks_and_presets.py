from __future__ import annotations

from alphaclip.hooks import decorate_highlights, generate_hook_variants, generate_titles
from alphaclip.presets import PRESETS, get_preset, list_presets
from alphaclip.scorer import select_highlights


def test_three_presets_registered():
    ids = {p.id for p in list_presets()}
    assert ids == {"trench-recap", "protocol-explainer", "wallet-security-tip"}
    for preset in PRESETS.values():
        assert preset.hooks
        assert preset.cta
        assert "not financial advice" in preset.disclaimer.lower()
        assert preset.keywords


def test_unknown_preset_errors():
    try:
        get_preset("face-farm")
    except ValueError as exc:
        assert "trench-recap" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_hook_variants_include_preset_voice(trench):
    hooks = generate_hook_variants("The whale got liquidated on 40x", trench)
    assert hooks
    assert any("trench" in h.lower() or "wrecked" in h.lower() or "tape" in h.lower() for h in hooks)
    titles = generate_titles("The whale got liquidated on 40x", trench)
    assert titles
    assert any("liquidation" in t.lower() or "whale" in t.lower() for t in titles)


def test_decorate_highlights_fills_titles(demo_segments, security):
    picks = select_highlights(demo_segments, security, max_clips=1, media_duration=32)
    decorate_highlights(picks, security)
    assert picks[0].title
    assert picks[0].hook
    assert picks[0].titles
    assert picks[0].hooks
