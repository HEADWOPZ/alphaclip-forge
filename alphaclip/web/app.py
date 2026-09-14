from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from alphaclip import __version__
from alphaclip.config import FIXTURES_DIR, work_root
from alphaclip.pipeline import forge
from alphaclip.presets import list_presets

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES = Environment(
    loader=FileSystemLoader(str(WEB_DIR / "templates")),
    autoescape=select_autoescape(["html"]),
)

app = FastAPI(title="AlphaClip Forge", version=__version__, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    template = TEMPLATES.get_template("index.html")
    return template.render(presets=list_presets(), version=__version__)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "name": "alphaclip-forge", "version": __version__}


@app.get("/api/presets")
def api_presets() -> list[dict]:
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "cta": p.cta,
            "disclaimer": p.disclaimer,
        }
        for p in list_presets()
    ]


@app.post("/api/forge")
async def api_forge(
    preset: str = Form("trench-recap"),
    url: str = Form(""),
    mock: str = Form("true"),
    rights: str = Form(""),
    upload: UploadFile | None = File(None),
) -> dict:
    if rights.lower() not in {"1", "true", "on", "yes"}:
        raise HTTPException(
            400,
            "Confirm you own or have a license to the source media before forging.",
        )
    use_mock = mock.lower() in {"1", "true", "on", "yes"}
    job_id = uuid.uuid4().hex[:12]
    dest = work_root() / "jobs" / job_id
    dest.mkdir(parents=True, exist_ok=True)

    source: str | None = None
    if upload is not None and upload.filename:
        suffix = Path(upload.filename).suffix or ".mp4"
        stored = dest / f"upload{suffix}"
        with stored.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        source = str(stored)
    elif url.strip():
        source = url.strip()
    elif use_mock:
        fixture = FIXTURES_DIR / "demo.mp4"
        if not fixture.is_file():
            raise HTTPException(500, "Demo fixture missing. Run python scripts/make_fixture.py")
        source = str(fixture)
    else:
        raise HTTPException(400, "Paste a URL, upload a file, or enable mock demo mode.")

    try:
        result = forge(
            source=source,
            preset_id=preset,
            mock_transcript=True if use_mock else None,
            out_dir=dest,
            job_id=job_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

    return {
        "job_id": result.job_id,
        "preset": result.preset_id,
        "zip": f"/api/jobs/{result.job_id}/download",
        "clip_count": len(result.clips),
        "clips": [
            {
                "filename": c.filename,
                "title": c.title,
                "hook": c.hook,
                "duration": c.duration,
                "score": c.score,
            }
            for c in result.clips
        ],
        "disclaimer": result.clips[0].disclaimer if result.clips else "",
    }


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str) -> FileResponse:
    dest = work_root() / "jobs" / job_id
    if not dest.is_dir():
        raise HTTPException(404, "Unknown job.")
    zips = sorted(dest.glob("alphaclip-*.zip"))
    if not zips:
        raise HTTPException(404, "Zip not ready.")
    return FileResponse(
        zips[-1],
        media_type="application/zip",
        filename=zips[-1].name,
    )
