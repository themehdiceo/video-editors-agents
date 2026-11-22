"""Petits films schématiques 9:16 (style « montagne » validé : noir, bonshommes qui bougent, Plus Jakarta Sans 800, vert #D0FE16).
Mehdi 20/11 : des personnages qui bougent, pas des slides de texte ; pub courte = 2-3 animations de ~3-4 s.
render(kind, dur, marks, kick, lines, out)  marks = {nom: s depuis le début}, lines = [("texte *vert*", s), ...]
kinds : guru (vend la formation puis laisse le gars seul), deal (on monte ensemble, % partagé, win-win),
        balance (lflous vs lwe9t), cross (panneaux contradictoires, ?), train (lfourssa part, la foule court)."""
import math, re, subprocess
from PIL import Image, ImageDraw, ImageFont
FONT = "/Users/pro/video-editors-agents/assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS, S = 1080, 1920, 30, 2
GREEN, WHITE, GREY, RED, DARKC = (208, 254, 22, 255), (255, 255, 255, 255), (163, 163, 163, 255), (255, 77, 77, 255), (13, 13, 13, 255)
BLACK = (0, 0, 0, 255)


def font(sz, w="ExtraBold"):
    f = ImageFont.truetype(FONT, int(sz * S)); f.set_variation_by_name(w); return f


FL, FK, FP, FBIG = font(54), font(30, "Bold"), font(34), font(90)
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
lerp = lambda a, b, u: a + (b - a) * u
P = lambda *pts: [(x * S, y * S) for x, y in pts]


def fig(d, x, y, t, walk=False, arms="down", col=WHITE, k=1.6, face=1):
    """Bonhomme, pieds en (x, y). arms : down / up / out / hold / scratch."""
    ph = math.sin(t * 11) if walk else 0
    Q = lambda *pts: [((x + (px - x) * k) * S, (y + (py - y) * k) * S) for px, py in pts]
    hip, neck, head = (x, y - 42), (x, y - 82), (x, y - 100)
    for s in (1, -1):
        d.line(Q(hip, (x + 12 * ph * s, y)), fill=col, width=int(7 * k * S))
    A = {"down": [(x + 10 + 8 * ph, y - 48), (x - 10 - 8 * ph, y - 48)], "up": [(x + 18, y - 128), (x - 18, y - 128)],
         "out": [(x + 34, y - 74), (x - 34, y - 74)], "hold": [(x + 30 * face, y - 64), (x + 26 * face, y - 60)],
         "scratch": [(x + 4, y - 112), (x - 12, y - 50)]}[arms]
    for a in A: d.line(Q(neck, a), fill=col, width=int(6 * k * S))
    d.line(Q(hip, neck), fill=col, width=int(8 * k * S))
    d.ellipse(Q((head[0] - 14, head[1] - 14), (head[0] + 14, head[1] + 14)), fill=col)


def pill(d, cx, cy, txt, bg, fg, u=1.0, f=FP):
    tw = f.getlength(txt) / S; w, h = tw + 40, f.size / S + 22
    y0 = cy - h / 2 + 14 * (1 - u)
    d.rounded_rectangle(P((cx - w / 2, y0), (cx + w / 2, y0 + h)), h / 2 * S, fill=bg)
    d.text((cx * S, (y0 + h / 2) * S), txt, font=f, fill=fg, anchor="mm")


def card_lines(img, lines, t, y=1470):
    for txt, tt in lines:
        u = ease((t - tt) / 0.3)
        if u > 0:
            sg = [(p, i % 2 == 1) for i, p in enumerate(re.split(r"\*", txt)) if p]
            fl = FL
            while sum(fl.getlength(p) for p, _ in sg) / S > 900: fl = font(fl.size / S - 4)
            wl = sum(fl.getlength(p) for p, _ in sg) / S; cw, rh = wl + 80, 112
            lay = Image.new("RGBA", (int(cw * S), rh * S), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([0, 0, cw * S - 1, rh * S - 1], 28 * S, fill=DARKC, outline=(38, 38, 38, 255), width=2 * S)
            x = 40
            for p, g in sg:
                ld.text((x * S, rh / 2 * S), p, font=fl, fill=GREEN if g else WHITE, anchor="lm"); x += fl.getlength(p) / S
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * u)))
            img.alpha_composite(lay, (int((W - cw) / 2 * S), int((y + 24 * (1 - u)) * S)))
        y += 130


def ground(d, y=1250): d.line(P((90, y), (990, y)), fill=(60, 60, 60, 255), width=3 * S)


# ---------- scènes ----------
def guru(d, img, t, M):
    ground(d)
    # estrade du gourou
    d.rounded_rectangle(P((130, 1130), (400, 1250)), 12 * S, fill=(30, 30, 30, 255))
    d.text((265 * S, 1190 * S), "GOUROU", font=FK, fill=GREY, anchor="mm")
    sell, alone = M.get("sell", 0.8), M.get("alone", 2.2)
    gx = 265 if t < alone else lerp(265, -120, ease((t - alone) / 1.0))
    fig(d, gx, 1130, t, walk=t >= alone, arms="out" if t < sell else "hold", col=GREEN, face=1)
    if t >= alone:  # il part avec le sac d'argent
        d.ellipse(P((gx + 30, 1020), (gx + 80, 1070)), fill=GREEN); d.text(((gx + 55) * S, 1046 * S), "$", font=FP, fill=BLACK, anchor="mm")
    # la boîte FORMATION : chez le gourou, puis vole vers l'élève
    u = ease((t - sell) / 0.6)
    bx, by = lerp(gx + 60, 690, u), lerp(1000, 1060, u) - 140 * math.sin(math.pi * u)
    d.rounded_rectangle(P((bx - 105, by - 42), (bx + 105, by + 42)), 12 * S, fill=WHITE)
    d.text((bx * S, by * S), "FORMATION", font=font(28), fill=BLACK, anchor="mm")
    # l'élève : paye, reçoit, puis reste seul, perdu
    fig(d, 820, 1250, t, arms="hold" if t >= sell + 0.6 else "out", face=-1)
    if t >= alone + 0.3:
        for i, ch in enumerate("???"):
            ua = ease((t - alone - 0.3 - 0.15 * i) / 0.3)
            d.text(((790 + 34 * i) * S, (960 - 30 * ua - 18 * i) * S), ch, font=FBIG, fill=(255, 255, 255, int(255 * ua)), anchor="mm")
        pill(d, 820, 820, "BO7DEK", RED, WHITE, ease((t - alone - 0.6) / 0.3))


def deal(d, img, t, M):
    ground(d)
    # escalier des ventes qui pousse sous leurs pieds
    grow = ease((t - M.get("sales", 0.3)) / 1.6)
    steps = [(200 + 120 * i, 1250 - 70 * (i + 1) * grow) for i in range(6)]
    for x, y in steps:
        d.rectangle(P((x, y), (x + 116, 1250)), fill=(24, 24, 24, 255), outline=(60, 60, 60, 255), width=2 * S)
    d.text((540 * S, 1300 * S), "LMABI3AT", font=FK, fill=GREY, anchor="mm")
    pos = ease((t - M.get("sales", 0.3)) / 1.8) * 5
    i = min(int(pos), 5); fx = 258 + 120 * pos; fy = steps[i][1]
    win = t >= M.get("win", 2.4)
    fig(d, fx - 40, fy, t, walk=not win and pos < 5, arms="up" if win else "down", col=WHITE)
    fig(d, fx + 30, fy, t + 0.3, walk=not win and pos < 5, arms="up" if win else "down", col=GREEN)
    pill(d, fx - 40, fy - 250, "NTA", DARKC, WHITE); pill(d, fx + 30, fy - 330, "ANA", GREEN, BLACK)
    up = ease((t - M.get("pct", 1.2)) / 0.4)
    if up > 0:
        pill(d, 540, 700, "Nakhod 10 % mn l'arba7", DARKC, GREEN, up)
    if win:
        uw = ease((t - M.get("win", 2.4)) / 0.35)
        pill(d, 540, 560, "WIN-WIN", GREEN, BLACK, uw, f=font(60))


def balance(d, img, t, M):
    tilt = ease((t - M.get("tilt", 0.8)) / 0.7)
    ang = math.radians(lerp(-10, 14, tilt))  # penche vers LWE9T (droite)
    cx, cy, L = 540, 820, 330
    d.polygon(P((cx, cy), (cx - 70, 1250), (cx + 70, 1250)), fill=(40, 40, 40, 255))
    ex, ey = L * math.cos(ang), L * math.sin(ang)
    d.line(P((cx - ex, cy - ey), (cx + ex, cy + ey)), fill=WHITE, width=8 * S)
    for sx, lab, col in ((-1, "LFLOUS", WHITE), (1, "LWE9T", GREEN)):
        px, py = cx + sx * ex, cy + sx * ey
        d.line(P((px, py), (px - 70, py + 160)), fill=GREY, width=3 * S); d.line(P((px, py), (px + 70, py + 160)), fill=GREY, width=3 * S)
        d.arc(P((px - 90, py + 110), (px + 90, py + 210)), 0, 180, fill=GREY, width=5 * S)
        if sx < 0:
            for k in range(4): d.ellipse(P((px - 45 + 22 * k, py + 120 - 6 * k), (px - 5 + 22 * k, py + 150 - 6 * k)), fill=(230, 230, 230, 255))
        else:  # horloge dont l'aiguille tourne
            d.ellipse(P((px - 50, py + 60), (px + 50, py + 160)), outline=GREEN, width=6 * S)
            a = t * 6; d.line(P((px, py + 110), (px + 38 * math.sin(a), py + 110 - 38 * math.cos(a))), fill=GREEN, width=5 * S)
        pill(d, px, py - 70, lab, GREEN if sx > 0 else DARKC, BLACK if sx > 0 else WHITE)
    fig(d, 180, 1250, t, arms="up" if t >= M.get("tilt", 0.8) + 0.7 else "down", col=GREEN)


def cross(d, img, t, M):
    ground(d)
    d.line(P((540, 1250), (540, 760)), fill=(110, 110, 110, 255), width=10 * S)
    signs = [("BDA HADA", -1, 820, M.get("a", 0.3)), ("LA, HADA 7SEN", 1, 930, M.get("b", 1.2)), ("HADA AHSAN", -1, 1040, M.get("c", 1.9))]
    for txt, sx, y, tt in signs:
        u = ease((t - tt) / 0.35)
        if u <= 0: continue
        w = FP.getlength(txt) / S + 70; x0 = 540 if sx > 0 else 540 - w
        tip = x0 + w + 40 if sx > 0 else x0 - 40
        poly = [(x0, y - 38), (x0 + w, y - 38), (tip if sx > 0 else x0 + w, y), (x0 + w, y + 38), (x0, y + 38), (x0 if sx > 0 else tip, y)]
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.polygon(P(*poly), fill=DARKC, outline=GREY, width=3 * S)
        ld.text(((x0 + w / 2) * S, y * S), txt, font=FP, fill=WHITE, anchor="mm")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * u))); img.alpha_composite(lay)
    d = ImageDraw.Draw(img)
    look = math.sin(t * 5)  # il tourne la tête dans tous les sens
    fig(d, 880 + 10 * look, 1250, t, arms="scratch", face=1 if look > 0 else -1)
    lost = ease((t - M.get("lost", 2.3)) / 0.3)
    if lost > 0: d.text((880 * S, (1010 - 20 * lost) * S), "?", font=font(130), fill=(208, 254, 22, int(255 * lost)), anchor="mm")
    return d


def train(d, img, t, M):
    ground(d, 1200)
    d.rectangle(P((0, 1200), (W, 1260)), fill=(28, 28, 28, 255))
    go = M.get("go", 1.0)
    tx = 240 + 1600 * ease((t - go) / 1.6) ** 1.6
    for c in range(3):  # wagons
        x = tx + 330 * c - 300
        d.rounded_rectangle(P((x, 960), (x + 310, 1180)), 22 * S, fill=(45, 45, 45, 255), outline=GREEN, width=4 * S)
        for wi in range(3): d.rectangle(P((x + 25 + 95 * wi, 995), (x + 95 + 95 * wi, 1060)), fill=(90, 90, 90, 255))
        for wx in (x + 60, x + 250): d.ellipse(P((wx - 26, 1162), (wx + 26, 1214)), fill=(20, 20, 20, 255), outline=GREY, width=3 * S)
    pill(d, tx + 200, 900, "LFOURSSA", GREEN, BLACK)
    # la foule qui arrive trop tard
    for i in range(5):
        fx = lerp(-80 - 90 * i, 420 - 70 * i, ease((t - 0.2 - 0.12 * i) / 1.8))
        fig(d, fx, 1200, t + i, walk=True, col=WHITE if i else GREEN, k=1.25)
    late = ease((t - M.get("late", 2.2)) / 0.3)
    if late > 0: pill(d, 300, 760, "KOULCHI HDER 3LIH", RED, WHITE, late)


SCENES = {"guru": guru, "deal": deal, "balance": balance, "cross": cross, "train": train}


def render(kind, dur, marks, kick, lines, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        t = k / FPS
        img = Image.new("RGBA", (W * S, H * S), BLACK); d = ImageDraw.Draw(img)
        d.rectangle(P((90, 378), (90 + 44 * ease(t / 0.3), 382)), fill=GREEN)
        d.text((150 * S, 380 * S), " ".join(kick.upper()), font=FK, fill=GREY, anchor="lm")
        SCENES[kind](d, img, t, marks)
        card_lines(img, lines, t)
        img = img.resize((W, H), Image.LANCZOS)
        a = min(1, t / 0.2, (dur - t) / 0.2)
        if a < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * max(a, 0))))
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    return out


if __name__ == "__main__":  # aperçu : anim9.py guru 2.5 out.png
    import sys
    kind, t = sys.argv[1], float(sys.argv[2])
    img = Image.new("RGBA", (W * S, H * S), BLACK); d = ImageDraw.Draw(img)
    SCENES[kind](d, img, t, {}); card_lines(img, [("Exemple *vert*", 0)], t)
    img.resize((W // 2, H // 2), Image.LANCZOS).save(sys.argv[3])
