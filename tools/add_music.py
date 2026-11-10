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
    ap.add_argument("--volume", type=float, default=0.3)
    ap.add_argument("--start", type=float, default=0.0, help="décalage dans le morceau (passer une intro molle)")
    ap.add_argument("--delay", type=float, default=0.0, help="la musique commence à cet instant de la vidéo")
    ap.add_argument("--duck-ratio", type=float, default=3.0, help="force de la baisse sous la voix (2 léger, 6 fort)")
    ap.add_argument("--until", type=float)
    ap.add_argument("--fade", type=float, default=1.5)
    ap.add_argument("--no-duck", action="store_true")
    a = ap.parse_args()
    end = a.until or duration(a.video)
    span = max(0.5, end - a.delay)
    fade_st = max(0.0, span - a.fade)
    dl = int(a.delay * 1000)
    m = (f"[1:a]aloop=loop=-1:size=2e9,atrim={a.start:.3f}:{a.start + span:.3f},asetpts=PTS-STARTPTS,loudnorm=I=-14:TP=-2,volume={a.volume},"
         f"afade=t=in:d=0.8,afade=t=out:st={fade_st:.3f}:d={a.fade},adelay={dl}|{dl},aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[m]")
    if a.no_duck:
        mix = "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[v0];[v0][m]amix=inputs=2:duration=first:normalize=0[mx]"
        graph = m + ";" + mix
    else:
        graph = (m + f";[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,asplit=2[v][sc];[m][sc]sidechaincompress=threshold=0.05:ratio={a.duck_ratio}:attack=30:release=500[md];"
                 "[v][md]amix=inputs=2:duration=first:normalize=0[mx]")
    graph += ";[mx]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", a.music, "-filter_complex", graph,
           "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.out]
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(r.returncode)
    print(f"Musique ajoutée (volume {a.volume}, jusqu'à {end:.1f} s) -> {a.out}")


if __name__ == "__main__":
    main()
