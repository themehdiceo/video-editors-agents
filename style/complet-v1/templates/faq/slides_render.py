#!/usr/bin/env python3
"""Écrans noirs animés (slides VSL v7) : noir #000 plein cadre, voix dessous. Plus Jakarta Sans 800, texte blanc,
mots-clés *verts* #D0FE16, surtitre gris #A3A3A3 en capitales espacées précédé d'un trait vert, cartes #0d0d0d bord #262626
coins 28 px, « PROFIT PARTNERS CAPITAL » gris #555 en bas à droite. Chaque élément apparaît sur son mot (glisse 26 px, 0,32 s).
Fondu 0,25 s entrée/sortie. Jamais en même temps qu'une motion (0,5 s d'écart). Sous-titres masqués pendant la slide.
À lancer APRÈS motions_render.py (lit ses overlays dans plan.json)."""
import json, re, subprocess
from PIL import Image, ImageDraw, ImageFont

D = "jobs/20261118-062812-edit/work/"
FONT = "assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS = 1920, 1080, 30
GREEN, WHITE, GREY, DARK = (208, 254, 22, 255), (255, 255, 255, 255), (163, 163, 163, 255), (85, 85, 85, 255)

def font(sz, w="ExtraBold"):
    f = ImageFont.truetype(FONT, sz)
    f.set_variation_by_name(w); return f

FL, FK, FB = font(64), font(28, "Bold"), font(22, "Bold")
Wd = json.load(open(D + "words_dst.json"))
n = lambda s: s.replace("\xa0", " ").lower()
def find(word, after):
    return next((w["t"] for w in Wd if w["t"] >= after and n(w["w"]).startswith(n(word))), None)

TM = json.load(open(D + "aroll_cut.mp4.timemap.json"))["ranges"]
def s2d(x):
    for r in TM:
        if r["src_end"] >= x: return r["dst_start"] + max(0, x - r["src_start"])
    return 1e9
plan = json.load(open(D + "plan.json"))
motions = [(o["at"], o["at"] + o["dur"]) for o in plan["overlays"] if "/motions/" in o["file"]]
plan["overlays"] = [o for o in plan["overlays"] if "/slides/" not in o["file"]]
import os; os.makedirs(D + "slides", exist_ok=True)
S = json.load(open(D + "slides_spec.json"))
windows = []

def segs(txt):  # [(texte, vert?)]
    return [(p, i % 2 == 1) for i, p in enumerate(re.split(r"\*", txt)) if p]

for i, s in enumerate(S):
    ts, last = [], s2d(s["hint_src"]) - 1
    for txt, trig in s["lines"]:
        t = find(trig, last) or last + 1.0
        ts.append(t); last = t
    t_in = ts[0] - 0.2
    e1 = s2d(s["end_src"]); t_end = (find(s["end_word"][0], e1 - 3) or e1) + 0.6
    prev_m = max([b for a, b in motions if a < t_in] or [0]); next_m = min([a for a, b in motions if a > t_in] or [1e9])
    t_in = max(t_in, prev_m + 0.5); t_end = min(t_end, next_m - 0.5)
    dur = t_end - t_in
    # mise en page : bloc centré, aligné à gauche
    rows = []
    for txt, _ in s["lines"]:
        sg = segs(txt); wl = sum(FL.getlength(p) for p, _ in sg)
        rows.append((sg, wl))
    cw = int(max(r[1] for r in rows) + 2 * 44)
    rh, gap = 118, 22
    bh = 60 + len(rows) * (rh + gap)
    x0, y0 = (W - cw) // 2, (H - bh) // 2
    out = D + f"slides/s{i + 1:02d}.mov"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
    cache = {}
    for k in range(int(dur * FPS)):
        t = t_in + k / FPS
        a = min(1, (t - t_in) / 0.25, (t_end - t) / 0.25)
        us = tuple(round(ease((t - (ts[j] if j else t_in)) / 0.32), 2) for j in range(len(rows)))
        key = (round(max(a, 0), 2), us)
        if key not in cache:
            img = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
            d.rectangle([x0, y0 + 14, x0 + 40, y0 + 18], fill=GREEN)
            d.text((x0 + 56, y0 + 16), "  ".join(s["kick"]) if False else " ".join(list(s["kick"])).replace("   ", "  "), font=FK, fill=GREY, anchor="lm")
            d.text((W - 60, H - 50), "PROFIT PARTNERS CAPITAL", font=FB, fill=DARK, anchor="rs")
            y = y0 + 60
            for j, (sg, wl) in enumerate(rows):
                u = us[j]
                if u > 0:
                    lay = Image.new("RGBA", (cw, rh), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                    ld.rounded_rectangle([0, 0, cw - 1, rh - 1], 28, fill=(13, 13, 13, 255), outline=(38, 38, 38, 255), width=2)
                    x = 44
                    for ptxt, g in sg:
                        ld.text((x, rh / 2), ptxt, font=FL, fill=GREEN if g else WHITE, anchor="lm"); x += FL.getlength(ptxt)
                    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * u)))
                    img.alpha_composite(lay, (x0, int(y + 26 * (1 - u))))
                y += rh + gap
            if key[0] < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * max(key[0], 0))))
            cache = {key: img.tobytes()}
        p.stdin.write(cache[key])
    p.stdin.close(); p.wait()
    plan["overlays"].append({"file": f"work/slides/s{i + 1:02d}.mov", "at": round(t_in, 3), "dur": round(dur, 3), "x": 0, "y": 0})
    windows.append((t_in, t_end))
    print(i + 1, round(t_in, 2), round(dur, 2), [round(x, 1) for x in ts])
json.dump(plan, open(D + "plan.json", "w"), indent=1, ensure_ascii=False)
# sous-titres masqués pendant les slides
def sec(x):
    h, m, s_ = x.split(":"); return int(h) * 3600 + int(m) * 60 + float(s_)
lines, kept = open(D + "subs.ass", encoding="utf-8").read().split("\n"), []
for l in lines:
    if l.startswith("Dialogue:"):
        f = l.split(",", 3); a, b = sec(f[1]), sec(f[2])
        if any(a < we and b > ws for ws, we in windows): continue
    kept.append(l)
open(D + "subs.ass", "w", encoding="utf-8").write("\n".join(kept))
json.dump(windows, open(D + "slides_windows.json", "w"))
