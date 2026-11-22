"""Écran noir animé 9:16 (style slides montage complet v1, même look que l'écran de fin) : surtitre gris espacé + trait vert,
cartes #0d0d0d qui arrivent chacune sur son mot, mots-clés *verts*. Fondu 0,25 s entrée/sortie. Sa voix continue dessous.
render(kick, lines, times, dur, out) ; lines = ["texte *vert*", ...], times = secondes depuis le début de l'écran."""
import re, subprocess
from PIL import Image, ImageDraw, ImageFont
FONT = "/Users/pro/video-editors-agents/assets/fonts/PlusJakartaSans[wght].ttf"
W, H, FPS = 1080, 1920, 30
GREEN, WHITE, GREY = (208, 254, 22, 255), (255, 255, 255, 255), (163, 163, 163, 255)


def font(sz, w="ExtraBold"):
    f = ImageFont.truetype(FONT, sz); f.set_variation_by_name(w); return f


FL, FK = font(60), font(32, "Bold")
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3


def render(kick, lines, times, dur, out):
    segs = [[(p, i % 2 == 1) for i, p in enumerate(re.split(r"\*", l)) if p] for l in lines]
    fl = FL
    while max(sum(fl.getlength(p) for p, _ in s) for s in segs) > 880: fl = font(fl.size - 4)
    cw, rh, gap = 960, 130, 26
    x0 = (W - cw) // 2
    y0 = (H - (70 + len(lines) * (rh + gap))) // 2 - 40
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for k in range(int(dur * FPS)):
        t = k / FPS
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
        u = ease(t / 0.3)
        d.rectangle([x0, y0 - 2, x0 + int(44 * u), y0 + 2], fill=GREEN)
        d.text((x0 + 60, y0), " ".join(kick.upper()), font=FK, fill=GREY, anchor="lm")
        y = y0 + 70
        for sg, t0 in zip(segs, times):
            u = ease((t - t0) / 0.32)
            if u > 0:
                lay = Image.new("RGBA", (cw, rh), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                ld.rounded_rectangle([0, 0, cw - 1, rh - 1], 28, fill=(13, 13, 13, 255), outline=(38, 38, 38, 255), width=2)
                x = 44
                for txt, g in sg:
                    ld.text((x, rh / 2), txt, font=fl, fill=GREEN if g else WHITE, anchor="lm"); x += fl.getlength(txt)
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * u)))
                img.alpha_composite(lay, (x0, int(y + 26 * (1 - u))))
            y += rh + gap
        a = min(1, t / 0.25, (dur - t) / 0.25)
        if a < 1: img.putalpha(img.getchannel("A").point(lambda v: int(v * max(a, 0))))
        p.stdin.write(img.tobytes())
    p.stdin.close(); p.wait()
    return out
