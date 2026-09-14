from __future__ import annotations

from pathlib import Path

import pytest

from alphaclip.ingest import IngestError, classify_source, ingest_source


def test_classify_local(tmp_path: Path):
    video = tmp_path / "talk.mp4"
    video.write_bytes(b"not-really-video")
    assert classify_source(str(video)) == "local"


def test_classify_urls():
    assert classify_source("https://www.youtube.com/watch?v=dQw4w9wgGcQ") == "youtube"
    assert classify_source("https://youtu.be/dQw4w9wgGcQ") == "youtube"
    assert classify_source("https://x.com/user/status/1") == "x"
    assert classify_source("https://twitter.com/user/status/1") == "x"
    assert classify_source("https://www.loom.com/share/abc") == "loom"
    assert classify_source("https://example.com/v.mp4") == "url"


def test_missing_local_video():
    with pytest.raises(IngestError):
        classify_source("/tmp/definitely-missing-alphaclip.mp4")


def test_copy_local(tmp_path: Path):
    src = tmp_path / "src.mp4"
    src.write_bytes(b"abc")
    dest = ingest_source(str(src), tmp_path / "ingest")
    assert dest.is_file()
    assert dest.read_bytes() == b"abc"
