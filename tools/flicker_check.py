#!/usr/bin/env python3
"""Détecte les clignotements : sauts de luminosité d'une image à l'autre qui ne sont pas des coupes.

Usage: flicker_check.py <video> [--seuil 12] [--retour 6]
Sortie : une ligne par saut suspect (temps, écart de luminosité), puis le total. 0 = OK.
"""
import argparse
import re
import subprocess
import sys


def jumps(luma, times, seuil, retour):
    """Flash = la luminosité saute puis revient au niveau d'avant en moins de `retour` images.
    Une vraie coupe saute et reste : elle n'est pas comptée."""
    out = []
    for i in range(1, len(luma)):
        avant = luma[i - 1]
        if abs(luma[i] - avant) > seuil:
            if any(abs(l - avant) < seuil / 2 for l in luma[i + 1:i + 1 + retour]):
                out.append((times[i], abs(luma[i] - avant)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--seuil", type=float, default=12)
    ap.add_argument("--retour", type=int, default=6)
    a = ap.parse_args()
    vf = "scale=270:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.src, "-vf", vf, "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    times, luma, t = [], [], 0.0
    for line in r.stderr.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m.group(1))
        m = re.search(r"YAVG=([\d.]+)", line)
        if m:
            times.append(t)
            luma.append(float(m.group(1)))
    bad = jumps(luma, times, a.seuil, a.retour)
    for tt, d in bad:
        print(f"{tt:7.2f}s  saut luminosité {d:.1f}")
    print(f"{len(bad)} clignotement(s) hors coupe sur {len(luma)} images")
    return 1 if bad else 0


def demo():
    t = [i / 24 for i in range(6)]
    assert jumps([50, 50, 80, 50, 50, 50], t, 12, 6)  # flash isolé détecté
    assert not jumps([50, 50, 80, 80, 80, 80], t, 12, 6)  # vraie coupe ignorée


if __name__ == "__main__":
    if sys.argv[1:] == ["--demo"]:
        demo()
        print("ok")
        sys.exit(0)
    sys.exit(main())
