from __future__ import annotations

import json
import subprocess
from pathlib import Path

from alphaclip.config import default_whisper_model, whisper_cli
from alphaclip.models import Segment, Transcript


class TranscriptError(RuntimeError):
    pass


def load_mock_transcript(path: Path) -> Transcript:
    if not path.is_file():
        raise TranscriptError(f"Mock transcript not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    segments_raw = data.get("segments") or []
    segments = [
        Segment(
            start=float(item["start"]),
            end=float(item["end"]),
            text=str(item.get("text") or "").strip(),
        )
        for item in segments_raw
        if item.get("text")
    ]
    if not segments:
        raise TranscriptError(f"Mock transcript {path} has no usable segments.")
    return Transcript(
        language=str(data.get("language") or "en"),
        segments=segments,
        source=str(data.get("source") or path.name),
        engine="mock",
    )


def transcribe(
    media_path: Path,
    work_dir: Path,
    mock_path: Path | None = None,
    model: str | None = None,
) -> Transcript:
    if mock_path:
        transcript = load_mock_transcript(mock_path)
        _write_json(work_dir / "transcript.json", transcript)
        return transcript

    model_name = model or default_whisper_model()
    transcript = _transcribe_faster_whisper(media_path, model_name)
    if transcript is None:
        transcript = _transcribe_whisper_cli(media_path, work_dir, model_name)
    if transcript is None:
        raise TranscriptError(
            "No speech-to-text engine available. Install `faster-whisper` "
            "(pip install 'alphaclip-forge[whisper]') or the `whisper` CLI, "
            "or rerun with --mock-transcript (fixtures/demo_transcript.json)."
        )
    _write_json(work_dir / "transcript.json", transcript)
    return transcript


def _write_json(path: Path, transcript: Transcript) -> None:
    path.write_text(json.dumps(transcript.to_dict(), indent=2), encoding="utf-8")


def _transcribe_faster_whisper(media_path: Path, model: str) -> Transcript | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        return None

    engine = WhisperModel(model, device="cpu", compute_type="int8")
    segments_iter, info = engine.transcribe(
        str(media_path),
        beam_size=1,
        vad_filter=True,
        word_timestamps=False,
    )
    segments = [
        Segment(start=float(seg.start), end=float(seg.end), text=seg.text.strip())
        for seg in segments_iter
        if seg.text and seg.text.strip()
    ]
    language = getattr(info, "language", None) or "en"
    return Transcript(
        language=language,
        segments=segments,
        source=str(media_path),
        engine=f"faster-whisper:{model}",
    )


def _transcribe_whisper_cli(media_path: Path, work_dir: Path, model: str) -> Transcript | None:
    binary = whisper_cli()
    if not binary:
        return None
    out_dir = work_dir / "whisper"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        binary,
        str(media_path),
        "--model",
        model,
        "--output_format",
        "json",
        "--output_dir",
        str(out_dir),
        "--fp16",
        "False",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise TranscriptError(f"whisper CLI failed:\n{detail[-800:]}") from exc

    json_files = list(out_dir.glob("*.json"))
    if not json_files:
        raise TranscriptError("whisper CLI ran but produced no JSON transcript.")
    data = json.loads(json_files[0].read_text(encoding="utf-8"))
    segments = [
        Segment(
            start=float(item["start"]),
            end=float(item["end"]),
            text=str(item.get("text") or "").strip(),
        )
        for item in data.get("segments") or []
        if item.get("text")
    ]
    return Transcript(
        language=str(data.get("language") or "en"),
        segments=segments,
        source=str(media_path),
        engine=f"whisper-cli:{model}",
    )


def has_whisper() -> bool:
    if whisper_cli():
        return True
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def whisper_status() -> str:
    try:
        import faster_whisper  # noqa: F401

        fw = "installed"
    except ImportError:
        fw = "missing"
    cli = whisper_cli() or "missing"
    return f"faster-whisper={fw} whisper-cli={cli}"
