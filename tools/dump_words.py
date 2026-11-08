#!/usr/bin/env python3
"""Transcription lisible : une ligne par tour de parole, avec horodatage et locuteur.
usage: dump_words.py words.json out.txt [--gap 0.8]"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
gap = float(sys.argv[sys.argv.index("--gap") + 1]) if "--gap" in sys.argv else 0.8
words = json.load(open(src))["words"]
if "--from" in sys.argv:  # fenêtre : --from 600 --to 630
    t0 = float(sys.argv[sys.argv.index("--from") + 1])
    t1 = float(sys.argv[sys.argv.index("--to") + 1])
    words = [w for w in words if w["start"] >= t0 and w["end"] <= t1]
lines, cur, last, spk = [], [], None, None
for w in words:
    s = w.get("speaker")
    if cur and (s != spk or w["start"] - last > gap):
        lines.append(f"[{cur[0]['start']:.1f}-{cur[-1]['end']:.1f}] {spk}: " + " ".join(x["w"] for x in cur))
        cur = []
    cur.append(w)
    spk, last = s, w["end"]
if cur:
    lines.append(f"[{cur[0]['start']:.1f}-{cur[-1]['end']:.1f}] {spk}: " + " ".join(x["w"] for x in cur))
open(out, "w").write("\n".join(lines))
print(len(lines), "lignes")
