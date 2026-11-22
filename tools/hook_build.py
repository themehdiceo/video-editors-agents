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


def rms_track(src, t0, t1, win=0.01):
    import array
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t0, 0):.3f}", "-t", f"{t1 - max(t0, 0):.3f}", "-i", src,
                        "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    a = array.array("h")
    a.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    n = int(16000 * win)
    return [(sum(x * x for x in a[i:i + n]) / n) ** 0.5 for i in range(0, len(a) - n, n)]


def snap(src, t, reach=0.45, win=0.01, need=5):
    """Recale une borne de coupe sur le creux d'énergie le plus proche (>= need*10 ms de calme).
    Les timestamps Scribe dérivent de 0.1-0.3 s : sans ça on coupe au milieu d'un mot. Renvoie (t_snap, ok)."""
    lo = t - reach - 0.1
    tr = rms_track(src, lo, t + reach + 0.1, win)
    if len(tr) < 2 * need + 2:
        return t, False
    thr = max(max(tr) * 0.06, 120)
    q = [v < thr for v in tr]
    c0 = int((t - lo) / win)
    h = need // 2
    for d in range(0, int(reach / win) + 1):
        for sgn in (1, -1):
            i = c0 + sgn * d
            if h <= i < len(tr) - h and all(q[i - h:i + h + 1]):
                return round(lo + (i + 0.5) * win, 3), True
    return t, False


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

    # Recalage des bornes sur la forme d'onde (désactivable : "snap": false dans le plan, ou range à 3 valeurs [s, e, "exact"])
    report = []
    if plan.get("snap", True):
        for sh in plan["shots"]:
            for rg in sh["ranges"]:
                if len(rg) > 2:
                    del rg[2:]
                    continue
                for bi in (0, 1):
                    new, ok = snap(src, rg[bi])
                    report.append(f"{sh['id']} {'début' if bi == 0 else 'fin'} {rg[bi]:.2f} -> {new:.2f} {'ok' if ok else 'PAS DE CREUX (parole continue)'}")
                    rg[bi] = new
        open(os.path.join(work, "snap_report.txt"), "w").write("\n".join(report))
        print(f"snap : {sum('PAS DE' in r for r in report)} bornes sans creux, voir work/snap_report.txt")
    words, cards, segs = [], [], []
    t = 0.0
    def crop(tl):
        cw = min(tl["w"], int(tl["h"] * (W / 2) / H))
        cx = tl["x"] + int((tl["w"] - cw) * tl["face_x"])
        return f"crop={cw}:{tl['h']}:{cx}:{tl['y']}"

    def lay_graph(lay, sh, inp, outp, u):
        """Filtre d'une mise en page ('split', 'zoom' ou tuile A/M plein écran) : [inp] -> [outp]. u = suffixe d'étiquettes."""
        if lay == "split":
            a, m = tiles["A"], tiles["M"]
            return (f"[{inp}]split=2[p{u}][q{u}];[p{u}]{crop(a)},scale={W // 2}:{H},setsar=1[l{u}];"
                    f"[q{u}]{crop(m)},scale={W // 2}:{H},setsar=1[r{u}];[l{u}][r{u}]hstack,fps={FPS}[{outp}]")
        if lay == "zoom":
            # zoom sur une zone de la source (x, y, w, h en pixels source), plein cadre : cache ce qui est hors zone
            zx, zy, zw, zh = sh["crop"]
            return f"[{inp}]crop={zw}:{zh}:{zx}:{zy},scale={W}:{H},setsar=1,fps={FPS}[{outp}]"
        tl = tiles[lay]
        if plan.get("fill", False):
            # plein cadre 16:9 SANS bords flous : zoom sur la tuile (bande 16:9, fy = 0 haut ... 1 bas, par shot ou par tuile)
            ch = min(tl["h"], int(tl["w"] * H / W))
            cw = int(ch * W / H)
            fy = sh.get("fy", tl.get("fy", 0.0))
            cy = tl["y"] + int((tl["h"] - ch) * fy)
            cx = tl["x"] + int((tl["w"] - cw) * tl.get("face_x", 0.5))
            return f"[{inp}]crop={cw}:{ch}:{cx}:{cy},scale={W}:{H},setsar=1,fps={FPS}[{outp}]"
        return (f"[{inp}]crop={tl['w']}:{tl['h']}:{tl['x']}:{tl['y']},split=2[a{u}][b{u}];"
                f"[b{u}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:6,eq=brightness=-0.2[bg{u}];"
                f"[a{u}]scale=-2:{H}[fg{u}];[bg{u}][fg{u}]overlay=(W-w)/2:0,setsar=1,fps={FPS}[{outp}]")

    src_words = [x for x in json.load(open(os.path.join(work, "words.json")))["words"] if "start" in x] \
        if os.path.exists(os.path.join(work, "words.json")) else []
    for si, sh in enumerate(plan["shots"]):
        shot_t0 = t
        flat = 0
        # "views" : [[t_source, layout], ...] = changements d'IMAGE seulement. Le son du range ne coupe jamais.
        views = sorted(sh.get("views", []), key=lambda v: v[0])
        for ri, (s, e) in enumerate(sh["ranges"]):
            d = round(e - s + PAD_IN + PAD_OUT, 3)
            lay = sh["layout"]
            t0s = s - PAD_IN
            before = [v for v in views if v[0] <= s + 0.001]
            if before:
                lay = before[-1][1]
            switches = [(v[0] - t0s, v[1]) for v in views if s + 0.001 < v[0] < e - 0.05]
            if not switches:
                vf = lay_graph(lay, sh, "0:v", "v", "")
            else:
                # un flux par usage (une étiquette ffmpeg ne peut être lue qu'une fois)
                need = [lay] + [x[1] for x in switches]
                parts = [f"[0:v]split={len(need)}" + "".join(f"[in{i}]" for i in range(len(need)))]
                for i, ly in enumerate(need):
                    parts.append(lay_graph(ly, sh, f"in{i}", f"L{i}", str(i)))
                cur = "L0"
                for k, (ts, ly) in enumerate(switches):
                    te = switches[k + 1][0] if k + 1 < len(switches) else 9999
                    nxt = "v" if k == len(switches) - 1 else f"o{k}"
                    parts.append(f"[{cur}][L{k + 1}]overlay=enable='between(t,{ts:.3f},{te:.3f})':eof_action=pass[{nxt}]")
                    cur = nxt
                vf = ";".join(parts)
            # "masks" : [[x, y, w, h, "texte"], ...] en pixels SOURCE : cache une marque (aplat + texte court) avant tout recadrage
            if sh.get("masks"):
                # Entrée à 7 valeurs [x, y, w, h, texte, t_debut_src, t_fin_src] = masque suivi dans le temps (tools/track_mask.py)
                def _mk(m):
                    x, y, w, h, tx = m[:5]
                    en = f":enable='between(t,{m[5] - t0s:.3f},{m[6] - t0s:.3f})'" if len(m) >= 7 else ""
                    return (f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0x1a1a1a@1:t=fill{en},"
                            f"drawtext=fontfile={os.path.join(ROOT, 'assets/fonts/Montserrat-ExtraBold.ttf')}:text='{tx}':fontcolor=white:"
                            f"fontsize={min(int(h * 0.5), 70)}:x={x}+({w}-text_w)/2:y={y}+({h}-text_h)/2{en}")
                mk = ",".join(_mk(m) for m in sh["masks"])
                vf = f"[0:v]{mk}[mv];" + vf.replace("[0:v]", "[mv]", 1)
            out = os.path.join(seg_dir, f"s{si:02d}_{ri}.mp4")
            # boost : mot soufflé trop faible ([début_src, fin_src, dB]) -> gain local avant le loudnorm
            boosts = "".join(
                f"volume={g}dB:enable='between(t,{b0 - (s - PAD_IN):.3f},{b1 - (s - PAD_IN):.3f})',"
                for b0, b1, g in sh.get("boost", []) if s - PAD_IN <= b0 < e + PAD_OUT)
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{s - PAD_IN:.3f}", "-t", f"{d}", "-i", src,
                 "-filter_complex", vf, "-map", "[v]", "-map", "0:a:0",
                 "-af", f"{boosts}afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03,aresample=48000",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
            segs.append(out)
            toks = sh["text"][ri]
            n = len(toks)
            # Calage sur les vrais mots de la source (words.json) : le jeton j prend le début du mot source j*m/n.
            sw = [x for x in src_words if x["start"] >= s - 0.05 and x["end"] <= e + 0.05 and x["w"].strip("?.,!؟ ")]
            if plan.get("align", True) and len(sw) >= 2:
                m_ = len(sw)
                starts = [max(sw[min(int(j * m_ / n), m_ - 1)]["start"], s) for j in range(n)] + [e]
                for j in range(1, n + 1):
                    starts[j] = max(starts[j], starts[j - 1] + 0.05) if j < n else starts[j]
            else:
                starts = [s + (e - s) * j / n for j in range(n + 1)]
            for j, w in enumerate(toks):
                ws = t + PAD_IN + (starts[j] - s)
                we = t + PAD_IN + (starts[j + 1] - s)
                wd = {"w": w, "start": round(ws, 3), "end": round(we, 3)}
                if j == n - 1 and ri not in sh.get("join", []):  # "join" : la phrase continue sur le range suivant
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
    # Musique choisie par Mehdi : toujours reposée à chaque rendu (brouillon ET 1080p), sinon elle se perd
    # quand on refait le montage (bug du 09/11 : musique absente après la correction du masque).
    ma = plan.get("music_after")
    if ma and ma.get("file"):
        mfile = ma["file"] if os.path.isabs(ma["file"]) else (
            os.path.join(job, ma["file"]) if os.path.exists(os.path.join(job, ma["file"])) else os.path.join(ROOT, ma["file"]))
        tmp = outp.replace(".mp4", "_music.mp4")
        cmd = ["python3", os.path.join(ROOT, "tools/add_music.py"), outp, mfile, tmp,
               "--volume", str(min(0.4, ma.get("volume", 0.3))), "--until", str(ma.get("until", hook_end))]
        for k in ("start", "delay", "duck_ratio"):
            if ma.get(k) is not None:
                cmd += [f"--{k.replace('_', '-')}", str(ma[k])]
        if ma.get("duck") is False:
            cmd.append("--no-duck")
        run(cmd)
        os.replace(tmp, outp)
        print(f"musique {os.path.basename(mfile)} posée (volume {min(0.4, ma.get('volume', 0.3))})")
    print(f"hook {hook_end:.1f} s + noir {bs} s -> {outp}")


if __name__ == "__main__":
    main()
