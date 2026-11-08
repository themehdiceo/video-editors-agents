#!/usr/bin/env python3
"""Monte un hook d'interview (extraits de la source Meet, plein écran A/M ou split, sous-titres, textes animés, noir final).

Usage: hook_build.py <work/plan.json> [--final]
Brouillon 480p par défaut -> out/final.mp4 ; --final = 1080p -> out/final_1080.mp4.

plan.json (type hook_interview) : voir jobs/*/work/plan.json
- tiles : zone (x, y, w, h) de chaque visage dans la source ; face_x = position du visage dans la tuile (0-1).
- shots[] : layout "A" | "M" (plein écran, tuile entière sur fond flou : jamais de zoom) | "split" (A à gauche, M à droite),
  ranges (temps source, coupes sur des limites de mots), text (une liste de mots par range, darija latine),
  k (index des mots-clés rouges, comptés sur tout le shot), cards (textes animés, off = décalage dans le shot).
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAD_IN, PAD_OUT = 0.03, 0.03


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(" ".join(cmd[:6]), "...\n", r.stderr[-1500:])
        sys.exit(1)
    return r


def main():
    final = "--final" in sys.argv[2:]
    plan_path = os.path.abspath(sys.argv[1])
    plan = json.load(open(plan_path))
    work = os.path.dirname(plan_path)
    job = os.path.dirname(work)
    src = os.path.join(job, plan["source"])
    FW, FH, FPS = plan["format"]["w"], plan["format"]["h"], plan["format"]["fps"]
    k = 1.0 if final else 480 / FH
    W, H = int(FW * k) // 2 * 2, int(FH * k) // 2 * 2
    tiles = plan["tiles"]
    seg_dir = os.path.join(work, "seg" + ("_final" if final else ""))
    os.makedirs(seg_dir, exist_ok=True)

    words, cards, segs = [], [], []
    t = 0.0
    for si, sh in enumerate(plan["shots"]):
        shot_t0 = t
        flat = 0
        for ri, (s, e) in enumerate(sh["ranges"]):
            d = round(e - s + PAD_IN + PAD_OUT, 3)
            lay = sh["layout"]
            if lay == "split":
                a, m = tiles["A"], tiles["M"]

                def crop(tl):
                    cw = min(tl["w"], int(tl["h"] * (W / 2) / H))
                    cx = tl["x"] + int((tl["w"] - cw) * tl["face_x"])
                    return f"crop={cw}:{tl['h']}:{cx}:{tl['y']}"
                vf = (f"[0:v]split=2[p][q];[p]{crop(a)},scale={W // 2}:{H},setsar=1[l];"
                      f"[q]{crop(m)},scale={W // 2}:{H},setsar=1[r];[l][r]hstack,fps={FPS}[v]")
            else:
                tl = tiles[lay]
                vf = (f"[0:v]crop={tl['w']}:{tl['h']}:{tl['x']}:{tl['y']},split=2[a][b];"
                      f"[b]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:6,eq=brightness=-0.2[bg];"
                      f"[a]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1,fps={FPS}[v]")
            out = os.path.join(seg_dir, f"s{si:02d}_{ri}.mp4")
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s - PAD_IN:.3f}", "-t", f"{d}", "-i", src,
                 "-filter_complex", vf, "-map", "[v]", "-map", "0:a:0",
                 "-af", f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03,aresample=48000",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
            segs.append(out)
            toks = sh["text"][ri]
            n = len(toks)
            for j, w in enumerate(toks):
                ws = t + PAD_IN + (e - s) * j / n
                we = t + PAD_IN + (e - s) * (j + 1) / n
                wd = {"w": w, "start": round(ws, 3), "end": round(we, 3)}
                if j == n - 1:
                    wd["br"] = True  # fin d'extrait : la phrase suivante repart de zéro
                if (flat + j) in sh.get("k", []):
                    wd["k"] = True
                words.append(wd)
            flat += n
            t += d
        for c in sh.get("cards", []):
            cc = {x: v for x, v in c.items() if x != "off"}
            cc["at"] = round(shot_t0 + c["off"], 3)
            cards.append(cc)
    hook_end = t
    # noir final (voix absente)
    black = os.path.join(seg_dir, "black.mp4")
    bs = plan["black_s"]
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={bs}",
         "-f", "lavfi", "-i", f"anoisesrc=r=48000:a=0.004:c=pink:d={bs}", "-ac", "1", "-ar", "48000", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", black])  # mono comme les extraits, sinon concat -c copy casse le son
    segs.append(black)

    json.dump({"words": words}, open(os.path.join(work, "hook_words.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(cards, open(os.path.join(work, "hook_cards.json"), "w"), ensure_ascii=False, indent=1)
    style = json.load(open(os.path.join(ROOT, "style/interview-v1/style.json")))
    style["subtitles"]["hold"] = 0.02
    style["subtitles"]["max_gap"] = 0.6
    json.dump(style, open(os.path.join(work, "sub_style.json"), "w"))
    run(["python3", os.path.join(ROOT, "tools/subtitles.py"), os.path.join(work, "hook_words.json"),
         os.path.join(work, "hook_subs.ass"), "--style", os.path.join(work, "sub_style.json"),
         "--w", "1920", "--h", "1080", "--mode", "build", "--range", f"0,{hook_end:.2f}"])
    run(["python3", os.path.join(ROOT, "tools/titles.py"), os.path.join(work, "hook_cards.json"),
         os.path.join(work, "hook_titles.ass"), "--w", "1920", "--h", "1080",
         "--style", os.path.join(ROOT, "style/interview-v1/style.json")])

    lst = os.path.join(work, "concat.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    raw = os.path.join(work, "hook_raw.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw])
    outp = os.path.join(job, plan["out"].replace("final.mp4", "final_1080.mp4") if final else plan["out"])
    fonts = os.path.join(ROOT, "assets/fonts")
    vf = f"ass={os.path.join(work, 'hook_subs.ass')}:fontsdir={fonts},ass={os.path.join(work, 'hook_titles.ass')}:fontsdir={fonts}"
    run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf", vf, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21" if not final else "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", outp])
    print(f"hook {hook_end:.1f} s + noir {bs} s -> {outp}")


if __name__ == "__main__":
    main()
