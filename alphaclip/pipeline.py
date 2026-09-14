from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

from alphaclip.config import FIXTURES_DIR, VERTICAL_HEIGHT, VERTICAL_WIDTH, work_root
from alphaclip.export import build_metadata, job_from_parts, write_metadata, zip_export
from alphaclip.hooks import decorate_highlights
from alphaclip.ingest import classify_source, ingest_source
from alphaclip.media import media_duration, video_size
from alphaclip.models import JobResult, RenderedClip
from alphaclip.presets import get_preset
from alphaclip.renderer import render_vertical_clip
from alphaclip.scorer import select_highlights
from alphaclip.transcript import transcribe


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text[:48] or "clip"


def default_mock_transcript() -> Path:
    return FIXTURES_DIR / "demo_transcript.json"


def forge(
    source: str,
    preset_id: str = "trench-recap",
    mock_transcript: Path | bool | None = None,
    out_dir: Path | None = None,
    work_dir: Path | None = None,
    max_clips: int | None = None,
    whisper_model: str | None = None,
    job_id: str | None = None,
) -> JobResult:
    """Run the full ingest → transcript → score → cut → caption → zip pipeline."""
    preset = get_preset(preset_id)
    job_id = job_id or uuid.uuid4().hex[:12]
    root = Path(out_dir) if out_dir else work_root() / "jobs" / job_id
    dest = Path(work_dir) if work_dir else root
    dest.mkdir(parents=True, exist_ok=True)

    mock_path: Path | None = None
    if mock_transcript is True:
        mock_path = default_mock_transcript()
    elif isinstance(mock_transcript, Path):
        mock_path = mock_transcript
    elif isinstance(mock_transcript, str):
        mock_path = Path(mock_transcript)

    source_kind = classify_source(source)
    media_path = ingest_source(source, dest / "ingest")
    duration = media_duration(media_path)

    transcript = transcribe(
        media_path,
        dest,
        mock_path=mock_path,
        model=whisper_model,
    )
    highlights = decorate_highlights(
        select_highlights(
            transcript.segments,
            preset,
            max_clips=max_clips,
            media_duration=duration,
        ),
        preset,
    )
    if not highlights:
        raise RuntimeError("Highlight scorer produced no clips. Try another preset or a longer source.")

    clips_dir = dest / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[RenderedClip] = []
    for index, highlight in enumerate(highlights, start=1):
        filename = f"{index:02d}-{slugify(highlight.title or preset.id)}.mp4"
        output = clips_dir / filename
        render_vertical_clip(
            source=media_path,
            start=highlight.start,
            end=min(highlight.end, duration),
            segments=transcript.segments,
            preset=preset,
            output_path=output,
            work_dir=dest / "captions",
        )
        width, height = video_size(output)
        rendered.append(
            RenderedClip(
                path=str(output),
                filename=filename,
                start=highlight.start,
                end=min(highlight.end, duration),
                duration=round(min(highlight.end, duration) - highlight.start, 3),
                width=width,
                height=height,
                score=highlight.score,
                title=highlight.title,
                hook=highlight.hook,
                titles=highlight.titles,
                hooks=highlight.hooks,
                cta=preset.cta,
                disclaimer=preset.disclaimer,
                reasons=highlight.reasons,
                text=highlight.text,
            )
        )

    metadata = build_metadata(
        job_id=job_id,
        source=str(source),
        source_kind=source_kind,
        preset=preset,
        clips=rendered,
        transcript_engine=transcript.engine,
        mock=bool(mock_path),
    )
    metadata_path = write_metadata(dest / "metadata.json", metadata)
    zip_path = zip_export(root / f"alphaclip-{preset.id}-{job_id}.zip", rendered, metadata_path)
    # Keep a copy of metadata next to the zip for `alphaclip schedule`.
    if metadata_path.parent != zip_path.parent:
        shutil.copy2(metadata_path, zip_path.parent / "metadata.json")

    manifest = {
        "job_id": job_id,
        "zip": str(zip_path),
        "clips": [c.filename for c in rendered],
        "preset": preset.id,
    }
    (dest / "job.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Sanity: at least one vertical clip on disk.
    if not rendered or rendered[0].width != VERTICAL_WIDTH or rendered[0].height != VERTICAL_HEIGHT:
        raise RuntimeError("Forge finished but did not produce a 1080x1920 clip.")

    return job_from_parts(
        job_id=job_id,
        source=str(source),
        preset_id=preset.id,
        work_dir=dest,
        clips=rendered,
        zip_path=zip_path,
        metadata_path=metadata_path,
        transcript_engine=transcript.engine,
        mock=bool(mock_path),
    )
