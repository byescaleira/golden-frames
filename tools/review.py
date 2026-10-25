"""Check a render: frame count vs. the edit, loudness, and one frame from the middle of every shot.

    python tools/review.py projects/<name> <video.mp4> [--titles]

Writes work/review.jpg (5 per row). --titles adds the moments where the cards are fully visible.
"""
import argparse
import re
import subprocess

from PIL import Image

from gf import FPS, Project, grab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("video")
    ap.add_argument("--titles", action="store_true")
    a = ap.parse_args()
    prj = Project(a.project)
    frames = prj.frames()
    expected = frames[-1]
    got = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_frames", "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.strip()
    loud = subprocess.run(["ffmpeg", "-nostdin", "-i", a.video, "-af", "loudnorm=print_format=summary", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    li = re.search(r"Input Integrated:\s*(-?[\d.]+)", loud)
    tp = re.search(r"Input True Peak:\s*([-+]?[\d.]+)", loud)
    ok = got == str(expected)
    print(f"frames {got} / expected {expected} {'OK' if ok else 'MISMATCH'}")
    print(f"loudness {li.group(1) if li else '?'} LUFS, true peak {tp.group(1) if tp else '?'} dBTP")

    times = [(frames[n] + frames[n + 1]) / 2 / FPS for n in range(len(frames) - 1)]
    if a.titles:
        ty = prj.style["typography"]
        total = frames[-1] / FPS
        times += [ty["open"]["start"] + 1.2, total - ty["close"]["lead"] + 1.5]
    S, cols = 300, 5
    sheet = Image.new("RGB", (S * cols, S * ((len(times) + cols - 1) // cols)))
    for i, t in enumerate(times):
        sheet.paste(grab(a.video, t, f"scale={S}:{S}"), (i % cols * S, i // cols * S))
    sheet.save(prj.work / "review.jpg", quality=85)
    print(prj.work / "review.jpg")


if __name__ == "__main__":
    main()
