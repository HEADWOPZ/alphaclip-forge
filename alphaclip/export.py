from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alphaclip import __version__
from alphaclip.models import JobResult, Preset, RenderedClip


def clip_to_meta(clip: RenderedClip, preset: Preset) -> dict[str, Any]:
    return {
        "filename": clip.filename,
        "start": clip.start,
        "end": clip.end,
        "duration": clip.duration,
        "width": clip.width,
        "height": clip.height,
        "score": clip.score,
        "title": clip.title,
        "titles": clip.titles,
        "hook": clip.hook,
        "hooks": clip.hooks,
        "cta": clip.cta,
        "disclaimer": clip.disclaimer,
        "reasons": clip.reasons,
        "text": clip.text,
        "preset": preset.id,
    }


def build_metadata(
    job_id: str,
    source: str,
    source_kind: str,
    preset: Preset,
    clips: list[RenderedClip],
    transcript_engine: str,
    mock: bool,
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generator": f"alphaclip-forge/{__version__}",
        "source": source,
        "source_kind": source_kind,
        "preset": {
            "id": preset.id,
            "name": preset.name,
            "cta": preset.cta,
            "disclaimer": preset.disclaimer,
        },
        "transcript_engine": transcript_engine,
        "mock": mock,
        "clip_count": len(clips),
        "clips": [clip_to_meta(clip, preset) for clip in clips],
        "notices": [
            "You must own or have a license to the source media. AlphaClip does not grant rights.",
            "Output is not financial advice. Crypto is volatile. Do your own research.",
            "Captions are machine-generated and may be inaccurate.",
        ],
    }


def write_metadata(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def zip_export(zip_path: Path, clips: list[RenderedClip], metadata_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(metadata_path, arcname="metadata.json")
        for clip in clips:
            zf.write(clip.path, arcname=f"clips/{clip.filename}")
    return zip_path


def job_from_parts(
    job_id: str,
    source: str,
    preset_id: str,
    work_dir: Path,
    clips: list[RenderedClip],
    zip_path: Path,
    metadata_path: Path,
    transcript_engine: str,
    mock: bool,
) -> JobResult:
    return JobResult(
        job_id=job_id,
        source=source,
        preset_id=preset_id,
        work_dir=str(work_dir),
        clips=clips,
        zip_path=str(zip_path),
        metadata_path=str(metadata_path),
        transcript_engine=transcript_engine,
        mock=mock,
    )
