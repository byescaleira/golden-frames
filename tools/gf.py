"""Shared helpers for the golden-frames tools: project loading, shot geometry, ffmpeg calls."""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FPS = 24000 / 1001


class Project:
    """A project folder: project.json (the edit decision list) + work/ (generated, git-ignored)."""

    def __init__(self, path: str | Path):
        self.dir = Path(path).resolve()
        self.file = self.dir / "project.json"
        self.data = json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}
        self.work = self.dir / "work"
        self.work.mkdir(exist_ok=True)

    # --- config -------------------------------------------------------------------------
    @property
    def source(self) -> Path:
        return Path(self.data["source"])

    @property
    def style(self) -> dict:
        name = self.data.get("style", "golden-frames")
        return json.loads((ROOT / "styles" / f"{name}.json").read_text(encoding="utf-8"))

    @property
    def shots(self) -> list[dict]:
        return self.data.get("shots", [])

    @property
    def cuts(self) -> list[float]:
        return self.data.get("cuts", [])

    def save(self):
        self.file.write_text(json.dumps(self.data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # --- clips --------------------------------------------------------------------------
    def clips(self) -> list[dict]:
        return json.loads((self.work / "clips.json").read_text())

    def clip(self, ref) -> dict:
        """A shot refers to its clip by file name (stable) or by scan index (handy while picking)."""
        clips = self.clips()
        if isinstance(ref, int):
            return clips[ref]
        for c in clips:
            if c["file"] == ref:
                return c
        raise KeyError(ref)

    # --- timeline -----------------------------------------------------------------------
    def frames(self) -> list[int]:
        """Cut points snapped to whole frames so the edit never drifts from the music."""
        f = [round(t * FPS) for t in self.cuts]
        assert len(f) - 1 == len(self.shots), f"{len(f) - 1} slots for {len(self.shots)} shots"
        return f


def geometry(shot: dict, clip: dict, dur: float) -> dict:
    """Where in the clip a shot starts, its square crop and any slow-motion stretch."""
    start = max(0.0, min(clip["dur"] * shot["at"] - dur / 2, clip["dur"] - dur - 0.05))
    side = int(clip["h"] / shot.get("zoom", 1.0)) // 2 * 2
    x = int(min(max(shot.get("cx", 0.5) * clip["w"] - side / 2, 0), clip["w"] - side))
    y = int(min(max(shot.get("cy", 0.5) * clip["h"] - side / 2, 0), clip["h"] - side))
    stretch = 1.0
    avail = clip["dur"] - 0.1
    if avail < dur:  # clip shorter than its slot: gentle slow motion instead of running out
        start, stretch = 0.0, dur / avail * 1.03
    return {"start": start, "side": side, "x": x, "y": y, "stretch": stretch}


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode(errors="replace")[-3000:])
    return r


def grab(path: Path, t: float, vf: str):
    """One frame as a PIL image."""
    from PIL import Image
    r = run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1",
             "-vf", vf, "-f", "image2pipe", "-vcodec", "png", "-"])
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")
