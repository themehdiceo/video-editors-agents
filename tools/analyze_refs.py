#!/usr/bin/env python3
"""Analyse image par image d'une vidéo de référence (pour apprendre un style de montage).

Usage: analyze_refs.py <video> <dossier_sortie> [--scene 0.3] [--max-sheets 6]

Produit dans <dossier_sortie> :
  analysis.json  : durée, coupes (temps), coupes/minute (global, 1re minute, reste), durée des plans
                   (médiane, p10, p90, max), luminosité/saturation moyennes par plan, volume (LUFS).
  shots_XX.jpg   : planches de 24 plans. Pour chaque plan : 1re image (+0,05 s) et dernière image.
                   Compare-les pour voir les zooms, flous d'entrée, mouvements, textes qui apparaissent.
  minute1.jpg    : la 1re minute, une image toutes les 0,5 s (le hook est souvent le plus travaillé).
Ensuite : LIS les planches (outil Read) et transcris la vidéo (tools/transcribe.py) pour relier
chaque visuel à la phrase dite.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys


_fonts = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
FONT = next((os.path.join(_fonts, f) for f in sorted(os.listdir(_fonts)) if f.lower().endswith((".ttf", ".otf")))
            if os.path.isdir(_fonts) else None, None)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(src):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                      "default=nw=1:nk=1", src]).stdout.strip())


def scene_cuts(src, thr):
    r = run(["ffmpeg", "-hide_banner", "-i", src, "-an", "-vf",
             f"scale=320:-2,select='gt(scene,{thr})',showinfo", "-f", "null", "-"])
    return [round(float(m), 3) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def shot_stats(src, t):
    """Luminosité (0-255) et saturation moyennes d'une image."""
    r = run(["ffmpeg", "-hide_banner", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf",
             "scale=160:-2,signalstats,metadata=print", "-f", "null", "-"])
    y = re.search(r"YAVG=([\d.]+)", r.stderr)
    s = re.search(r"SATAVG=([\d.]+)", r.stderr)
    return (round(float(y.group(1)), 1) if y else None, round(float(s.group(1)), 1) if s else None)


def loudness(src):
    r = run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", "ebur128", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def sheet(src, times, out, cols=6, w=320):
    """Planche : une image par temps, en grille, avec le temps écrit sur chaque vignette."""
    tmp = out + ".d"
    os.makedirs(tmp, exist_ok=True)
    files = []
    for i, t in enumerate(times):
        f = os.path.join(tmp, f"{i:04d}.jpg")
        label = f"drawtext=text='{t:.2f}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6"
        if FONT:
            label += f":fontfile='{FONT}'"
        for vf in (f"scale={w}:-2,{label}", f"scale={w}:-2"):  # sans police dispo : pas d'étiquette
            run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, t):.3f}", "-i", src, "-frames:v", "1",
                 "-vf", vf, f])
            if os.path.exists(f):
                break
        if os.path.exists(f):
            files.append(f)
    if not files:
        return
    rows = (len(files) + cols - 1) // cols
    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1", "-i", os.path.join(tmp, "%04d.jpg"),
         "-vf", f"tile={cols}x{rows}:padding=4:color=white", "-frames:v", "1", out])
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--scene", type=float, default=0.3)
    ap.add_argument("--max-sheets", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    dur = duration(a.src)
    cuts = [c for c in scene_cuts(a.src, a.scene) if c > 0.05]
    bounds = [0.0] + cuts + [dur]
    shots = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1) if bounds[i + 1] - bounds[i] > 0.04]
    lens = sorted(e - s for s, e in shots)

    def pct(p):
        return round(lens[min(len(lens) - 1, int(p * len(lens)))], 2) if lens else None

    first_min = [c for c in cuts if c < 60]
    rest_min = max(1e-6, (dur - 60) / 60)
    info = {
        "file": os.path.basename(a.src), "duration": round(dur, 2), "shots": len(shots),
        "cuts_per_min": round(len(cuts) / (dur / 60), 1),
        "cuts_per_min_first_minute": len(first_min) if dur >= 60 else round(len(cuts) / (dur / 60), 1),
        "cuts_per_min_after": round((len(cuts) - len(first_min)) / rest_min, 1) if dur > 60 else None,
        "shot_len_s": {"median": round(statistics.median(lens), 2) if lens else None,
                       "p10": pct(0.1), "p90": pct(0.9), "max": round(max(lens), 2) if lens else None},
        "loudness_lufs": loudness(a.src),
        "cuts": cuts,
        "shot_list": [],
    }
    for s, e in shots[:400]:
        y, sat = shot_stats(a.src, s + min(0.1, (e - s) / 2))
        info["shot_list"].append({"start": round(s, 2), "end": round(e, 2), "len": round(e - s, 2),
                                  "luma": y, "sat": sat})
    json.dump(info, open(os.path.join(a.out, "analysis.json"), "w"), indent=1)

    # Planches : 12 plans par planche, 1re et dernière image de chaque plan côte à côte.
    per = 12
    for k in range(min(a.max_sheets, (len(shots) + per - 1) // per)):
        times = []
        for s, e in shots[k * per:(k + 1) * per]:
            times += [s + 0.05, max(s + 0.05, e - 0.08)]
        sheet(a.src, times, os.path.join(a.out, f"shots_{k + 1:02d}.jpg"), cols=6)
    sheet(a.src, [i * 0.5 for i in range(int(min(60, dur) / 0.5))], os.path.join(a.out, "minute1.jpg"), cols=10, w=192)
    print(f"{info['shots']} plans, {info['cuts_per_min']} coupes/min "
          f"(1re minute {info['cuts_per_min_first_minute']}, ensuite {info['cuts_per_min_after']}), "
          f"plan médian {info['shot_len_s']['median']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
