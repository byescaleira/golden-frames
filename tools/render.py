"""Render the edit: one graded segment per shot, then concat + music + title cards.

    python tools/render.py projects/<name> [--size 1080|2160] [--out file.mp4]

1080 -> H.264 8-bit (social delivery). 2160 -> HEVC 10-bit "hvc1" master (no banding in skies).
Needs work/clips.json (scan.py) and work/grade.json (grade.py); title cards are rebuilt for the size.
"""
import argparse
import json

from gf import FPS, Project, geometry, run
from grade import look
from titles import build as build_titles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    prj = Project(a.project)
    style, size = prj.style, a.size
    uhd = size > 1080
    pix = "yuv420p10le" if uhd else "yuv420p"
    seg_codec = (["-c:v", "libx265", "-preset", "fast", "-crf", "12", "-x265-params", "log-level=error"] if uhd
                 else ["-c:v", "libx264", "-preset", "medium", "-crf", "12"])
    final_codec = (["-c:v", "libx265", "-preset", "medium", "-crf", "16", "-tag:v", "hvc1", "-x265-params", "log-level=error"]
                   if uhd else ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "20M", "-bufsize", "40M",
                                "-profile:v", "high"])
    per_shot = json.loads((prj.work / "grade.json").read_text())["per_shot"]
    lk = look(style, size)
    frames = prj.frames()
    seg_dir = prj.work / f"segs_{size}"
    seg_dir.mkdir(exist_ok=True)
    push = style["rhythm"]["intro_push"]

    listing = []
    for n, shot in enumerate(prj.shots):
        c = prj.clip(shot["file"])
        nf = frames[n + 1] - frames[n]
        dur = nf / FPS
        g = geometry(shot, c, dur)
        vf = [f"crop={g['side']}:{g['side']}:{g['x']}:{g['y']}"]
        if g["stretch"] != 1.0:
            vf.insert(0, f"setpts={g['stretch']:.4f}*PTS")
        if shot.get("push"):
            z = f"{size}*(1+{push}*t/{dur:.3f})"
            vf += [f"scale=w='{z}':h='{z}':eval=frame:flags=lanczos", f"crop={size}:{size}"]
        else:
            vf += [f"scale={size}:{size}:flags=lanczos"]
        vf += [f"fps={FPS}", per_shot[n], lk, f"format={pix}"]
        dst = seg_dir / f"{n:02d}.mp4"
        run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{g['start']:.3f}", "-i", str(prj.source / c["file"]),
             "-map", "0:v:0", "-an", "-vf", ",".join(vf), "-frames:v", str(nf), *seg_codec, "-y", str(dst)])
        listing.append(f"file '{dst.as_posix()}'")
        print(f"{n:02d} {prj.cuts[n]:6.2f}s +{dur:4.2f}s {shot.get('note', '')}", flush=True)
    (seg_dir / "list.txt").write_text("\n".join(listing) + "\n")

    total = frames[-1] / FPS
    m = prj.data["music"]
    m0 = m.get("start", 0.0)
    au, vi, ty = style["audio"], style["video"], style["typography"]
    cards = build_titles(prj, size)
    o0, o1 = ty["open"]["start"], ty["open"]["end"]
    e0, e1 = total - ty["close"]["lead"], total - ty["close"]["tail"]
    drift = ty["drift_px"] * size // 1080
    graph = (
        f"[2:v]format=rgba,fade=t=in:st={o0}:d=1.0:alpha=1,fade=t=out:st={o1 - 0.9}:d=0.9:alpha=1[t1];"
        f"[3:v]format=rgba,fade=t=in:st={e0:.3f}:d=1.0:alpha=1,fade=t=out:st={e1 - 0.6:.3f}:d=0.6:alpha=1[t2];"
        f"[0:v]fade=t=in:st=0:d={vi['fade_in']}[v0];"
        f"[v0][t1]overlay=x=0:y='{drift}-{drift}*clip((t-{o0})/{o1 - o0},0,1)':eval=frame[v1];"
        f"[v1][t2]overlay=x=0:y='{drift}-{drift}*clip((t-{e0:.3f})/{e1 - e0:.3f},0,1)':eval=frame,"
        f"fade=t=out:st={total - vi['fade_out']:.3f}:d={vi['fade_out']}[vout];"
        f"[1:a]atrim={m0}:{m0 + total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={au['fade_in']},"
        f"afade=t=out:st={total - au['fade_out']:.3f}:d={au['fade_out']}[aout]"
    )
    out = a.out or str(prj.dir / f"{prj.dir.name}_{size}.mp4")
    run(["ffmpeg", "-nostdin", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(seg_dir / "list.txt"),
         "-i", m["file"],
         "-loop", "1", "-t", f"{total:.3f}", "-i", str(cards["open"]),
         "-loop", "1", "-t", f"{total:.3f}", "-i", str(cards["close"]),
         "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]", *final_codec, "-pix_fmt", pix,
         "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-y", out])
    print(f"done: {out} ({total:.2f}s, {frames[-1]} frames)")


if __name__ == "__main__":
    main()
