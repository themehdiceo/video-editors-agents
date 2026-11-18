#!/usr/bin/env python3
"""Écran noir animé « montagne » (remplace la slide s03, ~0:59-1:10) : un grimpeur monte, bloqué par
« 3A9BA » (= l'identité l9dima), passe par-dessus, coche « LFLOUS » puis « L'BUSINESS », drapeau « FORSA » au sommet.
Calé sur les mots (words_dst.json). Style slides VSL v7 (noir, Plus Jakarta Sans 800, vert #D0FE16).
Rendu 2x puis réduit (anti-crénelage). Sortie : work/slides/s03_mont.mov (qtrle). Lancer depuis la racine du dépôt."""
import json, math, re, subprocess
from PIL import Image, ImageDraw, ImageFont

D = "jobs/20261118-062812-edit/work/"
FONT = "assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS, S = 1920, 1080, 30, 2
GREEN, WHITE, GREY, DARK, RED = (208, 254, 22, 255), (255, 255, 255, 255), (163, 163, 163, 255), (85, 85, 85, 255), (255, 77, 77, 255)


def font(sz, w="ExtraBold"):
    f = ImageFont.truetype(FONT, sz * S); f.set_variation_by_name(w); return f


FL, FK, FB, FP = font(52), font(26, "Bold"), font(22, "Bold"), font(26)
Wd = json.load(open(D + "words_dst.json"))
n = lambda s: s.replace("\xa0", " ").lower()
find = lambda word, after: next(w["t"] for w in Wd if w["t"] >= after and n(w["w"]).startswith(n(word)))

T_IN = 59.28
T_END = 70.1                      # avant la motion m04 (70.63) - 0,5 s
t_wra, t_3a9ba, t_forsa = find("wra", 59), find("3a9ba", 59.4), find("forsa", 59.5)
t_ident, t_fker = find("l'identité", 61), find("fker", 62)
t_flous, t_biz = find("lflous", 65.5), find("l'business", 67)

ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
lerp = lambda a, b, u: a + (b - a) * u
slope_y = lambda x: 1040 - 0.592 * (x - 250)        # flanc gauche : (250,1040) -> sommet (1450,330)

# (temps, x) du grimpeur ; entre 2 clés : marche linéaire
KEYS = [(T_IN, 420), (t_3a9ba + 1.2, 712), (t_fker, 712), (t_fker + 0.9, 900),
        (t_flous - 0.1, 1000), (t_biz - 0.1, 1180), (t_biz + 0.7, 1405)]
ROCK_X = 800


def climber_pos(t):
    if t <= KEYS[0][0]: return KEYS[0][1], slope_y(KEYS[0][1]), False
    for (ta, xa), (tb, xb) in zip(KEYS, KEYS[1:]):
        if t <= tb:
            u = (t - ta) / max(tb - ta, 1e-6); x = lerp(xa, xb, u); y = slope_y(x)
            if ta == t_fker:                         # par-dessus le rocher : arc de 110 px
                y -= 150 * math.sin(math.pi * u)
            return x, y, xa != xb
    return KEYS[-1][1], slope_y(KEYS[-1][1]), False


def P(*pts): return [(x * S, y * S) for x, y in pts]


def pill(d, cx, by, txt, bg, fg, u=1.0):
    """Pastille centrée sur cx, bas à by."""
    tw = FP.getlength(txt) / S; w, h = tw + 36, 46
    x0, y0 = cx - w / 2, by - h - 10 * (1 - u)
    d.rounded_rectangle(P((x0, y0), (x0 + w, y0 + h)), 23 * S, fill=bg)
    d.text(((cx) * S, (y0 + h / 2) * S), txt, font=FP, fill=fg, anchor="mm")


def segs(txt): return [(p, i % 2 == 1) for i, p in enumerate(re.split(r"\*", txt)) if p]


LINES = [("Wra kol 3a9ba kayna *forsa*", t_wra - 0.05), ("L3a9ba = *l'identité* dyalek l9dima", t_ident - 0.05)]


def background():
    bg = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 255))
    ImageDraw.Draw(bg).polygon(P((1100, 1080), (1760, 520), (2000, 700), (2000, 1080)), fill=(14, 14, 14, 255))  # montagne de fond
    grad = Image.linear_gradient("L").resize((W * S, H * S)).point(lambda v: 44 - v * 26 // 255)          # flanc : clair en haut
    flank = Image.merge("RGBA", (grad, grad, grad, Image.new("L", (W * S, H * S), 255)))
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).polygon(P((150, 1100), (250, 1040), (1450, 330), (1900, 1040), (1920, 1100)), fill=255)
    bg.paste(flank, (0, 0), mask)
    d = ImageDraw.Draw(bg)
    d.polygon(P((1450, 330), (1360, 383), (1395, 395), (1420, 378), (1450, 405), (1480, 380), (1520, 400), (1560, 400)),
              fill=(232, 232, 232, 255))                                                          # neige
    d.line(P((250, 1040), (1450, 330), (1900, 1040)), fill=(70, 70, 70, 255), width=3 * S)
    d.text(((W - 60) * S, (H - 50) * S), "PROFIT PARTNERS CAPITAL", font=FB, fill=DARK, anchor="rs")
    return bg


BG = background()


def draw_climber(d, x0, y0, t, walking, arms_up, k=1.5):
    ph = math.sin(t * 9) if walking else 0
    def P(*pts): return [((x0 + (px - x0) * k) * S, (y0 + (py - y0) * k) * S) for px, py in pts]
    x, y = x0, y0
    hip = (x, y - 42); neck = (x + 6, y - 82); head = (x + 9, y - 98)
    d.rounded_rectangle(P((x - 16, y - 84), (x + 2, y - 50)), 6 * S, fill=GREEN)                  # sac à dos
    for s in (1, -1):
        d.line(P(hip, (x + 10 * ph * s, y)), fill=WHITE, width=int(7 * k * S))                               # jambes
        if arms_up: d.line(P(neck, (x + 6 + 14 * s, y - 128)), fill=WHITE, width=int(6 * k * S))
        else: d.line(P(neck, (x + 6 + 14 * ph * s + 6, y - 50)), fill=WHITE, width=int(6 * k * S))
    d.line(P(hip, neck), fill=WHITE, width=int(8 * k * S))
    d.ellipse(P((head[0] - 13, head[1] - 13), (head[0] + 13, head[1] + 13)), fill=WHITE)


def frame(t):
    img = BG.copy(); d = ImageDraw.Draw(img)
    # surtitre + lignes (cartes)
    d.rectangle(P((100, 74), (140, 78)), fill=GREEN)
    d.text((156 * S, 76 * S), "L ' 3 A 9 B A", font=FK, fill=GREY, anchor="lm")
    y = 110
    for txt, tt in LINES:
        u = ease((t - tt) / 0.32)
        if u > 0:
            sg = segs(txt); wl = sum(FL.getlength(p) for p, _ in sg) / S; cw, rh = wl + 80, 100
            lay = Image.new("RGBA", (int(cw * S), rh * S), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([0, 0, cw * S - 1, rh * S - 1], 26 * S, fill=(13, 13, 13, 255), outline=(38, 38, 38, 255), width=2 * S)
            x = 40
            for p, g in sg:
                ld.text((x * S, rh / 2 * S), p, font=FL, fill=GREEN if g else WHITE, anchor="lm"); x += FL.getlength(p) / S
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * u)))
            img.alpha_composite(lay, (100 * S, int((y + 26 * (1 - u)) * S)))
        y += 118
    d = ImageDraw.Draw(img)
    # drapeau FORSA au sommet
    uf = ease((t - t_forsa) / 0.4)
    if uf > 0:
        top = 330 - 120 * uf
        d.line(P((1452, 332), (1452, top)), fill=WHITE, width=5 * S)
        wave = 6 * math.sin(t * 5)
        d.polygon(P((1454, top), (1600, top + 6 + wave), (1600, top + 56 + wave), (1454, top + 50)), fill=GREEN)
        d.text((1527 * S, (top + 29 + wave / 2) * S), "FORSA", font=FP, fill=(0, 0, 0, 255), anchor="mm")
    # checkpoints LFLOUS / L'BUSINESS (apparaissent après le rocher, verts quand atteints)
    for cx, label, tt in ((1000, "LFLOUS", t_flous), (1180, "L'BUSINESS", t_biz)):
        ua = ease((t - (t_fker + 0.9)) / 0.35)
        if ua > 0:
            cy = slope_y(cx)
            d.line(P((cx, cy), (cx, cy - 175)), fill=(120, 120, 120, 255), width=3 * S)
            done = t >= tt
            pill(d, cx - FP.getlength(label) / S / 2 - 30, cy - 130, ("✓ " if False else "") + label, GREEN if done else (13, 13, 13, 255),
                 (0, 0, 0, 255) if done else WHITE, ua)
    # rocher 3A9BA : tombe après le passage
    ur = ease((t - (t_fker + 0.9)) / 0.8)
    rx = ROCK_X - 260 * ur; ry = slope_y(rx) + 0; rock_a = int(255 * (1 - ur))
    if rock_a > 0:
        rock = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); rd = ImageDraw.Draw(rock)
        R = lambda dx, dy: (rx + 1.4 * dx, ry + 1.4 * dy)
        rd.polygon(P(R(-62, 30), R(-50, -70), R(-10, -104), R(40, -88), R(66, -30), R(60, -10)),
                   fill=(92, 40, 40, 255), outline=RED, width=3 * S)
        ul = min(ease((t - t_3a9ba) / 0.3), 1 - ease((t - t_fker) / 0.2))
        if ul > 0:
            lab = "L'IDENTITÉ L9DIMA" if t >= t_ident else "3A9BA"
            pill(rd, rx, ry - 160, lab, RED, WHITE, ul)
        rock.putalpha(rock.getchannel("A").point(lambda v: v * rock_a // 255))
        img.alpha_composite(rock); d = ImageDraw.Draw(img)
    # grimpeur (pousse le rocher quand il est bloqué)
    x, yy, walking = climber_pos(t)
    blocked = t_3a9ba + 1.2 <= t < t_fker
    if blocked: x += 4 * math.sin(t * 14)
    draw_climber(d, x, yy, t, walking or blocked, t >= KEYS[-1][0])
    # sommet : halo vert
    if t >= KEYS[-1][0]:
        u = ease((t - KEYS[-1][0]) / 0.5)
        for r in (45, 70):
            d.ellipse(P((1405 - r * u, 285 - r * u), (1405 + r * u, 285 + r * u)), outline=(208, 254, 22, int(160 * (1 - u * 0.6))), width=3 * S)
    a = min(1, (t - T_IN) / 0.25, (T_END - t) / 0.25)
    img = img.resize((W, H), Image.LANCZOS)
    if a < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * max(a, 0))))
    return img


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:                                          # aperçu d'une image : mountain_render.py 66.0
        frame(float(sys.argv[1])).save(sys.argv[2] if len(sys.argv) > 2 else D + "mont_test.png"); sys.exit()
    out = D + "slides/s03_mont.mov"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for k in range(int((T_END - T_IN) * FPS)):
        p.stdin.write(frame(T_IN + k / FPS).tobytes())
    p.stdin.close(); p.wait()
    print(out, round(T_END - T_IN, 2), dict(forsa=t_forsa, ident=t_ident, fker=t_fker, flous=t_flous, biz=t_biz))
