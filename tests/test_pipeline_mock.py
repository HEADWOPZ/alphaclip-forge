from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from alphaclip.config import VERTICAL_HEIGHT, VERTICAL_WIDTH
from alphaclip.media import video_size
from alphaclip.pipeline import forge


@pytest.fixture
def demo_mp4(repo_root: Path) -> Path:
    path = repo_root / "fixtures" / "demo.mp4"
    if not path.is_file():
        pytest.skip("fixtures/demo.mp4 missing — run python scripts/make_fixture.py")
    return path


def test_mock_forge_exports_vertical_zip(demo_mp4: Path, demo_transcript_path: Path, tmp_path: Path):
    result = forge(
        source=str(demo_mp4),
        preset_id="trench-recap",
        mock_transcript=demo_transcript_path,
        out_dir=tmp_path / "job",
        max_clips=2,
        job_id="testfixture",
    )
    assert result.clips
    clip = Path(result.clips[0].path)
    assert clip.is_file()
    width, height = video_size(clip)
    assert (width, height) == (VERTICAL_WIDTH, VERTICAL_HEIGHT)
    assert result.clips[0].duration >= 8

    meta = json.loads(Path(result.metadata_path).read_text(encoding="utf-8"))
    assert meta["clip_count"] >= 1
    assert meta["mock"] is True
    assert "not financial advice" in meta["preset"]["disclaimer"].lower()
    assert meta["clips"][0]["titles"]

    zpath = Path(result.zip_path)
    assert zpath.is_file()
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        assert "metadata.json" in names
        assert any(n.startswith("clips/") and n.endswith(".mp4") for n in names)


def test_protocol_preset_mock(demo_mp4: Path, demo_transcript_path: Path, tmp_path: Path):
    result = forge(
        source=str(demo_mp4),
        preset_id="protocol-explainer",
        mock_transcript=demo_transcript_path,
        out_dir=tmp_path / "proto",
        max_clips=1,
    )
    blob = result.clips[0].text.lower()
    assert "protocol" in blob or "vault" in blob or "oracle" in blob or "tvl" in blob
