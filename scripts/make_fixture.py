#!/usr/bin/env python3
"""Generate fixtures/demo.mp4 — 32s 1280x720 source for mock-mode CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "demo.mp4"

SCENES = [
    (0, 4, "THE AIRDROP YOU SLEPT ON", "trenches / generational bag"),
    (4, 8, "LIQUIDATION CASCADE", "40x whale - three wicks"),
    (8, 12, "DO NOT FADE THIS TAPE", "funding flipped / runner"),
    (12, 16.2, "HOW THE PROTOCOL WORKS", "vault -> AMM"),
    (16.2, 20.4, "ORACLE + RESTAKE", "slash if a validator lies"),
    (20.4, 24.4, "TVL IS IDLE LIQUIDITY", "read the docs first"),
    (24.4, 28.2, "DRAIN TRICK", "unlimited approval"),
    (28.2, 32.0, "REVOKE. HARDWARE.", "never type a seed phrase"),
]

FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
]


def _font() -> Path:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return path
    raise SystemExit("No caption font found for the demo fixture.")


def _draw(start: float, end: float, title: str, sub: str, font: Path) -> str:
    def esc(text: str) -> str:
        return text.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")

    enable = f"between(t,{start},{end})"
    return (
        f"drawtext=fontfile={font}:text='{esc(title)}':fontcolor=0xF4E8C8:"
        f"fontsize=42:x=(w-text_w)/2:y=300:enable='{enable}',"
        f"drawtext=fontfile={font}:text='{esc(sub)}':fontcolor=0xC4B48A:"
        f"fontsize=28:x=(w-text_w)/2:y=364:enable='{enable}'"
    )


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    font = _font()
    vf = ",".join(_draw(a, b, t, s, font) for a, b, t, s in SCENES) + ",format=yuv420p"
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x14120c:s=1280x720:d=32:r=30",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=180:sample_rate=44100:duration=32",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "26",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(OUT),
    ]
    print("generating", OUT, file=sys.stderr)
    subprocess.run(cmd, check=True)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
