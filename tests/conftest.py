from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from alphaclip.models import Segment  # noqa: E402
from alphaclip.presets import get_preset  # noqa: E402
from alphaclip.transcript import load_mock_transcript  # noqa: E402


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def demo_transcript_path(repo_root: Path) -> Path:
    return repo_root / "fixtures" / "demo_transcript.json"


@pytest.fixture
def demo_segments(demo_transcript_path: Path) -> list[Segment]:
    return load_mock_transcript(demo_transcript_path).segments


@pytest.fixture
def trench():
    return get_preset("trench-recap")


@pytest.fixture
def protocol():
    return get_preset("protocol-explainer")


@pytest.fixture
def security():
    return get_preset("wallet-security-tip")
