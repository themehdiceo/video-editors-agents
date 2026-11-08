#!/usr/bin/env python3
"""Détecte les silences (forme d'onde) avec ffmpeg silencedetect.

Usage: silences.py <media> <sortie.json> [--noise -35dB] [--min 0.25]

Sortie: {"silences": [{"start": 1.2, "end": 1.9}, ...], "duration": 61.2}
Utilisé avec la transcription pour ne jamais couper au milieu d'un mot :
une coupe doit tomber DANS un silence, jamais dans une zone de son.
"""
import argparse
import json
import re
import subprocess
import sys


def duration(src: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", src], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--noise", default="-35dB")
    ap.add_argument("--min", type=float, default=0.25)
    a = ap.parse_args()
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", a.src, "-af",
         f"silencedetect=noise={a.noise}:d={a.min}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    total = duration(a.src)
    sil, cur = [], None
    for line in proc.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            cur = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and cur is not None:
            sil.append({"start": round(cur, 3), "end": round(float(m.group(1)), 3)})
            cur = None
    if cur is not None:
        sil.append({"start": round(cur, 3), "end": round(total, 3)})
    json.dump({"duration": round(total, 3), "noise": a.noise, "silences": sil}, open(a.out, "w"), indent=1)
    print(f"{len(sil)} silences sur {total:.1f}s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
