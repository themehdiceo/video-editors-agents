#!/usr/bin/env python3
"""Textes animés à l'écran (titres, chiffres clés, questions-choc) façon VSL, en ASS : rapide, net, sans navigateur.

Usage: titles.py <cartes.json> <sortie.ass> [--w 1920 --h 1080] [--style style/interview-v1/style.json]

cartes.json : liste de cartes (temps sur la timeline montée)
[
  {"at": 0.4, "dur": 2.6, "text": "Salarié à **12 000 DH** | par mois", "pos": "top"},
  {"at": 3.2, "dur": 2.2, "count": {"to": 60000, "prefix": "", "suffix": " $ / MOIS"}, "pos": "center"},
  {"at": 6.0, "dur": 2.5, "text": "Comment t'as quitté le salariat ?", "pos": "lower", "box": true}
]
- **mot** : mot-clé en couleur (highlight), italique, plus gros. « | » = retour à la ligne.
- pos : top | center | lower (bas, au-dessus des sous-titres) | left | right (côté d'un des deux visages).
- box : bandeau sombre derrière le texte (lisible sur n'importe quelle image).
- count : chiffre qui défile de from (0) à to en 0,8 s, puis reste affiché.
- size : taille de police (défaut 104 en 1080p, 150 pour un count).
Animation : entrée floue + petit rebond (0,25 s), sortie en fondu (0,15 s).
Ajoute le fichier dans plan.json : "titles": "work/titles.ass" (compose.py l'incruste au-dessus des sous-titres).
"""
import argparse
import json
import re
import sys

POS = {  # alignement ASS (numpad) et position relative (x, y)
    "top": (8, 0.5, 0.10), "center": (5, 0.5, 0.45), "lower": (2, 0.5, 0.70),
    "left": (5, 0.25, 0.30), "right": (5, 0.75, 0.30),
}


def ass_color(h):
    h = h.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ts(t):
    t = max(0.0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def rich(text, base, hi, ks):
    """**mot** -> mot-clé coloré, italique, agrandi. | -> retour à la ligne."""
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text.replace("{", "(").replace("}", ")"))):
        if i % 2:
            out.append(r"{\c" + hi + r"&\i1\fscx" + str(ks) + r"\fscy" + str(ks) + "}" + part +
                       r"{\c" + base + r"&\i0\fscx100\fscy100}")
        else:
            out.append(part)
    return "".join(out).replace(" | ", r"\N").replace("|", r"\N")


def fmt_num(n):
    return f"{int(round(n)):,}".replace(",", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1920)
    ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--style")
    a = ap.parse_args()
    st = {"font": "Montserrat Black", "color": "FFFFFF", "highlight": "FFD400", "keyword_scale": 1.25}
    if a.style:
        sub = json.load(open(a.style)).get("subtitles", {})
        st.update({k: sub[k] for k in ("color", "highlight") if k in sub})
        if "titles" in json.load(open(a.style)):
            st.update(json.load(open(a.style))["titles"])
    k = a.h / 1080
    base, hi = ass_color(st["color"]), ass_color(st["highlight"])
    ks = int(100 * st["keyword_scale"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {a.w}
PlayResY: {a.h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: T,{st['font']},{int(92 * k)},{base},&H000000FF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,{max(2, int(5 * k))},{max(1, int(3 * k))},5,40,40,40,1
Style: B,{st['font']},{int(92 * k)},{base},&H000000FF,&H50000000,&H50000000,-1,0,0,0,100,100,0,0,4,{max(8, int(22 * k))},0,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for c in json.load(open(a.cards)):
        at, dur = float(c["at"]), float(c.get("dur", 2.5))
        al, rx, ry = POS.get(c.get("pos", "center"), POS["center"])
        if "y" in c:  # position verticale libre (0-1), texte centré : pour cacher une zone précise
            al, ry = 5, float(c["y"])
        x, y = int(rx * a.w), int(ry * a.h)
        style = "B" if c.get("box") else "T"
        size = int(c.get("size", 150 if "count" in c else 104) * k)
        anim = (r"\an" + str(al) + rf"\pos({x},{y})\fs{size}\blur10\alpha&HFF&\fscx82\fscy82"
                r"\t(0,250,\blur0\alpha&H00&\fscx104\fscy104)\t(250,380,\fscx100\fscy100)"
                + rf"\fad(0,150)")
        if c.get("label"):  # étiquette verte au-dessus + filet vert qui s'ouvre sous le texte (design « question »)
            lab_y = y - int(0.075 * a.h)
            ev.append(f"Dialogue: 2,{ts(at)},{ts(at + dur)},T,,0,0,0,,{{\\an8\\pos({x},{lab_y})\\fs{int(34 * k)}\\fsp{int(9 * k)}"
                      f"\\c{hi}&\\bord0\\shad0\\alpha&HFF&\\t(0,200,\\alpha&H00&)\\fad(0,150)}}{c['label']}")
            ly, hw = y + int(size * 1.55), int(150 * k)
            ev.append(f"Dialogue: 2,{ts(at + 0.15)},{ts(at + dur)},T,,0,0,0,,{{\\an5\\pos({x},{ly})\\c{hi}&\\bord0\\shad0"
                      f"\\p1\\fscx10\\t(0,350,\\fscx100)\\fad(0,150)}}m {-hw} 0 l {hw} 0 {hw} {max(4, int(7 * k))} {-hw} {max(4, int(7 * k))}{{\\p0}}")
        if "count" in c:
            cnt = c["count"]
            n0, n1 = float(cnt.get("from", 0)), float(cnt["to"])
            steps, ramp = 24, 0.8
            for i in range(steps + 1):
                t0 = at + ramp * i / steps
                t1 = at + ramp * (i + 1) / steps if i < steps else at + dur
                e = 1 - (1 - i / steps) ** 3  # ralentit à la fin
                val = cnt.get("prefix", "") + "**" + fmt_num(n0 + (n1 - n0) * e) + "**" + cnt.get("suffix", "")
                a_ = anim if i == 0 else rf"\an{al}\pos({x},{y})\fs{size}" + (r"\fad(0,150)" if i == steps else "")
                ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},{style},,0,0,0,,{{{a_}}}{rich(val, base, hi, ks)}")
        else:
            ev.append(f"Dialogue: 1,{ts(at)},{ts(at + dur)},{style},,0,0,0,,{{{anim}}}{rich(c['text'], base, hi, ks)}")
    open(a.out, "w").write(head + "\n".join(ev) + "\n")
    print(f"{len(ev)} événements de titres -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
