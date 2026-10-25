"""Measure a reference video you like and turn it into numbers a style can copy.

    python tools/reference_profile.py <video> [--name my-style] [--out styles/refs/]

Measures:
  * edit rhythm: cuts (ffmpeg scene detection), shot-length median/p10/p90, cuts per minute,
    and how many cuts land within 80 ms of a musical onset (cutting on the music or not)
  * colour: luma p1/p50/p99 (black lift, contrast, highlight roll-off), saturation, shadow and
    highlight tint (split-toning), warmth
  * format: size, aspect, fps, duration
Writes <out>/<name>.profile.json plus <name>.frames.jpg (one frame per detected shot), so text and
typography can be read from the frames. Feed several profiles into a style with your own judgement.
Nothing is uploaded anywhere; the video stays local.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from gf import grab

LUMA = np.array([0.2126, 0.7152, 0.0722])


def scene_cuts(path, thresh):
    r = subprocess.run(["ffmpeg", "-nostdin", "-i", str(path), "-vf", f"scale=320:-2,select='gt(scene,{thresh})',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def probe(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                                  capture_output=True, text=True).stdout)
    s = j["streams"][0]
    return {"w": s["width"], "h": s["height"], "fps": s["r_frame_rate"], "dur": float(j["format"]["duration"])}


def onsets(path):
    try:
        import librosa
    except ImportError:
        return None
    try:
        y, sr = librosa.load(str(path), sr=22050, mono=True)
    except Exception:
        return None
    return librosa.onset.onset_detect(y=y, sr=sr, units="time")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "styles" / "refs"))
    ap.add_argument("--scene", type=float, default=0.30, help="scene-change threshold (lower = more cuts)")
    a = ap.parse_args()
    src = Path(a.video)
    name = a.name or src.stem
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    info = probe(src)
    cuts = [0.0] + scene_cuts(src, a.scene) + [info["dur"]]
    shots = np.diff(cuts)
    mids = [(cuts[i] + cuts[i + 1]) / 2 for i in range(len(cuts) - 1)]

    on = onsets(src)
    on_music = None
    if on is not None and len(on) and len(cuts) > 2:
        inner = np.array(cuts[1:-1])
        on_music = float(np.mean([np.min(np.abs(on - c)) < 0.10 for c in inner]))  # ~2 frames at 24 fps

    px, thumbs = [], []
    for t in mids:
        im = grab(src, t, "scale=256:-2")
        thumbs.append(im)
        px.append(np.asarray(im, dtype=np.float32).reshape(-1, 3) / 255)
    a_ = np.concatenate(px)
    luma = a_ @ LUMA
    mx, mn = a_.max(1), a_.min(1)
    sat = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-3), 0)
    sh, hi = luma < np.percentile(luma, 15), luma > np.percentile(luma, 85)
    tint = lambda m: [round(float(x), 3) for x in a_[m].mean(0) - a_[m].mean()]  # per-channel offset from neutral

    profile = {
        "source": src.name, "format": info, "aspect": round(info["w"] / info["h"], 3),
        "rhythm": {"shots": len(shots), "cuts_per_min": round(60 * (len(shots) - 1) / info["dur"], 1),
                   "shot_median": round(float(np.median(shots)), 2), "shot_p10": round(float(np.percentile(shots, 10)), 2),
                   "shot_p90": round(float(np.percentile(shots, 90)), 2),
                   "cuts_on_music_onsets": None if on_music is None else round(on_music, 2)},
        "color": {"luma_p1": round(float(np.percentile(luma, 1)), 3), "luma_p50": round(float(np.percentile(luma, 50)), 3),
                  "luma_p99": round(float(np.percentile(luma, 99)), 3), "saturation": round(float(sat.mean()), 3),
                  "shadow_tint_rgb": tint(sh), "highlight_tint_rgb": tint(hi),
                  "warmth": round(float(a_[:, 0].mean() - a_[:, 2].mean()), 3)},
        "cuts": [round(c, 2) for c in cuts],
    }
    (out / f"{name}.profile.json").write_text(json.dumps(profile, indent=1))

    S, cols = 256, 6
    th = max(im.height * S // im.width for im in thumbs)
    sheet = Image.new("RGB", (S * cols, th * ((len(thumbs) + cols - 1) // cols)))
    for i, im in enumerate(thumbs):
        sheet.paste(im.resize((S, im.height * S // im.width)), (i % cols * S, i // cols * th))
    sheet.save(out / f"{name}.frames.jpg", quality=85)
    print(json.dumps({k: profile[k] for k in ("rhythm", "color")}, indent=1))
    print(out / f"{name}.profile.json")


if __name__ == "__main__":
    main()
