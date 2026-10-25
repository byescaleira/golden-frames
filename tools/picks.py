"""Grid of candidate frames to compare picks side by side.

    python tools/picks.py projects/<name> 104:1 3:1 165:2 ... [--out work/picks.jpg]

Each item is <scan index>:<frame 0|1|2> (frames at 20/50/80% of the clip).
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw

from gf import Project


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("items", nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    prj = Project(a.project)
    clips = prj.clips()
    items = [tuple(map(int, s.split(":"))) for s in a.items]
    tw, th, cols = 400, 225, 4
    sheet = Image.new("RGB", (cols * tw, ((len(items) + cols - 1) // cols) * th))
    d = ImageDraw.Draw(sheet)
    for n, (i, f) in enumerate(items):
        x, y = n % cols * tw, n // cols * th
        im = Image.open(prj.work / "thumbs" / f"{Path(clips[i]['file']).stem}_{f}.jpg")
        im.thumbnail((tw, th))
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + 70, y + 18], fill="black")
        d.text((x + 3, y + 3), f"#{i}:{f}", fill="yellow")
    out = Path(a.out) if a.out else prj.work / "picks.jpg"
    sheet.save(out, quality=85)
    print(out)


if __name__ == "__main__":
    main()
