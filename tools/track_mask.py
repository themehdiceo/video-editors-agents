#!/usr/bin/env python3
"""Suit une marque qui bouge dans un écran de téléphone filmé (marque juste au-dessus de la carte claire du dashboard).
Usage : python3 tools/track_mask.py source.mov t0 t1 --x 190 --w 490 --texte BOUTIQUE [--above 190] [--out masks.json]
Écrit une liste "masks" pour plan.json : [[x, y, w, h, texte, t_debut_src, t_fin_src], ...] (temps SOURCE absolus).
Méthode : à chaque image, haut de la carte claire (médiane de luminosité) ; le masque couvre de (haut - above) à (haut - 4)."""
import argparse
import json
import subprocess

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("t0", type=float)
ap.add_argument("t1", type=float)
ap.add_argument("--x", type=int, default=190)
ap.add_argument("--w", type=int, default=490)
ap.add_argument("--texte", default="BOUTIQUE")
ap.add_argument("--above", type=int, default=190)
ap.add_argument("--probe-x", type=int, default=450, help="début de la zone de sondage (hors logo)")
ap.add_argument("--probe-w", type=int, default=200)
ap.add_argument("--y0", type=int, default=250)
ap.add_argument("--h", type=int, default=900)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--pad", type=float, default=0.12, help="marge de temps autour de la plage")
ap.add_argument("--out")
a = ap.parse_args()

t0, t1 = a.t0 - a.pad, a.t1 + a.pad
W, H = a.probe_w, a.h
cmd = ["ffmpeg", "-v", "error", "-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", a.src,
       "-vf", f"fps={a.fps},crop={W}:{H}:{a.probe_x}:{a.y0},format=gray", "-f", "rawvideo", "-"]
raw = subprocess.run(cmd, capture_output=True, check=True).stdout
n = len(raw) // (W * H)
fr = np.frombuffer(raw[: n * W * H], dtype=np.uint8).reshape(n, H, W)
tops = []
for f in fr:
    med = np.median(f, axis=1)
    idx = np.where(med > 110)[0]
    # première ligne claire suivie de 20 lignes claires (évite un reflet isolé)
    top = None
    for i in idx:
        if i + 20 < H and (med[i:i + 20] > 110).all():
            top = int(i)
            break
    tops.append(a.y0 + top if top is not None else None)
# comble les trous, puis lisse : on prend le plus HAUT de la fenêtre ±3 images pour couvrir le mouvement
last = next((v for v in tops if v is not None), a.y0 + 200)
for i, v in enumerate(tops):
    tops[i] = v if v is not None else last
    last = tops[i]
bottoms, ys = [], []
for i in range(n):
    win = tops[max(0, i - 3): i + 4]
    b = max(win) - 4                       # bas du masque : juste au-dessus de la carte
    y = min(win) - a.above                 # haut du masque
    ys.append(max(0, (y // 10) * 10))
    bottoms.append(b)
# segments de même (y, bas)
segs = []
for i in range(n):
    key = (ys[i], bottoms[i] // 10 * 10 + 10 if False else bottoms[i])
    ts = t0 + i / a.fps
    if segs and abs(segs[-1][0] - ys[i]) < 20 and abs(segs[-1][1] - bottoms[i]) < 20:
        segs[-1][0] = min(segs[-1][0], ys[i])
        segs[-1][1] = max(segs[-1][1], bottoms[i])
        segs[-1][3] = ts + 1 / a.fps
    else:
        segs.append([ys[i], bottoms[i], ts, ts + 1 / a.fps])
masks = [[a.x, y, a.w, b - y, a.texte, round(s, 3), round(e + 0.001, 3)] for y, b, s, e in segs]
print(f"{n} images, {len(masks)} blocs ; haut de carte min/max : {min(tops)}/{max(tops)}")
if a.out:
    json.dump(masks, open(a.out, "w"))
else:
    print(json.dumps(masks))
