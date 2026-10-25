"""Per-shot colour normalisation + the style's shared look.

    python tools/grade.py projects/<name> [--preview]

1. Measures every shot on its raw square crop (3 frames): luma p1/p50/p99, saturation, midtone colour.
   Flat log footage shows up as a high p1, a narrow range and low saturation.
2. Builds a per-shot correction (levels, midtone power, partial grey-world white balance, saturation)
   so log and normal clips land on the same base. A shot's "exp" (< 1 brightens) nudges a face that
   ends up dark against the sky or at night.
3. Appends the style's look (curve, split-tone, hue moves, halation, vignette, grain).
Writes work/shotstats.json and work/grade.json; --preview writes work/grade_preview.jpg (raw | graded).
"""
import argparse
import json
import math

import numpy as np
from PIL import Image

from gf import FPS, Project, geometry, grab

LUMA = (0.2126, 0.7152, 0.0722)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def measure(prj, n, shot, dur):
    c = prj.clip(shot["file"])
    g = geometry(shot, c, dur)
    crop = f"crop={g['side']}:{g['side']}:{g['x']}:{g['y']},scale=256:256"
    px = [np.asarray(grab(prj.source / c["file"], min(g["start"] + dur * k / g["stretch"], c["dur"] - 0.1), crop),
                     dtype=np.float32) / 255 for k in (0.2, 0.5, 0.8)]
    a = np.concatenate([p.reshape(-1, 3) for p in px])
    luma = a @ np.array(LUMA)
    mx, mn = a.max(1), a.min(1)
    sat = np.where(mx > 0.02, (mx - mn) / np.maximum(mx, 1e-3), 0)
    mid = (luma > 0.2) & (luma < 0.8)
    return {"n": n, "file": shot["file"], "p1": float(np.percentile(luma, 1)), "p50": float(np.percentile(luma, 50)),
            "p99": float(np.percentile(luma, 99)), "sat": float(sat.mean()),
            "rgb_mid": (a[mid].mean(0) if mid.any() else a.mean(0)).tolist()}


def normalise(s, shot, cfg):
    night = s["p50"] < cfg["night_median"]
    black = clamp(s["p1"] * cfg["black_factor"], 0.0, cfg["black_max"])
    white = clamp(s["p99"] * cfg["white_factor"], cfg["white_min"], 1.0)
    norm_mid = clamp((s["p50"] - black) / (white - black), 0.05, 0.95)
    target = cfg["mid_target_night"] if night else cfg["mid_target_day"]
    gamma = clamp(math.log(target) / math.log(norm_mid), *cfg["gamma_range"]) * shot.get("exp", 1.0)
    r, g, b = s["rgb_mid"]
    m = (r + g + b) / 3
    k = cfg["wb_strength_night"] if night else cfg["wb_strength_day"]
    gains = [(m / max(c, 1e-3)) ** k for c in (r, g, b)]
    norm = sum(w * gn for w, gn in zip(LUMA, gains))
    gains = [clamp(gn / norm, 0.75, 1.35) for gn in gains]
    sat = clamp((cfg["sat_target_night"] if night else cfg["sat_target_day"]) / max(s["sat"], 0.05), *cfg["sat_range"])
    # levels + midtone power + white-balance gain in one per-channel LUT
    lut = [f"{ch}='maxval*clip({gn:.3f}*pow(clip((val/maxval-{black:.3f})/{white - black:.3f},0,1),{gamma:.3f}),0,1)'"
           for ch, gn in zip("rgb", gains)]
    info = f"black={black:.3f} white={white:.3f} gamma={gamma:.2f} sat={sat:.2f} wb={[round(x, 2) for x in gains]}"
    return f"format=gbrp16le,lutrgb={':'.join(lut)},eq=saturation={sat:.3f}", info + (" night" if night else "")


def look(style, size=1080):
    """The shared look; halation blur scales with output size."""
    h = style["halation"]
    sigma = h["sigma_at_1080"] * size // 1080
    tr, tg, tb = h["tint"]
    halo = (f"format=gbrp,split[base][glow];"
            f"[glow]curves=master='0/0 {h['threshold']}/0 1/0.85',gblur=sigma={sigma},"
            f"colorchannelmixer=rr={tr}:gg={tg}:bb={tb}[halo];"
            f"[base][halo]blend=all_mode=screen:all_opacity={h['opacity']}")
    return ",".join(style["look"] + [halo] + style["finish"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    prj = Project(a.project)
    style = prj.style
    frames = prj.frames()
    stats, per_shot = [], []
    for n, shot in enumerate(prj.shots):
        dur = (frames[n + 1] - frames[n]) / FPS
        s = measure(prj, n, shot, dur)
        f, info = normalise(s, shot, style["normalize"])
        stats.append(s)
        per_shot.append(f)
        flat = s["p1"] > 0.07 and s["p99"] - s["p1"] < 0.80 and s["sat"] < 0.30
        print(f"{n:02d} {info} {'LOG?' if flat else ''} {shot.get('note', '')}", flush=True)
    (prj.work / "shotstats.json").write_text(json.dumps(stats, indent=1))
    (prj.work / "grade.json").write_text(json.dumps({"per_shot": per_shot}, indent=1))

    if a.preview:
        S, cols = 300, 4
        sheet = Image.new("RGB", (S * 2 * cols, S * ((len(prj.shots) + cols - 1) // cols)))
        lk = look(style, 540)
        for n, shot in enumerate(prj.shots):
            c = prj.clip(shot["file"])
            dur = (frames[n + 1] - frames[n]) / FPS
            g = geometry(shot, c, dur)
            t = min(g["start"] + dur / 2 / g["stretch"], c["dur"] - 0.1)
            base = f"crop={g['side']}:{g['side']}:{g['x']}:{g['y']},scale=540:540"
            for k, vf in enumerate((base, f"{base},{per_shot[n]},{lk}")):
                sheet.paste(grab(prj.source / c["file"], t, vf).resize((S, S)), ((n % cols) * 2 * S + k * S, (n // cols) * S))
        sheet.save(prj.work / "grade_preview.jpg", quality=88)
        print(prj.work / "grade_preview.jpg")


if __name__ == "__main__":
    main()
