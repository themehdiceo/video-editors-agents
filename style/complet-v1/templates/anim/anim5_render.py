#!/usr/bin/env python3
"""5 animations explicatives (choisies par Jeremy, « GO LES 5 » de Mehdi le 2026-11-18), écrans noirs plein cadre,
chaque élément sur son mot (words_dst.json). Style slides VSL v7 / calc_render.py (v8b validée).
  a1 budget (1 % recherche / 99 % pub, appels vidéo, budget qui suit le produit qui vend)
  a2 un produit, 3 angles marketing (l3yalat / rjal / kbar f l3mer)
  a3 akfes l7alat : ticket 390 − 250 = 140, − 120 de pub (CPA) = 20 $
  a4 l'enchère Facebook : 60 $ (5 $ de rbe7) contre 390 $
  a5 circuit de l'argent : carte marocaine -> carte virtuelle (cashback) -> banque US -> banque au Maroc
Usage (racine du dépôt) : anim5_render.py [a1 a2 …]  -> work/slides/<id>.mov + work/anim5_windows.json
                          anim5_render.py a3 384.0 out.png  -> aperçu d'une image"""
import json, math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

D = "jobs/20261118-062812-edit/work/"
FONT = "assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS = 1920, 1080, 30
GREEN, WHITE, GREY, DARK, CARD, EDGE = (208, 254, 22), (255, 255, 255), (163, 163, 163), (85, 85, 85), (13, 13, 13), (38, 38, 38)
RED, GOLD, BOX, BLUE, BLACK = (255, 107, 107), (240, 190, 60), (196, 160, 110), (90, 150, 255), (0, 0, 0)
_fc = {}


def font(sz, w="ExtraBold"):
    sz = max(8, int(sz))
    if (sz, w) not in _fc:
        f = ImageFont.truetype(FONT, sz); f.set_variation_by_name(w); _fc[(sz, w)] = f
    return _fc[(sz, w)]


Wd = json.load(open(D + "words_dst.json"))
nrm = lambda s: s.replace("\xa0", " ").lower()


def find(word, after):
    return next(w["t"] for w in Wd if w["t"] >= after and nrm(w["w"]).startswith(nrm(word)))


ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
up = lambda t, t0, d=0.32: ease((t - t0) / d)
fade = lambda col, u: tuple(int(c * max(0, min(1, u))) for c in col)
lerp = lambda a, b, u: a + (b - a) * u


# ---------- dessin ----------
def text(d, xy, s, sz, col, u=1.0, anchor="mm", dy=18, w="ExtraBold"):
    if u > 0: d.text((xy[0], xy[1] + dy * (1 - u)), s, font=font(sz, w), fill=fade(col, u), anchor=anchor)


def header(d, kick, title, col=GREEN):
    d.rectangle([100, 74, 140, 78], fill=GREEN)
    d.text((156, 76), " ".join(kick), font=font(26, "Bold"), fill=GREY, anchor="lm")
    f = font(34); w = f.getlength(title) + 50
    d.rounded_rectangle([W / 2 - w / 2, 60, W / 2 + w / 2, 112], 26, fill=col)
    d.text((W / 2, 86), title, font=f, fill=BLACK, anchor="mm")
    d.text((W - 60, H - 30), "PROFIT PARTNERS CAPITAL", font=font(22, "Bold"), fill=DARK, anchor="rs")


def pill(d, cx, cy, s, bg, fg=BLACK, sz=30, u=1.0):
    if u <= 0: return
    f = font(sz); w, h = f.getlength(s) + 40, sz + 22
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], h / 2, fill=fade(bg, u))
    d.text((cx, cy), s, font=f, fill=fade(fg, u) if fg != BLACK else BLACK, anchor="mm")


def card(d, box, u=1.0, r=26, outline=EDGE):
    d.rounded_rectangle(box, r, fill=fade(CARD, u), outline=fade(outline, u), width=2)


def arrow(d, a, b, col, u=1.0, w=8):
    if u <= 0: return
    x = lerp(a[0], b[0], u); y = lerp(a[1], b[1], u)
    d.line([a, (x, y)], fill=col, width=w)
    ang = math.atan2(y - a[1], x - a[0]); L = 26
    d.polygon([(x, y), (x - L * math.cos(ang - 0.45), y - L * math.sin(ang - 0.45)),
               (x - L * math.cos(ang + 0.45), y - L * math.sin(ang + 0.45))], fill=col)


def check(d, cx, cy, s, col):
    d.line([(cx - s, cy), (cx - s / 3, cy + s * 0.7), (cx + s, cy - s * 0.7)], fill=col, width=max(4, int(s / 3)), joint="curve")


def cross(d, cx, cy, s, col):
    d.line([(cx - s, cy - s), (cx + s, cy + s)], fill=col, width=max(4, int(s / 3)))
    d.line([(cx - s, cy + s), (cx + s, cy - s)], fill=col, width=max(4, int(s / 3)))


def person(d, x, y, k=1.0, col=WHITE, kind="man", arms_up=False):
    """y = pieds."""
    P = lambda px, py: (x + px * k, y + py * k)
    wd = max(3, int(7 * k))
    hip, neck = P(0, -45), P(0, -90)
    for s in (1, -1): d.line([hip, P(12 * s, 0)], fill=col, width=wd)
    if kind == "woman":
        d.polygon([P(0, -92), P(-24, -40), P(24, -40)], fill=col)
    d.line([hip, neck], fill=col, width=wd + 1)
    for s in (1, -1):
        d.line([P(0, -84), P(22 * s, -120) if arms_up else P(18 * s, -55)], fill=col, width=wd - 1)
    d.ellipse([P(-15, -122), P(15, -92)], fill=col)
    if kind == "woman":
        d.line([P(-15, -110), P(-19, -80)], fill=col, width=wd); d.line([P(15, -110), P(19, -80)], fill=col, width=wd)
    if kind == "old":
        d.line([P(26, -60), P(30, 0)], fill=col, width=wd - 1); d.arc([P(14, -72), P(38, -48)], 180, 360, fill=col, width=wd - 1)
        d.line([hip, neck], fill=col, width=wd + 1)


def parcel(d, x, y, s, col=BOX):
    d.rounded_rectangle([x, y, x + s, y + s], max(2, s // 6), fill=col)
    d.line([x + s // 2, y, x + s // 2, y + s * 0.45], fill=BLACK, width=max(1, s // 8))


def coin(d, x, y, r, col, lbl="$"):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=BLACK, width=2)
    d.text((x, y + 1), lbl, font=font(r * 1.0), fill=BLACK, anchor="mm")


def megaphone(d, cx, cy, col, k=1.0):
    P = lambda px, py: (cx + px * k, cy + py * k)
    d.polygon([P(-50, -15), P(30, -50), P(30, 50), P(-50, 15)], fill=col)
    d.rounded_rectangle([P(-68, -18), P(-46, 18)], 5, fill=col)
    for r in (18, 34): d.arc([P(30 - r, -r), P(30 + r, r)], -40, 40, fill=col, width=max(3, int(5 * k)))


def magnifier(d, cx, cy, col, k=1.0):
    d.ellipse([cx - 34 * k, cy - 34 * k, cx + 34 * k, cy + 34 * k], outline=col, width=int(9 * k))
    d.line([(cx + 24 * k, cy + 24 * k), (cx + 62 * k, cy + 62 * k)], fill=col, width=int(12 * k))


def bottle(d, cx, cy, col, k=1.0):
    d.rounded_rectangle([cx - 45 * k, cy - 60 * k, cx + 45 * k, cy + 90 * k], 22 * k, fill=col)
    d.rectangle([cx - 20 * k, cy - 95 * k, cx + 20 * k, cy - 58 * k], fill=col)
    d.rounded_rectangle([cx - 30 * k, cy - 10 * k, cx + 30 * k, cy + 40 * k], 8 * k, fill=BLACK)
    d.text((cx, cy + 15 * k), "P", font=font(34 * k), fill=col, anchor="mm")


def bubble(d, cx, cy, w, h, col, label, tcol=BLACK, sz=30, tail=(0, 1)):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 24, fill=col)
    tx, ty = cx + tail[0] * w * 0.2, cy + h / 2
    d.polygon([(tx - 18, ty - 2), (tx + 18, ty - 2), (tx, ty + 26)], fill=col)
    d.text((cx, cy), label, font=font(sz), fill=tcol, anchor="mm")


def bankcard(d, cx, cy, col, label, k=1.0, u=1.0):
    w, h = 300 * k, 190 * k
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 22 * k, fill=fade(col, u))
    d.rounded_rectangle([cx - w / 2 + 26 * k, cy - h / 2 + 46 * k, cx - w / 2 + 76 * k, cy - h / 2 + 84 * k], 6, fill=fade(GOLD, u))
    d.text((cx - w / 2 + 26 * k, cy + h / 2 - 34 * k), label, font=font(26 * k), fill=fade(BLACK, u) if u >= 1 else BLACK, anchor="lm")


def bank(d, cx, cy, col, k=1.0):
    d.polygon([(cx - 110 * k, cy - 50 * k), (cx, cy - 115 * k), (cx + 110 * k, cy - 50 * k)], fill=col)
    for i in range(4):
        x = cx - 80 * k + i * 53 * k
        d.rectangle([x - 11 * k, cy - 40 * k, x + 11 * k, cy + 50 * k], fill=col)
    d.rectangle([cx - 120 * k, cy + 56 * k, cx + 120 * k, cy + 76 * k], fill=col)


def flag_us(d, x, y, w=110, h=70):
    for i in range(7):
        d.rectangle([x, y + i * h / 7, x + w, y + (i + 0.5) * h / 7], fill=(200, 40, 50))
        d.rectangle([x, y + (i + 0.5) * h / 7, x + w, y + (i + 1) * h / 7], fill=WHITE)
    d.rectangle([x, y, x + w * 0.42, y + h * 0.54], fill=(40, 60, 140))


def flag_ma(d, x, y, w=110, h=70):
    d.rectangle([x, y, x + w, y + h], fill=(193, 39, 45))
    cx, cy, r = x + w / 2, y + h / 2, h * 0.32
    pts = [(cx + r * math.sin(math.radians(a)), cy - r * math.cos(math.radians(a))) for a in range(0, 720, 144)]
    d.line(pts + [pts[0]], fill=(0, 98, 51), width=4)


def lock(d, cx, cy, col, k=1.0):
    d.arc([cx - 18 * k, cy - 40 * k, cx + 18 * k, cy], 180, 360, fill=col, width=int(6 * k))
    d.line([(cx - 18 * k, cy - 20 * k), (cx - 18 * k, cy)], fill=col, width=int(6 * k))
    d.line([(cx + 18 * k, cy - 20 * k), (cx + 18 * k, cy)], fill=col, width=int(6 * k))
    d.rounded_rectangle([cx - 28 * k, cy - 4 * k, cx + 28 * k, cy + 38 * k], 6, fill=col)


def hammer(d, cx, cy, col, ang=0.0):
    c, s = math.cos(ang), math.sin(ang)
    R = lambda px, py: (cx + px * c - py * s, cy + px * s + py * c)
    d.line([R(0, 0), R(0, 110)], fill=col, width=12)
    d.polygon([R(-55, -22), R(55, -22), R(55, 22), R(-55, 22)], fill=col)


def ticket(d, t, rows, x0=150, y0=180, w=720, title="KOL MABI3A"):
    h = 120 + 96 * len(rows)
    card(d, [x0, y0, x0 + w, y0 + h], 1, 28)
    d.text((x0 + 40, y0 + 50), title, font=font(24, "Bold"), fill=GREY, anchor="lm")
    y = y0 + 116
    for tt, left, right, col in rows:
        u = up(t, tt)
        tot = left.startswith("=")
        if tot and u > 0: d.line([x0 + 40, y - 46, x0 + w - 40, y - 46], fill=fade(GREY, u), width=3)
        sz = 50 if tot else 42
        text(d, (x0 + 40, y), left, sz, col, u, "lm"); text(d, (x0 + w - 40, y), right, sz, col, u, "rm")
        y += 96


# ---------- a1 : budget ----------
def a1(t, T):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    if t < T["prod"] - 0.3 or True:
        pass
    sA = 1 - ease((t - (T["prod"] - 0.3)) / 0.3)   # 1 = partie A visible
    if sA > 0:
        la = Image.new("RGB", (W, H)); d2 = ImageDraw.Draw(la)
        header(d2, "L'BUDGET", "L'BUDGET DYALEK F PROFIT PARTNERS")
        x0, x1, y0, y1 = 200, 1720, 250, 350
        ub = up(t, T["p1"] - 0.2, 0.5)
        if ub > 0:
            d2.rounded_rectangle([x0, y0, x0 + (x1 - x0) * ub, y1], 18, fill=(40, 40, 40))
        u1 = up(t, T["p1"])
        if u1 > 0:
            d2.rounded_rectangle([x0, y0, x0 + 70, y1], 18, fill=fade(WHITE, u1))
            text(d2, (x0 + 35, y1 + 40), "1 %", 40, WHITE, u1)
            magnifier(d2, 330, 520, fade(WHITE, up(t, T["rech"])), 1.0)
            text(d2, (330, 640), "Recherche dyal les produits", 32, WHITE, up(t, T["rech"]))
            text(d2, (330, 690), "n3erfo l'produit li khdam", 30, GREY, up(t, T["khdam"]), w="Bold")
        u99 = up(t, T["p99"], 0.6)
        if u99 > 0:
            d2.rounded_rectangle([x0 + 80, y0, x0 + 80 + (x1 - x0 - 80) * u99, y1], 18, fill=GREEN)
            text(d2, ((x0 + 80 + x1) / 2, (y0 + y1) / 2), "99 %  L'ICHHAR", 44, BLACK, u99, dy=0)
            ui = up(t, T["ichhar"])
            megaphone(d2, 1000, 540, fade(GREEN, ui), 1.1)
            arrow(d2, (1110, 540), (1330, 540), fade(GREEN, ui), up(t, T["mabi3at"] - 0.3, 0.4))
            um = up(t, T["mabi3at"])
            if um > 0:
                for i in range(6): parcel(d2, 1360 + (i % 3) * 80, 470 + (i // 3) * 80, 64)
                text(d2, (1470, 680), "Mabi3at", 34, WHITE, um)
        uc = up(t, T["ana"])
        if uc > 0:
            for i, (who, tt) in enumerate((("Ana", T["ana"]), ("Nta", T["nta"]))):
                u = up(t, tt); cx = 760 + i * 400
                card(d2, [cx - 170, 760, cx + 170, 990], u, 20, outline=fade(GREY, u))
                person(d2, cx, 975, 1.0, fade(WHITE, u), "man")
                text(d2, (cx, 790), who, 30, GREEN, u, dy=0)
            text(d2, (W / 2, 1025), "Appels vidéo, ensemble", 30, GREY, up(t, T["appels"]), w="Bold")
        img = Image.blend(img, la, sA) if sA < 1 else la
        d = ImageDraw.Draw(img)
    if t >= T["prod"] - 0.3:
        lb = Image.new("RGB", (W, H)); d2 = ImageDraw.Draw(lb)
        header(d2, "L'BUDGET", "L'BUDGET KAYTBE3 L'PRODUIT LI KAYTBA3")
        xs = (560, 960, 1360)
        for i, cx in enumerate(xs):
            u = up(t, T["prod"] + i * 0.12)
            parcel(d2, cx - 60, 700, 120, fade(BOX, u))
            text(d2, (cx, 860), f"Produit {i + 1}", 34, WHITE, u)
            # ventes
            us = up(t, T["tba3"], 0.6)
            sales = (1.0, 0.25, 0.2)[i]
            if us > 0:
                h = 200 * sales * us
                d2.rounded_rectangle([cx - 30, 690 - h, cx + 30, 690], 8, fill=GOLD)
            if i == 0:
                ua = up(t, T["tl3o"], 0.7)
                if ua > 0:
                    arrow(d2, (cx + 110, 690), (cx + 110, 690 - 420 * ua), GREEN, 1, 14)
                    text(d2, (cx + 220, 340), "Budget  +", 40, GREEN, ua)
                text(d2, (cx, 920), "kaytba3 bzaf", 30, GREEN, up(t, T["tba3"]), w="Bold")
            else:
                ul = up(t, T["thabet"], 0.4)
                if ul > 0:
                    d2.line([(cx + 80, 600), (cx + 150, 600)], fill=fade(GREY, ul), width=10)
                    lock(d2, cx + 115, 520, fade(GREY, ul), 0.9)
                    text(d2, (cx + 115, 640), "thabet", 28, GREY, ul, w="Bold")
                text(d2, (cx, 920), "ma kaytba3ch bzaf", 28, GREY, up(t, T["matba3"]), w="Bold")
        text(d2, (W / 2, 1000), "W kanb9aw noptimisiw", 34, WHITE, up(t, T["optim"]))
        u = ease((t - (T["prod"] - 0.3)) / 0.3)
        img = Image.blend(img, lb, u) if u < 1 else lb
    return img


def t_a1():
    return dict(start=find("f", 89.8) - 0.05, end=find("noptimisiw", 110) + 0.5,
                p1=find("1 %", 91), rech=find("l'recherche", 92), khdam=find("n3erfo", 94), p99=find("99 %", 96),
                ichhar=find("l'ichhar", 96.5), mabi3at=find("mabi3at", 98), ana=find("ana", 100), nta=find("nta", 100.6),
                appels=find("appels", 101), prod=find("produits", 102.5), tba3=find("kaytba3o", 103), tl3o=find("kantl3o", 103.5),
                matba3=find("kaytba3ouch", 105), thabet=find("thabet", 107), optim=find("noptimisiw", 110))


# ---------- a2 : angles ----------
def a2(t, T):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "L E S  A N G L E S".replace(" ", "")[:0] or "ANGLES", "NEFS L'PRODUIT, 3 D LES MESSAGES")
    up0 = up(t, T["nefs"])
    win = 1 if t >= T["kter"] else -1
    zoom = up(t, T["mrkz"], 0.4)
    bottle(d, W / 2, 870, fade(WHITE, up0), 1.0)
    text(d, (W / 2, 1010), "Nefs l'produit", 32, WHITE, up0)
    pos = [(480, 330), (960, 300), (1440, 330)]
    people = [("L3yalat", "woman", T["l3yalat"]), ("Rjal", "man", T["rjal"]), ("Kbar f l3mer", "old", T["kbar"])]
    for i, ((bx, by), (lbl, kind, tp)) in enumerate(zip(pos, people)):
        ub = up(t, T["msg"] + i * 0.25, 0.4)
        if ub <= 0: continue
        arrow(d, (W / 2 + (i - 1) * 60, 770), (bx + (1 - i) * 40, 715), fade((60, 60, 60), ub), ub, 5)
        dim = 0.35 if (t >= T["kter"] and i != win) else 1.0
        isw = t >= T["kter"] and i == win
        k = 1 + 0.15 * zoom if isw else 1
        col = GREEN if isw else WHITE
        bubble(d, bx, by, 330 * k, 110 * k, fade(col, ub * dim), f"Message {i + 1}", sz=34 * k)
        up_ = up(t, tp)
        if up_ > 0:
            person(d, bx, 640, 1.15, fade(col if isw else WHITE, up_ * dim), kind)
            text(d, (bx, 685), lbl, 34, fade(col, dim) if dim < 1 else col, up_)
        if isw:
            check(d, bx + 210 * k, by, 22, GREEN)
            pill(d, bx + 200, 580, "Kaykhdem kter", GREEN, BLACK, 30, up(t, T["kter"]))
    text(d, (W / 2, 175), "3 angles = 3 personas", 34, GREY, up(t, T["angles"]), w="Bold")
    return img


def t_a2():
    return dict(start=find("bhal", 290.5) - 0.1, end=find("3lih", 312) + 0.4, nefs=find("nefs", 292.4), msg=find("3", 294.4),
                l3yalat=find("l3yalat", 300), rjal=find("rjal", 301.5), kbar=find("kbar", 303), angles=find("angles", 304.4),
                kter=find("kaykhdem", 310), mrkz=find("mrkzin", 311.5))


# ---------- a3 : akfes l7alat ----------
def a3(t, T):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "LE CPA", "CHHAL KAYTQAM 3LIK CLIENT ?")
    ticket(d, t, [(T["p390"], "Prix", "390 $", WHITE), (T["four"], "− Fournisseur", "250 $", RED),
                  (T["m140"], "= Marge", "140 $", WHITE), (T["pub"], "− L'ichhar (1 client)", "120 $", RED),
                  (T["r20"], "= Rbe7", "20 $", GREEN)], y0=170)
    text(d, (510, 820 + 40), "3 900 dh", 30, GREY, 0)  # (réservé)
    # oubli de la pub
    if T["oubli"] <= t < T["pub"]:
        blink = 0.6 + 0.4 * math.sin((t - T["oubli"]) * 9)
        pill(d, 1380, 300, "W l'ichhar ???", RED, BLACK, 40, up(t, T["oubli"]) * blink)
    # CPA
    uc = up(t, T["cpa"])
    if uc > 0:
        card(d, [1000, 230, 1780, 560], uc)
        megaphone(d, 1130, 330, fade(RED, uc), 0.9)
        arrow(d, (1210, 330), (1450, 330), fade(GREY, uc), uc, 6)
        person(d, 1520, 395, 1.0, fade(WHITE, uc))
        pill(d, 1390, 445, "CPA = coût d'acquisition", GREEN, BLACK, 32, uc)
        text(d, (1390, 510), "chhal kaytqam 3lik bach tjib 1 client", 28, GREY, up(t, T["chhal"]), w="Bold")
    # calcul final
    text(d, (1390, 680), "140 $ − 120 $", 70, WHITE, up(t, T["calc"]))
    text(d, (1390, 790), "= 20 $ d rbe7", 70, GREEN, up(t, T["r20"]))
    pill(d, 1390, 900, "F AKFES L7ALAT  (le pire des cas)", GREEN, BLACK, 32, up(t, T["akfes"]))
    return img


def t_a3():
    return dict(start=find("ngoulo", 364.4) - 0.1, end=find("l7alat", 393.5) + 0.4, p390=find("390", 366), four=find("250", 369),
                m140=find("140", 370.5), oubli=find("ba9i", 378), pub=find("120", 382), cpa=find("coût", 384.5),
                chhal=find("chhal", 385.5), calc=find("140", 389.5), r20=find("20", 391.8), akfes=find("akfes", 393))


# ---------- a4 : l'enchère ----------
def a4(t, T):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "L'ENCHERE", "L'ICHHAR = UNE ENCHÈRE")
    L, R = 480, 1440
    # vendeur produit à 60 $
    u = up(t, T["p60"])
    if u > 0:
        person(d, L - 110, 640, 1.4, fade(WHITE, u)); parcel(d, L - 10, 560, 80, fade(BOX, u))
        text(d, (L, 700), "Produit b 60 $", 40, WHITE, u)
        text(d, (L, 760), "Rbe7 : 5 $ / mabi3a", 36, GREEN, up(t, T["r5"]))
        ux = up(t, T["jab"])
        text(d, (L, 830), "Client f l'ichhar : 120 $", 36, RED, ux)
        uk = up(t, T["khaser"])
        if uk > 0:
            text(d, (L, 910), "5 $ − 120 $ = − 115 $", 44, RED, uk)
            pill(d, L, 990, "KHASER", RED, BLACK, 36, uk)
    # nous, produit à 390 $
    u = up(t, T["7na"])
    if u > 0:
        person(d, R - 120, 640, 1.4, fade(WHITE, u)); parcel(d, R - 30, 520, 120, fade(BOX, u))
        text(d, (R, 700), "Produit b 390 $ (7na)", 40, WHITE, u)
        text(d, (R, 760), "Marge : 140 $", 36, GREEN, u)
        text(d, (R, 830), "N9edro nkhlso 120 $ f client", 36, GREEN, up(t, T["7na"] + 0.4))
    # l'enchère : client au centre, marteau, offres
    ue = up(t, T["ench"])
    if ue > 0:
        go = up(t, T["sbe9"], 0.8)
        cx = lerp(W / 2, R + 210, go); cy = lerp(480, 560, go)
        person(d, cx, cy, 1.3, fade(GOLD, ue))
        text(d, (cx, cy - 175), "Client", 30, GOLD, ue)
        ang = (-1.0 + 0.7 * abs(math.sin((t - T["ench"]) * 6))) if t < T["fb"] + 0.6 else -0.6
        hammer(d, W / 2 + 120, 205, fade(WHITE, ue), ang)
        text(d, (W / 2 - 110, 210), "Facebook", 40, BLUE, up(t, T["fb"]))
        ub = up(t, T["fb"] + 0.3, 0.5)
        if go < 0.2:
            arrow(d, (L + 160, 540), (W / 2 - 70, 420), fade(RED, ub), ub, 4); text(d, (L + 260, 420), "5 $", 36, RED, ub)
            arrow(d, (R - 160, 540), (W / 2 + 70, 420), fade(GREEN, ub), ub, 14); text(d, (R - 250, 410), "120 $", 48, GREEN, ub)
        if go > 0.9:
            check(d, R + 290, 400, 26, GREEN)
            text(d, (R, 955), "Kaysbe9 li 9ader ysref kter bach yjib client", 36, WHITE, up(t, T["sbe9"] + 0.3))
    return img


def t_a4():
    return dict(start=find("daba", 400.5) - 0.1, end=find("client", 424.9) + 0.45, p60=find("60", 402), r5=find("5", 408.5),
                jab=find("jab", 412), khaser=find("khaser", 414.5), **{"7na": find("7na", 419)}, ench=find("l'enchère", 421.8) - 0.3,
                fb=find("facebook", 422.3), sbe9=find("kaysbe9", 423))


# ---------- a5 : circuit de l'argent ----------
def a5(t, T):
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    header(d, "LFLOUS", "KIFACH DDKHEL LFLOUS W NTA F L'MAGHRIB ?")
    # 1. carte marocaine : dotation sghira -> stop
    u = up(t, T["cmar"])
    if u > 0:
        dim = 0.35 if t >= T["virt"] else 1.0
        bankcard(d, 330, 330, fade((193, 39, 45), dim), "Carte marocaine", 0.9)
        flag_ma(d, 400, 245, 70, 45)
        text(d, (330, 470), "Dotation", 28, fade(GREY, dim), up(t, T["dot"]), w="Bold")
        ug = up(t, T["dot"])
        d.rounded_rectangle([200, 500, 460, 530], 12, outline=fade(GREY, dim * ug), width=2)
        d.rounded_rectangle([202, 502, 202 + 40 * ug, 528], 10, fill=fade(RED, dim * ug))
        us = up(t, T["stop"])
        if us > 0:
            megaphone(d, 330, 640, fade(GREY, us * dim), 0.8); cross(d, 330, 640, 50, fade(RED, us * dim))
            text(d, (330, 730), "Kattw9ef f l'ichhar", 30, fade(RED, dim), us)
    # 2. carte virtuelle : pub + cashback + illimitée
    u = up(t, T["virt"])
    if u > 0:
        bankcard(d, 960, 330, fade(GREEN, u), "Carte virtuelle", 0.9)
        up_ = up(t, T["pub"], 0.5)
        megaphone(d, 960, 640, fade(GREEN, up_), 0.8); arrow(d, (960, 500), (960, 580), fade(GREEN, up_), up_, 6)
        text(d, (960, 730), "Katkhlles l'ichhar", 30, GREEN, up_)
        uc = up(t, T["cash"], 0.5)
        if uc > 0:
            for i in range(4):
                ph = ((t - T["cash"]) * 0.8 + i * 0.25) % 1
                coin(d, lerp(1060, 1080, ph), lerp(600, 380, ph), 18, GOLD)
            text(d, (1180, 520), "Cashback", 30, GOLD, uc); text(d, (1180, 560), "2 % → 5 %", 30, GOLD, up(t, T["pct"]))
        ui = up(t, T["illim"])
        text(d, (960, 470), "Dotation illimitée", 30, GREEN, ui, w="Bold")
    # 3. flux des ventes : ventes -> banque US -> banque Maroc
    uv = up(t, T["ventes"])
    if uv > 0:
        y = 900
        for i in range(3): parcel(d, 200 + i * 70, y - 50, 56, fade(BOX, uv))
        text(d, (300, y + 50), "Flous lmabi3at", 30, WHITE, uv)
        ua = up(t, T["compte"], 0.5); arrow(d, (440, y - 20), (720, y - 20), fade(WHITE, ua), ua, 7)
        ub = up(t, T["mirikan"])
        if ub > 0:
            bank(d, 900, y - 20, fade(WHITE, ub), 0.75); flag_us(d, 990, y - 125, 80, 50)
            text(d, (900, y + 70), "Compte f Mirikan", 30, WHITE, ub)
            text(d, (900, y + 108), "kan7elloh m3ak", 26, GREY, up(t, T["ens"]), w="Bold")
        ur = up(t, T["traj3"], 0.5); arrow(d, (1080, y - 20), (1380, y - 20), fade(GREEN, ur), ur, 7)
        um = up(t, T["maghrib"])
        if um > 0:
            bank(d, 1560, y - 20, fade(GREEN, um), 0.75); flag_ma(d, 1650, y - 125, 80, 50)
            text(d, (1560, y + 70), "Compte f l'Maghrib", 30, GREEN, um)
    return img


def t_a5():
    return dict(start=find("sara7a", 438.3) - 0.1, end=find("l'maghrib", 463.5) + 0.45, cmar=find("marocaine", 439),
                dot=find("dotation", 439.7), stop=find("tw9ef", 441.5), virt=find("virtuelles", 446.8) - 0.2, pub=find("katkhlles", 448.3),
                cash=find("cashback", 450), pct=find("2 %", 452), illim=find("illimitée", 455.5), ventes=find("flous", 456.5),
                compte=find("compte", 457.3), mirikan=find("mirikan", 459.8), ens=find("ensemble", 460.8), traj3=find("traj3ha", 462.5),
                maghrib=find("l'maghrib", 463.5))


SCENES = {"a1": (a1, t_a1), "a2": (a2, t_a2), "a3": (a3, t_a3), "a4": (a4, t_a4), "a5": (a5, t_a5)}


def frame(name, t):
    fn, tf = SCENES[name]; T = tf()
    img = fn(t, T)
    a = min(1, (t - T["start"]) / 0.25, (T["end"] - t) / 0.25)
    return img if a >= 1 else Image.blend(Image.new("RGB", (W, H)), img, max(a, 0))


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] in SCENES and args[1].replace(".", "").isdigit():
        frame(args[0], float(args[1])).save(args[2] if len(args) > 2 else D + "anim_test.png"); sys.exit()
    wins = {}
    try: wins = json.load(open(D + "anim5_windows.json"))
    except FileNotFoundError: pass
    for name in (args or list(SCENES)):
        fn, tf = SCENES[name]; T = tf()
        out = D + f"slides/{name}.mov"
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
        for k in range(int((T["end"] - T["start"]) * FPS)):
            t = T["start"] + k / FPS
            img = fn(t, T); a = min(1, (t - T["start"]) / 0.25, (T["end"] - t) / 0.25)
            if a < 1: img = Image.blend(Image.new("RGB", (W, H)), img, max(a, 0))
            p.stdin.write(img.tobytes())
        p.stdin.close(); p.wait()
        wins[name] = [round(T["start"], 3), round(T["end"], 3)]
        print(name, wins[name])
    json.dump(wins, open(D + "anim5_windows.json", "w"))
