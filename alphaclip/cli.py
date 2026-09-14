from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import click

from alphaclip import __version__
from alphaclip.config import (
    FIXTURES_DIR,
    WHISPER_MODELS,
    default_whisper_model,
    ffmpeg_bin,
    ffprobe_bin,
    resolve_font,
    work_root,
    ytdlp_bin,
)
from alphaclip.hooks import generate_hook_variants, generate_titles
from alphaclip.pipeline import default_mock_transcript, forge
from alphaclip.presets import get_preset, list_presets
from alphaclip.schedule import PROVIDERS, has_credentials, schedule
from alphaclip.transcript import has_whisper, whisper_status


class ForgeGroup(click.Group):
    def get_command(self, ctx: click.Context, cmd_name: str):
        if cmd_name == "ui":
            return click.Group.get_command(self, ctx, "serve")
        return super().get_command(ctx, cmd_name)


@click.group(cls=ForgeGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="alphaclip")
def main() -> None:
    """AlphaClip Forge — crypto Shorts/TikTok clip factory."""


@main.command("forge")
@click.argument("source", required=False)
@click.option(
    "--preset",
    "preset_id",
    default="trench-recap",
    show_default=True,
    type=click.Choice([p.id for p in list_presets()], case_sensitive=False),
    help="Niche overlay / scoring preset.",
)
@click.option("--url", "url_source", default=None, help="Remote YouTube / X / Loom URL (alt to SOURCE).")
@click.option(
    "--mock-transcript",
    "mock_transcript",
    is_flag=False,
    flag_value=str(default_mock_transcript()),
    default=None,
    help="Skip Whisper. Optionally pass a transcript JSON path (flag uses the demo fixture).",
)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None, help="Job output directory.")
@click.option("--max-clips", type=int, default=None, help="Cap exported highlights.")
@click.option(
    "--whisper-model",
    default=None,
    help=f"Whisper model size when not mocking (default: {default_whisper_model()}).",
)
@click.option("--json", "as_json", is_flag=True, help="Print machine-readable job result.")
def forge_cmd(
    source: str | None,
    preset_id: str,
    url_source: str | None,
    mock_transcript: str | None,
    out_dir: Path | None,
    max_clips: int | None,
    whisper_model: str | None,
    as_json: bool,
) -> None:
    """Ingest SOURCE (path or URL), cut captioned 9:16 clips, zip them."""
    resolved = url_source or source
    if not resolved:
        raise click.UsageError("Provide a local video path, a URL argument, or --url.")
    mock: Path | bool | None = None
    if mock_transcript:
        mock = Path(mock_transcript)
    try:
        result = forge(
            source=resolved,
            preset_id=preset_id,
            mock_transcript=mock,
            out_dir=out_dir,
            max_clips=max_clips,
            whisper_model=whisper_model,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        click.echo(
            json.dumps(
                {
                    "job_id": result.job_id,
                    "preset": result.preset_id,
                    "zip": result.zip_path,
                    "metadata": result.metadata_path,
                    "clips": [
                        {
                            "filename": c.filename,
                            "title": c.title,
                            "duration": c.duration,
                            "score": c.score,
                        }
                        for c in result.clips
                    ],
                },
                indent=2,
            )
        )
        return

    click.echo(f"Forged {len(result.clips)} clip(s) · preset={result.preset_id} · job={result.job_id}")
    for clip in result.clips:
        click.echo(f"  {clip.filename}  {clip.duration:.1f}s  score={clip.score:.2f}  {clip.title}")
    click.echo(f"Zip: {result.zip_path}")
    click.echo(f"Metadata: {result.metadata_path}")


@main.command("presets")
def presets_cmd() -> None:
    """List niche presets."""
    for preset in list_presets():
        click.echo(f"{preset.id:24} {preset.name}")
        click.echo(f"  {preset.description}")
        click.echo(f"  CTA: {preset.cta}")
        click.echo("")


@main.command("hooks")
@click.option("--preset", "preset_id", default="trench-recap", show_default=True)
@click.option("--text", required=True, help="Transcript excerpt or topic sentence.")
@click.option("--count", default=6, show_default=True)
def hooks_cmd(preset_id: str, text: str, count: int) -> None:
    """Print title / hook variants for a preset (no LLM required)."""
    try:
        preset = get_preset(preset_id)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("Hooks:")
    for item in generate_hook_variants(text, preset, count=count):
        click.echo(f"  • {item}")
    click.echo("Titles:")
    for item in generate_titles(text, preset, count=count):
        click.echo(f"  • {item}")
    click.echo(f"\nDisclaimer:\n{preset.disclaimer}")


@main.command("schedule")
@click.option(
    "--metadata",
    type=click.Path(path_type=Path, exists=True),
    required=True,
    help="Path to a job metadata.json.",
)
@click.option("--provider", type=click.Choice(PROVIDERS), default="buffer", show_default=True)
@click.option("--cadence-hours", type=float, default=8.0, show_default=True)
@click.option(
    "--live",
    is_flag=True,
    help="Actually POST (requires provider env keys). Default is dry-run.",
)
def schedule_cmd(metadata: Path, provider: str, cadence_hours: float, live: bool) -> None:
    """Plan (and optionally submit) Buffer / Late posts from a job zip's metadata."""
    try:
        result = schedule(
            metadata_path=metadata,
            provider=provider,
            dry_run=not live,
            cadence_hours=cadence_hours,
        )
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(result, indent=2))
    if result.get("dry_run"):
        ready = has_credentials(provider)
        if not ready:
            click.echo(
                f"\nDry-run: no {provider} credentials. "
                "Set BUFFER_ACCESS_TOKEN + BUFFER_PROFILE_ID or LATE_API_KEY + LATE_ACCOUNT_ID.",
                err=True,
            )


@main.command("serve")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=8080, show_default=True, type=int)
@click.option("--reload", is_flag=True, help="Dev auto-reload.")
def serve_cmd(host: str, port: int, reload: bool) -> None:
    """Run the dark web UI (paste URL, pick preset, download zip)."""
    import uvicorn

    uvicorn.run("alphaclip.web.app:app", host=host, port=port, reload=reload)


@main.command("doctor")
def doctor_cmd() -> None:
    """Check ffmpeg, yt-dlp, whisper, fonts, and the demo fixture."""
    rows: list[tuple[str, str]] = []

    def check(label: str, ok: bool, detail: str) -> None:
        rows.append((label, f"{'ok' if ok else 'missing'}  {detail}"))

    try:
        check("ffmpeg", True, ffmpeg_bin())
    except Exception as exc:
        check("ffmpeg", False, str(exc))
    try:
        check("ffprobe", True, ffprobe_bin())
    except Exception as exc:
        check("ffprobe", False, str(exc))

    ytdlp = ytdlp_bin()
    check("yt-dlp", bool(ytdlp), ytdlp or "install via pip (needed only for remote URLs)")
    check("whisper", has_whisper(), whisper_status())
    try:
        check("caption-font", True, str(resolve_font()))
    except Exception as exc:
        check("caption-font", False, str(exc))

    fixture = FIXTURES_DIR / "demo.mp4"
    transcript = default_mock_transcript()
    check("demo.mp4", fixture.is_file(), str(fixture))
    check("demo_transcript.json", transcript.is_file(), str(transcript))
    check("work-root", True, str(work_root()))

    click.echo(f"AlphaClip Forge {__version__}")
    click.echo(f"Python {sys.version.split()[0]}  ({shutil.which('python3')})")
    for label, detail in rows:
        click.echo(f"  {label:20} {detail}")
    click.echo("\nWhisper model sizes (optional, no GPU required):")
    for name, blurb in WHISPER_MODELS.items():
        mark = "*" if name == default_whisper_model() else " "
        click.echo(f"  {mark} {name:10} {blurb}")


@main.command("demo")
@click.option("--preset", "preset_id", default="trench-recap", show_default=True)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
def demo_cmd(preset_id: str, out_dir: Path | None) -> None:
    """Forge the bundled fixture in mock-transcript mode (no network, no GPU)."""
    fixture = FIXTURES_DIR / "demo.mp4"
    if not fixture.is_file():
        raise click.ClickException(
            f"Missing {fixture}. Run: python scripts/make_fixture.py"
        )
    result = forge(
        source=str(fixture),
        preset_id=preset_id,
        mock_transcript=True,
        out_dir=out_dir,
    )
    click.echo(f"Demo zip → {result.zip_path}")
    click.echo(f"{len(result.clips)} captioned 9:16 clip(s).")
