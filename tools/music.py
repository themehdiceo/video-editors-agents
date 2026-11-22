#!/usr/bin/env python3
"""Musique de fond.

Usage: music.py "<ambiance>" <sortie.mp3> [--dur 60]

1. Si ELEVENLABS_API_KEY est défini : génère une musique instrumentale via l'API ElevenLabs Music.
2. Sinon (ou en cas d'échec) : prend un morceau dans assets/music/ (libre de droits),
   en préférant un fichier dont le nom contient un mot de l'ambiance.
Code de sortie 2 si aucune musique n'est disponible (le montage continue sans).
"""
import argparse
import json
import os
import random
import shutil
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def elevenlabs(prompt: str, dur: float, out: str) -> bool:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return False
    body = json.dumps({"prompt": f"{prompt}. Instrumental, no vocals, background music for a short video.",
                       "music_length_ms": int(dur * 1000)}).encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r, open(out, "wb") as f:
            shutil.copyfileobj(r, f)
        return os.path.getsize(out) > 10000
    except Exception as e:  # noqa: BLE001
        print(f"ElevenLabs indisponible ({e}), on passe à la bibliothèque locale", file=sys.stderr)
        return False


def library(prompt: str, out: str) -> bool:
    lib = os.path.join(ROOT, "assets", "music")
    if not os.path.isdir(lib):
        return False
    files = [f for f in os.listdir(lib) if f.lower().endswith((".mp3", ".wav", ".m4a", ".ogg"))]
    if not files:
        return False
    words = [w.lower() for w in prompt.replace(",", " ").split() if len(w) > 3]
    scored = [f for f in files if any(w in f.lower() for w in words)]
    shutil.copy(os.path.join(lib, random.choice(scored or files)), out)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("out")
    ap.add_argument("--dur", type=float, default=60)
    a = ap.parse_args()
    if elevenlabs(a.prompt, a.dur, a.out):
        print(f"musique ElevenLabs -> {a.out}")
        return 0
    if library(a.prompt, a.out):
        print(f"musique de la bibliothèque -> {a.out}")
        return 0
    print("aucune musique disponible (ajoute des mp3 dans assets/music/)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
