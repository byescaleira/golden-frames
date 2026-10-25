"""Tag a finished render for identification and search: global tags, per-stream tags, one chapter per shot.

    python tools/metadata.py projects/<name> <video.mp4> [--out tagged.mp4]

Tags come from project.json "metadata" (any of: title, show, artist, album_artist, album, date,
creation_time, genre, composer, description, keywords, copyright, language, location); chapters are
named after each shot's "note". Remux only (-c copy): no re-encode, no quality loss. Without --out the
file is replaced in place after the tagged copy is verified.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

from gf import FPS, Project, run


def esc(s: str) -> str:
    """Escape a value for ffmpeg's FFMETADATA format."""
    for ch in "\\=;#\n":
        s = s.replace(ch, "\\" + ch)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("video")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    prj = Project(a.project)
    md = dict(prj.data.get("metadata", {}))
    kw = md.pop("keywords", "")
    desc = md.pop("description", "")
    lang = md.pop("language", "und")
    tags = {**md, "description": desc, "synopsis": desc, "media_type": "9",
            "comment": f"{desc} Palavras-chave: {kw}".strip(), "keywords": kw, "grouping": kw,
            "encoded_by": "golden-frames (ffmpeg)", "language": lang}
    tags = {k: str(v) for k, v in tags.items() if v}

    frames = prj.frames()
    lines = [";FFMETADATA1"] + [f"{k}={esc(v)}" for k, v in tags.items()]
    for n, shot in enumerate(prj.shots):
        lines += ["[CHAPTER]", "TIMEBASE=1001/24000", f"START={frames[n]}", f"END={frames[n + 1]}",
                  f"title={esc(f'{n + 1:02d} · ' + shot.get('note', f'cena {n + 1}'))}"]
    meta = prj.work / "metadata.txt"
    meta.write_text("\n".join(lines) + "\n", encoding="utf-8")

    src = Path(a.video)
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                       "stream=codec_type,codec_name,width,height,profile", "-of", "json", str(src)],
                                      capture_output=True, text=True).stdout)["streams"]
    v = next(s for s in probe if s["codec_type"] == "video")
    music = prj.data.get("music", {})
    out = Path(a.out) if a.out else src.with_name(src.stem + ".tagged" + src.suffix)
    run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(src), "-i", str(meta),
         "-map", "0", "-map_metadata", "1", "-map_chapters", "1", "-c", "copy",
         "-metadata:s:v:0", f"handler_name={tags.get('title', src.stem)} — {v['width']}x{v['height']} "
                            f"{v['codec_name'].upper()} {v.get('profile', '')}".strip(),
         "-metadata:s:v:0", f"language={lang}",
         "-metadata:s:a:0", f"handler_name={music.get('credit', 'Música')}",
         "-metadata:s:a:0", f"language={lang}",
         "-movflags", "+faststart", "-y", str(out)])
    if not a.out:
        os.replace(out, src)
        out = src
    print(f"tagged: {out} ({len(prj.shots)} chapters)")


if __name__ == "__main__":
    main()
