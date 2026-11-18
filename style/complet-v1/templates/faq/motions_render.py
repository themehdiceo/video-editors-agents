#!/usr/bin/env python3
"""Motions vsl-v1 : petite carte blanche, texte noir Plus Jakarta Sans 800, touche verte #D0FE16.
Chaque ligne apparaît sur son mot (motions_timed.json). Carte placée du côté opposé au visage (détection OpenCV).
Sortie : work/motions/mNN.mov (qtrle, alpha) + entrées "overlays" dans plan.json (coordonnées 1080p)."""
import json, os, subprocess, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

D = "jobs/20261118-062812-edit/work/"
FONT = "assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS = 1920, 1080, 30
GREEN, BLACK, WHITE = (208, 254, 22, 255), (0, 0, 0, 255), (255, 255, 255, 255)
PAD, RAD, GAP, MAXW = 40, 28, 14, 640
os.makedirs(D + "motions", exist_ok=True)

def font(sz, w="ExtraBold"):
    f = ImageFont.truetype(FONT, sz)
    try: f.set_variation_by_name(w)
    except Exception: pass
    return f

def wrap(txt, f, maxw):
    import re
    txt = re.sub(r" ([?»%$:])", "\u00a0\\1", txt).replace("« ", "«\u00a0")
    txt = re.sub(r"(\d) (\d{3})", "\\1\u00a0\\2", txt)
    words, lines, cur = txt.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def face_x(t):
    cap = cv2.VideoCapture(D + "aroll_cut.mp4"); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read(); cap.release()
    if not ok: return None
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    fs = det.detectMultiScale(g, 1.1, 6, minSize=(150, 150))
    if not len(fs): return None
    x, y, w, h = max(fs, key=lambda r: r[2] * r[3]); return (x + w / 2, y, w, h)

M = json.load(open(D + "motions_timed.json"))
plan = json.load(open(D + "plan.json")); plan["overlays"] = []
report = []
for i, m in enumerate(M):
    single = len(m["lines"]) == 1
    fl, fk = font(54 if single else 46), font(24, "Bold")
    # mise en page
    rows = []  # (texte, police, idx_ligne)
    for j, (txt, *_r) in enumerate(m["lines"]):
        for part in wrap(txt, fl, MAXW - 2 * PAD): rows.append((part, j))
    lh = int(fl.size * 1.25)
    kh = 44 if m["kick"] else 0
    tw = max([fl.getlength(r[0]) for r in rows] + [fk.getlength(m["kick"]) + 40 if m["kick"] else 0])
    cw, ch = int(tw + 2 * PAD), int(PAD * 2 + kh + (GAP if kh else 0) + lh * len(rows))
    t0, tl = m["t"][0], m["t"][-1]
    nxt = M[i + 1]["t"][0] if i + 1 < len(M) else plan_dur if (plan_dur := json.load(open(D + "aroll_cut.mp4.timemap.json"))["duration"]) else 1e9
    t_end = min(tl + (3.2 if single else 3.0), nxt - (1.0 if i + 1 < len(M) else 0.05))
    t_in = max(t0 - 0.15, 0); dur = t_end - t_in
    # côté opposé au visage
    # visage repéré sur la planche work/faces.jpg : centre vers 0,45-0,49 de la largeur, sauf 23-24 (0,51-0,53)
    fx = None
    side = "left" if i + 1 in (23, 24) else "right"
    x = W - cw - 110 if side == "right" else 110
    y = int(H * 0.47 - ch / 2)
    overlap = fx is not None and (x < fx[0] + fx[2] / 2 + 40 and x + cw > fx[0] - fx[2] / 2 - 40)
    report.append((i + 1, round(t_in, 2), round(dur, 2), side, None if fx is None else int(fx[0]), overlap))
    # rendu image par image
    out = D + f"motions/m{i + 1:02d}.mov"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{cw + 40}x{ch + 40}",
                          "-r", str(FPS), "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    n = int(dur * FPS)
    ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
    for k in range(n):
        t = t_in + k / FPS
        a_in, a_out = ease((t - t_in) / 0.3), min(1, max(0, (t_end - t) / 0.25))
        alpha = a_in * a_out
        img = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, cw - 1, ch - 1], RAD, fill=WHITE)
        yy = PAD
        if kh:
            kw = int(fk.getlength(m["kick"]) + 32)
            d.rounded_rectangle([PAD, yy, PAD + kw, yy + 40], 20, fill=GREEN)
            d.text((PAD + 16, yy + 20), m["kick"], font=fk, fill=BLACK, anchor="lm")
            yy += kh + GAP
        for txt, j in rows:
            u = ease((t - m["t"][j]) / 0.32) if j else ease((t - t_in) / 0.3)
            if u > 0:
                layer = Image.new("RGBA", (cw, lh), (0, 0, 0, 0))
                ImageDraw.Draw(layer).text((PAD, lh / 2 + 26 * (1 - u)), txt, font=fl, fill=BLACK, anchor="lm")
                a = layer.getchannel("A").point(lambda v: int(v * u)); layer.putalpha(a)
                card.alpha_composite(layer, (0, yy))
            yy += lh
        img.alpha_composite(card, (20, 20 + int(26 * (1 - a_in))))
        if alpha < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * alpha)))
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    plan["overlays"].append({"file": f"work/motions/m{i + 1:02d}.mov", "at": round(t_in, 3), "dur": round(dur, 3),
                             "x": x - 20, "y": y - 20})
json.dump(plan, open(D + "plan.json", "w"), indent=1, ensure_ascii=False)
for r in report: print(*r)
