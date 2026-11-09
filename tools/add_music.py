#!/usr/bin/env python3
"""Ajoute une musique de fond sous un rendu déjà monté (hook_build.py, compose.py…).

usage: add_music.py video.mp4 musique.mp3 sortie.mp4 [--volume 0.08] [--until 35.4] [--fade 1.5] [--no-duck]
- La voix reste devant : la musique baisse automatiquement quand quelqu'un parle (sidechain), sauf --no-duck.
- --until : la musique s'arrête (fondu) à cet instant, ex. avant le noir final. Par défaut : fin de la vidéo.
- Fondu d'entrée 0,5 s, fondu de sortie --fade s. Loudnorm -14 LUFS à la fin.
Ajoute aussi "music" dans le plan.json si tu veux que le rendu 1080p la garde (le bot relance ce script).
"""
import argparse
import json
import subprocess
import sys


def duration(path: str) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("music")
    ap.add_argument("out")
    ap.add_argument("--volume", type=float, default=0.08)
    ap.add_argument("--until", type=float)
    ap.add_argument("--fade", type=float, default=1.5)
    ap.add_argument("--no-duck", action="store_true")
    a = ap.parse_args()
    end = a.until or duration(a.video)
    fade_st = max(0.0, end - a.fade)
    m = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{end:.3f},asetpts=PTS-STARTPTS,volume={a.volume},"
         f"afade=t=in:d=0.5,afade=t=out:st={fade_st:.3f}:d={a.fade}[m]")
    if a.no_duck:
        mix = "[0:a][m]amix=inputs=2:duration=first:normalize=0[mx]"
        graph = m + ";" + mix
    else:
        graph = (m + ";[0:a]asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.02:ratio=6:attack=20:release=400[md];"
                 "[v][md]amix=inputs=2:duration=first:normalize=0[mx]")
    graph += ";[mx]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", a.music, "-filter_complex", graph,
           "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.out]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(r.returncode)
    print(f"Musique ajoutée (volume {a.volume}, jusqu'à {end:.1f} s) -> {a.out}")


if __name__ == "__main__":
    main()
