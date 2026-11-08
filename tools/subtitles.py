#!/usr/bin/env python3
"""Génère des sous-titres ASS style short (2-4 mots, mot actif surligné).

Usage: subtitles.py <words.json> <sortie.ass> [--timemap cut.mp4.timemap.json]
       [--style style/style.json] [--w 1080 --h 1920]

- words.json = sortie de transcribe.py (temps de la source).
- --timemap = sortie de cut.py : remappe les mots sur la timeline montée et
  supprime les mots coupés.
- style.json (optionnel) surcharge: font, size, color, highlight, outline, y (0-1), max_words, uppercase.
"""
import argparse
import json
import sys

DEFAULT = {"font": "Montserrat ExtraBold", "size": 84, "color": "FFFFFF", "highlight": "FF2BD6",
           "outline": 6, "y": 0.62, "max_words": 3, "uppercase": True, "max_gap": 0.35}


def ass_color(hex_rgb: str) -> str:
    h = hex_rgb.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ts(t: float) -> str:
    t = max(0.0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def remap(words, timemap):
    if not timemap:
        return words
    out = []
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        for r in timemap["ranges"]:
            if r["src_start"] <= mid <= r["src_end"]:
                off = r["dst_start"] - r["src_start"]
                out.append({**w, "start": max(r["dst_start"], w["start"] + off),
                            "end": min(r["dst_start"] + r["src_end"] - r["src_start"], w["end"] + off)})
                break
    return out


def group(words, n, max_gap):
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= n or w["start"] - cur[-1]["end"] > max_gap
                    or cur[-1]["w"].endswith((".", "!", "?", ","))):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("out")
    ap.add_argument("--timemap")
    ap.add_argument("--style")
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    a = ap.parse_args()
    st = dict(DEFAULT)
    if a.style:
        user = json.load(open(a.style))
        st.update(user.get("subtitles", user))  # accepte style/style.json entier ou juste la partie sous-titres

    words = json.load(open(a.words))["words"]
    tm = json.load(open(a.timemap)) if a.timemap else None
    words = [w for w in remap(words, tm) if w["w"]]

    margin_v = int(a.h * (1 - st["y"]))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {a.w}
PlayResY: {a.h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{st['font']},{st['size']},{ass_color(st['color'])},&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{st['outline']},2,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    hi = ass_color(st["highlight"])
    base = ass_color(st["color"])
    for g in group(words, st["max_words"], st["max_gap"]):
        for i, w in enumerate(g):
            start = w["start"]
            end = g[i + 1]["start"] if i + 1 < len(g) else g[-1]["end"]
            txt = []
            for j, x in enumerate(g):
                t = x["w"].upper() if st["uppercase"] else x["w"]
                t = t.replace("{", "(").replace("}", ")")
                if j == i:
                    txt.append(r"{\c" + hi + r"&\fscx108\fscy108}" + t + r"{\c" + base + r"&\fscx100\fscy100}")
                else:
                    txt.append(t)
            pop = r"{\t(0,80,\fscx104\fscy104)\t(80,160,\fscx100\fscy100)}" if i == 0 else ""
            lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{pop}{' '.join(txt)}")
    open(a.out, "w").write(head + "\n".join(lines) + "\n")
    print(f"{len(lines)} événements de sous-titres -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
