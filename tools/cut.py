#!/usr/bin/env python3
"""Coupe l'A-roll à partir d'une liste de passages à GARDER.

Usage: cut.py <source> <keep.json> <sortie.mp4> [--silences silences.json] [--pad 0.06]

keep.json: {"keep": [{"start": 0.40, "end": 4.95, "why": "hook"}, ...]}

- Chaque bord est "accroché" au silence le plus proche (forme d'onde) pour ne
  jamais couper un mot : un début recule dans le silence précédent, une fin
  avance dans le silence suivant, sans dépasser `pad` secondes de silence gardé.
- Micro-fondu audio de 15 ms à chaque raccord pour éviter les clics.
- Écrit aussi <sortie>.timemap.json : correspondance ancien temps -> nouveau temps
  (utilisé par subtitles.py et compose.py).
"""
import argparse
import json
import subprocess
import sys


def snap(keep, silences, pad):
    out = []
    for k in keep:
        s, e = float(k["start"]), float(k["end"])
        for z in silences:
            # début tombant dans un silence ou juste après : on démarre `pad` avant la fin du silence
            if z["start"] - 0.05 <= s <= z["end"] + 0.08:
                s = max(z["start"], z["end"] - pad)
            # fin tombant dans un silence ou juste avant : on finit `pad` après le début du silence
            if z["start"] - 0.08 <= e <= z["end"] + 0.05:
                e = min(z["end"], z["start"] + pad)
        if e - s > 0.08:
            out.append({**k, "start": round(s, 3), "end": round(e, 3)})
    # fusionne les chevauchements
    out.sort(key=lambda r: r["start"])
    merged = []
    for r in out:
        if merged and r["start"] <= merged[-1]["end"] + 0.02:
            merged[-1]["end"] = max(merged[-1]["end"], r["end"])
        else:
            merged.append(dict(r))
    return merged


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("keep")
    ap.add_argument("out")
    ap.add_argument("--silences")
    ap.add_argument("--pad", type=float, default=0.06)
    a = ap.parse_args()

    keep = json.load(open(a.keep))["keep"]
    sil = json.load(open(a.silences))["silences"] if a.silences else []
    ranges = snap(keep, sil, a.pad) if sil else keep

    parts, labels = [], []
    for i, r in enumerate(ranges):
        d = r["end"] - r["start"]
        fo = max(0.0, d - 0.015)
        parts.append(f"[0:v]trim=start={r['start']}:end={r['end']},setpts=PTS-STARTPTS[v{i}];")
        parts.append(f"[0:a]atrim=start={r['start']}:end={r['end']},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d=0.015,afade=t=out:st={fo:.3f}:d=0.015[a{i}];")
        labels.append(f"[v{i}][a{i}]")
    # 30 i/s (le rendu final est en 30 i/s) et preset rapide : 3 à 5 fois plus vite qu'avant, qualité gardée (crf 17).
    graph = "".join(parts) + "".join(labels) + f"concat=n={len(ranges)}:v=1:a=1[vc][a];[vc]fps=30[v]"
    import ffprogress
    ffprogress.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.src, "-filter_complex", graph,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out],
                   sum(r["end"] - r["start"] for r in ranges), ffprogress.find_log(a.out), "Découpe")

    t, tm = 0.0, []
    for r in ranges:
        tm.append({"src_start": r["start"], "src_end": r["end"], "dst_start": round(t, 3)})
        t += r["end"] - r["start"]
    json.dump({"ranges": tm, "duration": round(t, 3)}, open(a.out + ".timemap.json", "w"), indent=1)
    print(f"{len(ranges)} passages gardés, durée finale {t:.1f}s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
