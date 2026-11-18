#!/usr/bin/env python3
"""Écran noir explicatif « débutant » (~3:25-3:52), v8b VALIDÉE par Mehdi (préférée à la version pièces, calc_render_pieces.py).
3 scènes l'une après l'autre :
 A. PRODUIT RKHIS : ticket 20 $ − livraison − l'ichhar = 5 $ rbe7 ; puis 1 000 $ ÷ 5 $ = 200 mabi3a (+ 200 colis, 4 000 $ de CA)
 B. PRODUIT GHALI : ticket 390 $ − frais = 100 $ rbe7 ; puis 1 000 $ ÷ 100 $ = 10 mabi3at (+ 10 colis)
 C. CHEFTI LFAR9 : 200 vs 10, « nefs rrbe7 : 1 000 $ »
Chaque élément apparaît sur son mot. Style slides VSL v7. Sortie work/slides/s_calc.mov. Remplace les motions m12-m14.
Lancer depuis la racine du dépôt. Aperçu : calc_render.py 214.0 out.png"""
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

D = "jobs/20261118-062812-edit/work/"
FONT = "assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS = 1920, 1080, 30
GREEN, WHITE, GREY, DARK, CARD, EDGE, RED = (208, 254, 22), (255, 255, 255), (163, 163, 163), (85, 85, 85), (13, 13, 13), (38, 38, 38), (255, 107, 107)
BOX = (196, 160, 110)
_fc = {}


def font(sz, w="ExtraBold"):
    if (sz, w) not in _fc:
        f = ImageFont.truetype(FONT, sz); f.set_variation_by_name(w); _fc[(sz, w)] = f
    return _fc[(sz, w)]


Wd = json.load(open(D + "words_dst.json"))
n = lambda s: s.replace("\xa0", " ").lower()
find = lambda word, after: next(w["t"] for w in Wd if w["t"] >= after and n(w["w"]).startswith(n(word)))

T = dict(p20=find("20", 206), r5=find("5", 207.2), liv=find("livraison", 208), pub=find("dl'ichhar", 209),
         goal=find("1 000", 211), dh=find("10 000", 211.5), div5=find("khassek", 212.5), n200=find("200", 213),
         ca=find("chiffre", 216), sceneB=find("produit", 218.5) - 0.3, p390=find("390", 219), r100=find("100", 221),
         marge=find("marge", 222), akfes=find("akfes", 223), goal2=find("1 000", 225), div100=find("khassek", 226), n10=find("10", 227),
         sceneC=find("chefti", 227.5) - 0.1, c200=find("200", 229), c10=find("10", 230), nefs=find("nefs", 231))
T_IN, T_END = find("produit,", 205) - 0.25, find("3lach", 232) - 0.05
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
up = lambda t, t0, d=0.32: ease((t - t0) / d)
fade = lambda col, u: tuple(int(c * u) for c in col)


def text(d, xy, s, f, col, u=1.0, anchor="mm", dy=18):
    if u > 0: d.text((xy[0], xy[1] + dy * (1 - u)), s, font=f, fill=fade(col, u), anchor=anchor)


def parcel(d, x, y, s, col=BOX):
    d.rounded_rectangle([x, y, x + s, y + s], max(2, s // 6), fill=col)
    d.line([x + s // 2, y, x + s // 2, y + s * 0.45], fill=(0, 0, 0), width=max(1, s // 8))


def parcels(d, cx, y, t, t0, nb, dur):
    s, g, cols = (20, 6, 20) if nb > 50 else (64, 18, 5)
    k = int(nb * min(1, max(0, (t - t0) / dur)))
    gx = cx - (cols * s + (cols - 1) * g) / 2
    for i in range(k): parcel(d, gx + (i % cols) * (s + g), y + (i // cols) * (s + g), s)
    return k


def header(d, title, tag_col):
    d.rectangle([100, 74, 140, 78], fill=GREEN)
    d.text((156, 76), "L ' 7 S A B", font=font(26, "Bold"), fill=GREY, anchor="lm")
    f = font(34); w = f.getlength(title) + 50
    d.rounded_rectangle([W / 2 - w / 2, 60, W / 2 + w / 2, 112], 26, fill=tag_col)
    d.text((W / 2, 86), title, font=f, fill=(0, 0, 0), anchor="mm")
    d.text((W - 60, H - 30), "PROFIT PARTNERS CAPITAL", font=font(22, "Bold"), fill=DARK, anchor="rs")


def ticket(d, t, rows, x0=150, y0=200, w=700):
    """rows : [(t_apparition, gauche, droite, couleur)] ; « = » ligne de total."""
    h = 130 + 100 * len(rows)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 28, fill=CARD, outline=EDGE, width=2)
    d.text((x0 + 40, y0 + 50), "KOL MABI3A", font=font(24, "Bold"), fill=GREY, anchor="lm")
    y = y0 + 120
    for tt, left, right, col in rows:
        u = up(t, tt)
        if left.startswith("="):
            d.line([x0 + 40, y - 48, x0 + w - 40, y - 48], fill=fade(GREY, u), width=3)
        f = font(52 if left.startswith("=") else 44)
        text(d, (x0 + 40, y), left, f, col, u, "lm")
        text(d, (x0 + w - 40, y), right, f, col, u, "rm")
        y += 100


def equation(d, t, parts, cx=1400, y=300):
    """parts : [(t, texte, couleur)] posés à la suite, centrés sur cx."""
    f = font(64); gap = 24
    total = sum(f.getlength(p) for _, p, _ in parts) + gap * (len(parts) - 1)
    x = cx - total / 2
    for tt, p, col in parts:
        text(d, (x, y), p, f, col, up(t, tt), "lm"); x += f.getlength(p) + gap


def scene_a(t):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "PRODUIT RKHIS : 20 $", GREY)
    ticket(d, t, [(T["p20"], "Prix", "20 $", WHITE), (T["liv"], "− livraison", "", RED),
                  (T["pub"], "− l'ichhar", "", RED), (T["r5"], "= Rbe7", "5 $", GREEN)])
    ug = up(t, T["goal"] - 0.1)
    text(d, (1400, 215), "Objectif : 1 000 $ d rbe7" + (" (10 000 dh)" if t >= T["dh"] else ""), font(36, "Bold"), GREY, ug)
    equation(d, t, [(T["goal"], "1 000 $", WHITE), (T["div5"], "÷ 5 $", WHITE), (T["n200"], "=", WHITE), (T["n200"], "200 mabi3a", GREEN)])
    if t >= T["n200"] - 0.5:
        parcels(d, 1400, 420, t, T["n200"] - 0.5, 200, 0.9)
    text(d, (1400, 760), "200 × 20 $ = 4 000 $ de chiffre d'affaires", font(34, "Bold"), GREY, up(t, T["ca"]))
    return img


def scene_b(t):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "PRODUIT GHALI : 390 $", GREEN)
    ticket(d, t, [(T["p390"], "Prix", "390 $", WHITE), (T["p390"] + 0.9, "− frais", "", RED),
                  (T["r100"], "= Rbe7", "100 $", GREEN)])
    ua = up(t, T["akfes"])  # « f akfes l7alat » : le pire des cas (demandé par Mehdi)
    if ua > 0:
        s = "F AKFES L7ALAT  (le pire des cas)"; f = font(30); w = f.getlength(s) + 44
        d.rounded_rectangle([500 - w / 2, 680 - 26, 500 + w / 2, 680 + 26], 26, fill=fade(GREEN, ua))
        d.text((500, 680), s, font=f, fill=(0, 0, 0), anchor="mm")
    text(d, (1400, 215), "Objectif : 1 000 $ d rbe7 (10 000 dh)", font(36, "Bold"), GREY, up(t, T["goal2"] - 0.1))
    equation(d, t, [(T["goal2"], "1 000 $", WHITE), (T["div100"], "÷ 100 $", WHITE), (T["n10"], "=", WHITE), (T["n10"], "10 mabi3at", GREEN)])
    if t >= T["n10"] - 0.3:
        parcels(d, 1400, 440, t, T["n10"] - 0.3, 10, 0.7)
    return img


def scene_c(t):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "CHEFTI LFAR9 ?", GREEN)
    d.line([W / 2, 170, W / 2, 900], fill=(30, 30, 30), width=2)
    for cx, price, nb, lbl, tc in ((480, "Produit à 20 $", 200, "200 mabi3a", T["c200"]), (1440, "Produit à 390 $", 10, "10 mabi3at", T["c10"])):
        text(d, (cx, 220), price, font(44), GREY, 1, dy=0)
        parcels(d, cx, 300, t, -1, nb, 0.01)
        big = 1 + 0.3 * max(0, 1 - abs(t - tc) / 0.45)
        text(d, (cx, 680), lbl, font(int(80 * big)), WHITE, 1, dy=0)
    un = up(t, T["nefs"])
    if un > 0:
        s, f = "=  NEFS RRBE7 : 1 000 $", font(48); w = f.getlength(s) + 70
        d.rounded_rectangle([W / 2 - w / 2, 860 - 20 * (1 - un), W / 2 + w / 2, 940 - 20 * (1 - un)], 40, fill=fade(GREEN, un))
        d.text((W / 2, 900 - 20 * (1 - un)), s, font=f, fill=(0, 0, 0), anchor="mm")
    return img


def frame(t):
    X = 0.3  # fondu entre scènes
    if t < T["sceneB"]: img = scene_a(t)
    elif t < T["sceneB"] + X: img = Image.blend(scene_a(t), scene_b(t), (t - T["sceneB"]) / X)
    elif t < T["sceneC"]: img = scene_b(t)
    elif t < T["sceneC"] + X: img = Image.blend(scene_b(t), scene_c(t), (t - T["sceneC"]) / X)
    else: img = scene_c(t)
    a = min(1, (t - T_IN) / 0.25, (T_END - t) / 0.25)
    return img if a >= 1 else Image.blend(Image.new("RGB", (W, H)), img, max(a, 0))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        frame(float(sys.argv[1])).save(sys.argv[2] if len(sys.argv) > 2 else D + "calc_test.png"); sys.exit()
    out = D + "slides/s_calc.mov"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for k in range(int((T_END - T_IN) * FPS)):
        p.stdin.write(frame(T_IN + k / FPS).tobytes())
    p.stdin.close(); p.wait()
    print(out, round(T_IN, 2), round(T_END - T_IN, 2), {k: round(v, 2) for k, v in T.items()})
