#!/usr/bin/env python3
"""Planche contact pour le contrôle qualité : l'agent REGARDE ces images.

Usage: frames.py <video> <sortie.jpg> [--every 1.5] [--cols 6]
       frames.py <video> <dossier/> --at 0,2.5,7   (captures ponctuelles)
"""
import argparse
import os
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--every", type=float, default=1.5)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--at")
    a = ap.parse_args()
    if a.at:
        os.makedirs(a.out, exist_ok=True)
        for t in a.at.split(","):
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", t, "-i", a.src, "-frames:v", "1",
                            "-vf", "scale=540:-2", os.path.join(a.out, f"t{float(t):07.2f}.jpg")], check=True)
        print(f"captures -> {a.out}")
        return 0
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nw=1:nk=1", a.src], capture_output=True, text=True).stdout)
    n = max(1, int(dur / a.every))
    rows = (n + a.cols - 1) // a.cols
    vf = (f"fps=1/{a.every},scale=270:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:"
          f"fontcolor=white:box=1:boxcolor=black@0.6,tile={a.cols}x{rows}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.src, "-vf", vf, "-frames:v", "1", a.out],
                   check=True)
    print(f"planche {a.cols}x{rows} ({n} images) -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
