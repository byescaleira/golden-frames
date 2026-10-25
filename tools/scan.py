"""Inventory a footage folder: probe every clip, grab 3 frames each, build contact sheets.

    python tools/scan.py projects/<name> [--workers 6]

Writes work/clips.json, work/thumbs/ and work/sheets/sheet_NNN.jpg (8 clips per sheet: index, date,
duration, fps, then frames at 20/50/80%). Review the sheets to pick shots.
"""
import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

from gf import Project

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv"}
FRACS = (0.2, 0.5, 0.8)


def probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,color_transfer,pix_fmt:format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    return {"file": p.name, "dur": float(j.get("format", {}).get("duration", 0) or 0),
            "w": s.get("width"), "h": s.get("height"), "fps": s.get("r_frame_rate"),
            "trc": s.get("color_transfer"), "pix": s.get("pix_fmt")}


def thumbs(p: Path, info: dict, out: Path):
    for k, frac in enumerate(FRACS):
        dst = out / f"{p.stem}_{k}.jpg"
        if not dst.exists() and info["dur"]:
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{info['dur'] * frac:.2f}", "-i", str(p),
                            "-map", "0:v:0", "-frames:v", "1", "-vf", "scale=320:-2", "-q:v", "5", "-y", str(dst)],
                           capture_output=True)


def sheets(clips: list, thumbs_dir: Path, out: Path, rows=8, tw=320, th=180, lbl=210):
    out.mkdir(exist_ok=True)
    for page in range(0, len(clips), rows):
        sheet = Image.new("RGB", (lbl + 3 * tw, rows * th), "black")
        d = ImageDraw.Draw(sheet)
        for r, c in enumerate(clips[page:page + rows]):
            stem = Path(c["file"]).stem
            d.text((6, r * th + 8), f"#{page + r}", fill="yellow")
            d.text((6, r * th + 28), stem[:28], fill="white")
            d.text((6, r * th + 48), f"{c['dur']:.0f}s {c['fps']}", fill="white")
            for k in range(3):
                p = thumbs_dir / f"{stem}_{k}.jpg"
                if p.exists():
                    im = Image.open(p)
                    im.thumbnail((tw, th))
                    sheet.paste(im, (lbl + k * tw, r * th))
        sheet.save(out / f"sheet_{page // rows:03d}.jpg", quality=80)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    prj = Project(a.project)
    tdir = prj.work / "thumbs"
    tdir.mkdir(exist_ok=True)
    files = sorted(p for p in prj.source.iterdir() if p.suffix.lower() in VIDEO_EXT)

    def work(p):
        info = probe(p)
        thumbs(p, info, tdir)
        return info

    with ThreadPoolExecutor(a.workers) as ex:
        clips = list(ex.map(work, files))
    (prj.work / "clips.json").write_text(json.dumps(clips, indent=1))
    sheets(clips, tdir, prj.work / "sheets")
    print(f"{len(clips)} clips, {sum(c['dur'] for c in clips) / 60:.0f} min -> {prj.work / 'sheets'}")


if __name__ == "__main__":
    main()
