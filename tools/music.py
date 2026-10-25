"""Map the song and propose cut points on musical phrases.

    python tools/music.py projects/<name> [--write]

Reads music.file / music.start / music.end from project.json. Prints tempo, per-second energy (to spot
the calm vs. intense parts) and a suggested cut list: each cut lands on an onset, preferring the ones
after the longest pause (phrase starts), within the style's shot-length ranges. --write stores the
suggestion as project.json "cuts" (it does not touch "shots").
"""
import argparse
import json

import librosa
import numpy as np

from gf import Project


def suggest_cuts(onsets, gaps, strength, t_end, intro_end, intro_rng, body_rng):
    cuts, t = [0.0], 0.0
    while True:
        lo, hi = intro_rng if t < intro_end else body_rng
        if t_end - t <= hi:  # the last shot runs to the end
            break
        cand = [i for i, o in enumerate(onsets) if t + lo <= o <= t + hi and t_end - o >= lo]
        if not cand:
            t = min(t + (lo + hi) / 2, t_end)
            cuts.append(round(t, 2))
            continue
        best = max(cand, key=lambda i: (gaps[i], strength[i]))  # phrase start = onset after the longest pause
        t = float(onsets[best])
        cuts.append(round(t, 2))
    cuts.append(round(t_end, 2))
    return cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    prj = Project(a.project)
    m = prj.data["music"]
    y, sr = librosa.load(m["file"], sr=22050, mono=True)
    full = len(y) / sr
    m0, m1 = m.get("start", 0.0), m.get("end", full)
    y = y[int(m0 * sr):int(m1 * sr)]

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units="time")
    env = librosa.onset.onset_strength(y=y, sr=sr)
    on_frames = librosa.onset.onset_detect(onset_envelope=env, sr=sr)
    onsets = librosa.frames_to_time(on_frames, sr=sr)
    strength = env[on_frames]
    gaps = np.diff(np.concatenate([[0.0], onsets]))
    rms = librosa.feature.rms(y=y)[0]
    t = librosa.times_like(rms, sr=sr)
    energy = [float(rms[(t >= s) & (t < s + 1)].mean() * 1000) for s in range(int(t[-1]) + 1)]

    r = prj.style["rhythm"]
    intro_end = float(np.clip(m1 - m0, 0, 11.0))
    cuts = suggest_cuts(onsets, gaps, strength, m1 - m0, intro_end, r["intro_shot"], r["body_shot"])

    print(f"song {full:.1f}s, using {m0:.2f}-{m1:.2f}s, tempo ~{float(np.atleast_1d(tempo)[0]):.0f} bpm")
    peak = max(energy) or 1
    for s, e in enumerate(energy):
        print(f"{s + m0:5.0f}s {e:6.1f} " + "#" * int(40 * e / peak))
    print(f"\n{len(cuts) - 1} shots, cuts: {cuts}")
    (prj.work / "music.json").write_text(json.dumps({
        "range": [m0, m1], "tempo": float(np.atleast_1d(tempo)[0]), "beats": [round(float(b), 3) for b in beats],
        "onsets": [round(float(o), 3) for o in onsets], "energy": energy, "suggested_cuts": cuts}, indent=1))
    if a.write:
        prj.data["cuts"] = cuts
        prj.save()
        print("cuts written to project.json")


if __name__ == "__main__":
    main()
