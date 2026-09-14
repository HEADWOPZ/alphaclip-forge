from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

PROVIDERS = ("buffer", "late")

BUFFER_ENDPOINT = "https://api.bufferapp.com/1/updates/create.json"
LATE_ENDPOINT = "https://getlate.dev/api/v1/posts"


class ScheduleError(RuntimeError):
    pass


def _require_provider(provider: str) -> str:
    key = (provider or "").strip().lower()
    if key not in PROVIDERS:
        raise ScheduleError(f"Unknown provider '{provider}'. Use: {', '.join(PROVIDERS)}")
    return key


def credentials(provider: str) -> dict[str, str]:
    provider = _require_provider(provider)
    if provider == "buffer":
        token = os.environ.get("BUFFER_ACCESS_TOKEN", "").strip()
        profile = os.environ.get("BUFFER_PROFILE_ID", "").strip()
        return {"access_token": token, "profile_id": profile}
    return {
        "api_key": os.environ.get("LATE_API_KEY", "").strip(),
        "account_id": os.environ.get("LATE_ACCOUNT_ID", "").strip(),
    }


def has_credentials(provider: str) -> bool:
    creds = credentials(provider)
    return all(bool(v) for v in creds.values())


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ScheduleError(f"metadata.json not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def plan_posts(
    metadata: dict[str, Any],
    cadence_hours: float = 8.0,
    start: datetime | None = None,
) -> list[dict[str, Any]]:
    start_at = start or datetime.now(timezone.utc) + timedelta(minutes=30)
    clips = metadata.get("clips") or []
    plan: list[dict[str, Any]] = []
    for index, clip in enumerate(clips):
        when = start_at + timedelta(hours=cadence_hours * index)
        caption = _caption_for_clip(clip, metadata)
        plan.append(
            {
                "filename": clip.get("filename"),
                "title": clip.get("title"),
                "hook": clip.get("hook"),
                "text": caption,
                "scheduled_at": when.isoformat(),
                "platforms": ["tiktok", "youtube_shorts"],
            }
        )
    return plan


def _caption_for_clip(clip: dict[str, Any], metadata: dict[str, Any]) -> str:
    hook = clip.get("hook") or clip.get("title") or "New clip"
    cta = clip.get("cta") or (metadata.get("preset") or {}).get("cta") or ""
    disclaimer = clip.get("disclaimer") or (metadata.get("preset") or {}).get("disclaimer") or ""
    return f"{hook}\n\n{cta}\n\n{disclaimer}".strip()


def build_payloads(provider: str, plan: list[dict[str, Any]], creds: dict[str, str]) -> list[dict[str, Any]]:
    provider = _require_provider(provider)
    payloads: list[dict[str, Any]] = []
    if provider == "buffer":
        for item in plan:
            payloads.append(
                {
                    "url": BUFFER_ENDPOINT,
                    "method": "POST",
                    "data": {
                        "profile_ids[]": creds.get("profile_id"),
                        "text": item["text"],
                        "scheduled_at": item["scheduled_at"],
                        "media[title]": item.get("title"),
                    },
                }
            )
        return payloads
    for item in plan:
        payloads.append(
            {
                "url": LATE_ENDPOINT,
                "method": "POST",
                "headers": {"Authorization": f"Bearer {creds.get('api_key')}"},
                "json": {
                    "accountId": creds.get("account_id"),
                    "text": item["text"],
                    "scheduledFor": item["scheduled_at"],
                    "platforms": item["platforms"],
                    "title": item.get("title"),
                },
            }
        )
    return payloads


def schedule(
    metadata_path: Path,
    provider: str = "buffer",
    dry_run: bool | None = None,
    cadence_hours: float = 8.0,
) -> dict[str, Any]:
    """
    Env-gated scheduler.

    Without BUFFER_* / LATE_* keys, always dry-runs.
    With keys, still dry-runs unless dry_run=False — v1 never auto-posts by accident.
    """
    provider = _require_provider(provider)
    metadata = load_metadata(metadata_path)
    plan = plan_posts(metadata, cadence_hours=cadence_hours)
    creds = credentials(provider)
    ready = has_credentials(provider)
    if dry_run is None:
        dry_run = True
    if not ready:
        dry_run = True

    payloads = build_payloads(provider, plan, creds)
    results: list[dict[str, Any]] = []
    if dry_run:
        for item, payload in zip(plan, payloads):
            results.append(
                {
                    "status": "dry-run",
                    "filename": item["filename"],
                    "scheduled_at": item["scheduled_at"],
                    "would_call": _redact(payload),
                }
            )
        return {
            "provider": provider,
            "dry_run": True,
            "reason": None if ready else f"missing {provider} credentials",
            "posts": results,
        }

    for item, payload in zip(plan, payloads):
        results.append(_post(payload, filename=item["filename"]))
    return {"provider": provider, "dry_run": False, "posts": results}


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(payload))
    headers = clone.get("headers") or {}
    if "Authorization" in headers:
        headers["Authorization"] = "Bearer ***"
    data = clone.get("data") or {}
    if "access_token" in data:
        data["access_token"] = "***"
    return clone


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {"api.bufferapp.com", "getlate.dev"}


def _post(payload: dict[str, Any], filename: str) -> dict[str, Any]:
    url = payload["url"]
    if not _host_allowed(url):
        raise ScheduleError(f"Refusing to POST to unexpected host: {url}")
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(
                payload.get("method") or "POST",
                url,
                data=payload.get("data"),
                json=payload.get("json"),
                headers=payload.get("headers"),
            )
        return {
            "status": "submitted" if response.is_success else "error",
            "filename": filename,
            "http_status": response.status_code,
            "body": response.text[:400],
        }
    except httpx.HTTPError as exc:
        return {"status": "error", "filename": filename, "error": str(exc)}
