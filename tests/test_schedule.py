from __future__ import annotations

import json
from pathlib import Path

from alphaclip.schedule import build_payloads, has_credentials, plan_posts, schedule


def _meta() -> dict:
    return {
        "preset": {"cta": "Follow for recaps", "disclaimer": "Not financial advice."},
        "clips": [
            {
                "filename": "01-clip.mp4",
                "title": "Trench recap",
                "hook": "The trenches printed.",
                "cta": "Follow for recaps",
                "disclaimer": "Not financial advice.",
            }
        ],
    }


def test_plan_posts_staggers(tmp_path: Path):
    plan = plan_posts(_meta(), cadence_hours=8)
    assert len(plan) == 1
    assert "Not financial advice" in plan[0]["text"]
    assert "tiktok" in plan[0]["platforms"]


def test_dry_run_without_keys(tmp_path: Path, monkeypatch):
    for key in ("BUFFER_ACCESS_TOKEN", "BUFFER_PROFILE_ID", "LATE_API_KEY", "LATE_ACCOUNT_ID"):
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / "metadata.json"
    path.write_text(json.dumps(_meta()), encoding="utf-8")
    result = schedule(path, provider="buffer", dry_run=None)
    assert result["dry_run"] is True
    assert result["posts"][0]["status"] == "dry-run"
    assert "updates/create.json" in result["posts"][0]["would_call"]["url"]


def test_payload_redaction_late(monkeypatch):
    monkeypatch.setenv("LATE_API_KEY", "secret-key")
    monkeypatch.setenv("LATE_ACCOUNT_ID", "acc_1")
    assert has_credentials("late")
    payloads = build_payloads("late", plan_posts(_meta()), {"api_key": "secret-key", "account_id": "acc_1"})
    assert payloads[0]["json"]["accountId"] == "acc_1"
    assert "Bearer" in payloads[0]["headers"]["Authorization"]
