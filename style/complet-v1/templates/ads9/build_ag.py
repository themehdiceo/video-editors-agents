"""Pub face caméra 9:16 (rush 3:4 recadré), montage complet v1 + fin validée (anas-ads/endcard.py).
usage: build_ag.py ad5   (lit ad5.mov, ad5_g.json ; écrit ../out/<nom>.mp4)
Coupes sur l'énergie de la voix (250-3500 Hz) : pauses > 0,35 s coupées, marges 0,08 / 0,12, zoom 1,08 une coupe sur deux.
Mots Gemini recalés phrase par phrase sur le début/fin réels de la voix. Contrôle : aucun mot à cheval sur une coupe."""
import json, os, subprocess, sys
import numpy as np
H = os.path.dirname(os.path.abspath(__file__)); REPO = "/Users/pro/video-editors-agents"
M = f"{REPO}/assets/music/ads/rap-joyeux-2.mp3"; M_LUFS = -13.4
MAXGAP, PAD_IN, PAD_OUT = 0.35, 0.08, 0.12
ZOOM, VOICE_LUFS, MUSIC_UNDER, CTA_HOLD = 1.08, -16, 13.5, 5.5
VOICE = ("highpass=f=80,afftdn=nf=-28,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1:g=2.5,"
         f"deesser=i=0.3,acompressor=threshold=-20dB:ratio=2.5:attack=10:release=150:makeup=2,loudnorm=I={VOICE_LUFS}:TP=-2:LRA=9")
NAMES = {"r1": "AD1 relaunch 20nov", "a45": "AD 4.5 new", "a25": "AD 2.5 new", "ad5": "AG5 - anti gourou - nassaba d l'internet", "ad6": "AG6 - anti gourou - 99% dyal s7ab dorat"}
FIX = {"l-weqt": "lwe9t", "l-weqt.": "lwe9t", "l-flous.": "lflous", "l-business": "l'business", "l-business?": "l'business ?", "l-arba7,": "l'arba7", "l-bouton": "bouton", "l-ta7t,": "lte7t", "l-oukhra.": "lokhra", "wejjedt": "wjjedt", "kanshre7": "kanchre7", "nassaba": "Nassaba", "ibi3o": "ybi3o", "ykheliwk": "ykhlliwk", "rassk": "rassek", "lyouma": "lyoum", "lyoma": "lyoum",
       "sali": "nsali", "kaml": "kamel", "fl": "f", "ichhar": "l'ichhar", "lwla": "lowla", "l-lowala,": "lowla,", "stetmer": "nstathmer",
       "ghanstestmer": "ghanstathmer", "ghanaxd": "ghanakhod", "n-nas": "nass", "ch-her": "chhar", "ch-her,": "chhar,", "chher": "chhar",
       "lmlyon": "mlyon", "3emri": "3mri", "ghanxtaser": "ghankhtasser", "t-triq.": "triq.", "d-domaine": "domaine", "d-dorat": "dorat",
       "wjjt": "wjjedt", "lk": "lik", "dba": "daba", "rekez": "rkkez", "deja": "déjà", "video": "vidéo", "brrek": "brek", "brek": "brek",
       "ntla9aw": "ntla9aw", "ntlaqaw": "ntla9aw", "l'okhra": "lokhra", "l'oxra.": "lokhra.", "l-jiha": "jiha", "l-concept": "concept",
       "l-bouton": "bouton", "qdart": "9dert", "ghatqol": "ghatgoli", "ghatgoli": "ghatgoli", "n7eyydo": "n7ydo", "nrkkz": "nrkkez"}
KW = {"millionnaire", "10%", "weqt", "l-weqt", "l-weqt.", "youtube", "lmounafassa", "saturé", "lfourssa", "train", "formation", "trbe7", "nassaba", "formation", "fabor", "10", "mlyon", "20", "3am", "rabe7", "rabe7.", "pourcentage", "pourcentage,", "5", "nass", "concept",
      "99%", "kitfellaw", "budget", "triq.", "vidéo", "vidéo,", "bouton", "partenaires", "kolchi", "kolchi."}
name = sys.argv[1]; D_ = f"{H}/{name}"; os.makedirs(D_, exist_ok=True)
SRC = f"{H}/{name}.mov"
run = lambda *a: subprocess.run(list(a), check=True)
probe = lambda p, e: float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", e, "-of", "csv=p=0", p], capture_output=True, text=True).stdout.split()[0].strip(","))

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-map", "0:a:0", "-ac", "1", "-ar", "16000",
                      "-af", "highpass=f=250,lowpass=f=3500", "-f", "s16le", "-"], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
n = len(x) // 160
env = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
THR = np.percentile(env, 5) + 17  # pièce qui résonne, voix faible : seuil sur le plancher de bruit
v = env > THR
runs, i = [], 0
while i < len(v):
    if v[i]:
        j = i
        while j < len(v) and v[j]: j += 1
        if j - i >= 6: runs.append([i / 100, j / 100])
        i = j
    else: i += 1

segsG = json.load(open(f"{H}/{name}_g.json"))
words = []
for g in segsG:  # recalage phrase par phrase sur la voix réelle
    ws = g["words"]; g0, g1 = ws[0]["start"], ws[-1]["end"]
    rr = [r for r in runs if r[1] > g0 - 0.3 and r[0] < g1 + 0.3]
    v0, v1 = (rr[0][0], rr[-1][1]) if rr else (g0, g1)
    sc = lambda u: v0 + (u - g0) * (v1 - v0) / max(g1 - g0, 0.01)
    for w in ws:
        words.append({"w": FIX.get(w["w"].lower(), w["w"]).rstrip(".,?!"), "start": sc(w["start"]), "end": sc(w["end"]), "raw": w["w"].lower()})

# passages de voix, pauses <= MAXGAP fusionnées
vr = [runs[0][:]]
for r in runs[1:]:
    if r[0] - vr[-1][1] <= MAXGAP or env[int(vr[-1][1] * 100):int(r[0] * 100)].max() > np.percentile(env, 5) + 8: vr[-1][1] = r[1]  # on ne coupe que du vrai silence (fin de « 3am » rognée sinon)
    else: vr.append(r[:])
dur = probe(SRC, "format=duration")
segs = [[max(0, s - PAD_IN), min(dur, e + PAD_OUT)] for s, e in vr]
for j in range(1, len(segs)):
    if segs[j - 1][1] > segs[j][0]: m = (vr[j - 1][1] + vr[j][0]) / 2; segs[j - 1][1] = m; segs[j][0] = m
segs = [s for s in segs if s[1] - s[0] > 0.15]
segs[-1][1] = dur - 0.02  # Mehdi 20/11 : finir la phrase « ntla9aw f jiha lokhra » jusqu au bout du rush
# coupes sans perte (changement de zoom) entre deux phrases Gemini, au creux d'énergie, à l'intérieur d'un passage gardé
for g, h in zip(segsG, segsG[1:]):
    a_, b_ = g["words"][-1]["end"] - 0.15, h["words"][0]["start"] + 0.15
    k = int(a_ * 100) + int(np.argmin(env[int(a_ * 100):int(b_ * 100)])); c = k / 100
    for sg in segs:
        if sg[0] + 0.6 < c < sg[1] - 0.6: segs.append([c, sg[1]]); sg[1] = c; break
    segs.sort()
print("passages", [(round(s, 2), round(e, 2)) for s, e in segs])
# contrôle : mot (Gemini recalé) qui tombe hors des passages gardés
for w in words:
    inside = sum(max(0, min(w["end"], e) - max(w["start"], s)) for s, e in segs) / max(w["end"] - w["start"], 0.01)
    if inside < 0.6: print(f"ATTENTION mot hors passage : {w['w']} {w['start']:.2f}-{w['end']:.2f} ({inside:.0%})")

L, subwords, t = [], [], 0.0
CROP = "crop=ih*9/16:ih:(iw-ih*9/16)/2:0"
for j, (s, e) in enumerate(segs):
    d = e - s
    zf = f",crop=iw/{ZOOM}:ih/{ZOOM}:(iw-iw/{ZOOM})/2:(ih-ih/{ZOOM})*0.35" if j % 2 else ""
    L.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS,{CROP}{zf},scale=1080:1920:flags=lanczos,setsar=1,fps=30[v{j}]")
    fi = ",afade=t=in:d=0.012" if j == 0 or abs(segs[j - 1][1] - s) > 1e-3 else ""  # pas de fondu sur une coupe sans perte (musique continue)
    fo = f",afade=t=out:st={d - 0.02:.3f}:d=0.02" if j == len(segs) - 1 or abs(segs[j + 1][0] - e) > 1e-3 else ""
    L.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,aresample=48000{fi}{fo}[a{j}]")
    for w in words:
        if s <= (w["start"] + w["end"]) / 2 < e:
            subwords.append({"w": w["w"], "start": round(t + max(w["start"], s) - s, 3), "end": round(t + min(w["end"], e) - s, 3),
                             "k": w["raw"].strip(".,!?:") in {k.strip(".,") for k in KW} or w["w"].lower() in KW})
    t += d
L.append("".join(f"[v{j}][a{j}]" for j in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][ac]")
L.append("[ac]anull[a]")  # Mehdi 20/11 : musique déjà dans le rush, son d'origine intouché
open(f"{D_}/g.txt", "w").write(";\n".join(L))
p = f"{D_}/cut0.mov"
run("ffmpeg", "-v", "error", "-y", "-i", SRC, "-/filter_complex", f"{D_}/g.txt", "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000", p)
vd = probe(p, "stream=duration"); cut = f"{D_}/cut.mov"
run("ffmpeg", "-v", "error", "-y", "-i", p, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", f"apad=whole_dur={vd:.4f},atrim=0:{vd:.4f}", "-c:a", "pcm_s16le", cut)
# animations (Mehdi 20/11 : une toutes les 10-15 s) : cartes motion vsl-v1 + écrans noirs animés, déclencheur = mot source
sys.path[:0] = [H, f"{REPO}/jobs/ppc-ads/work"]
import cards, slides9, anim9, photos9
PH = "/Users/pro/Desktop/Mes photos/"; clicks = []
OFF, acc = [], 0.0
for s, e in segs: OFF.append((s, e, acc)); acc += e - s
s2d = lambda x: next((o + min(max(x, s), e) - s for s, e, o in OFF if x < e), acc)
def wt(tok, after, end=False):
    w = next(w for w in words if w["raw"].strip(".,?!").startswith(tok.lower()) and w["start"] >= after - 0.6)
    return s2d(w["end"] if end else w["start"])
ovs = []; hide = []
AF = f"{H}/{name}_anim.json"
for ci, c in enumerate(json.load(open(AF)) if os.path.exists(AF) else []):
    if c["type"] in ("anim", "photos"):  # Mehdi 20/11 : petits films de personnages / défilé de SES photos, ~3-4 s
        t_in = max(wt(*c["start"]) - 0.15, 0); t_end = min(wt(*c["end"], end=True) + 0.2, acc - 0.2)
        if c["type"] == "anim":
            mk = {k: wt(*v) - t_in for k, v in c.get("marks", {}).items()}
            ln = [(txt, wt(tok, x) - t_in) for txt, tok, x in c.get("lines", [])]
            f = anim9.render(c["kind"], t_end - t_in, mk, c["kick"], ln, f"{D_}/anim{ci}.mov")
        else:
            f = f"{D_}/anim{ci}.mov"; clicks += [t_in + x for x in photos9.render([PH + x for x in c["files"]], t_end - t_in, f)]
        hide.append((t_in, t_end)); ovs.append((f, t_in, "slide")); print(f"anim {ci} {c['type']} {t_in:.1f}-{t_end:.1f}"); continue
    times = [wt(tok, x) for _, tok, x in c["lines"]]
    t_in = max(times[0] - 0.15, 0)
    t_end = wt(*c["end"], end=True) + 0.25 if "end" in c else times[-1] + c.get("hold", 2.5)
    t_end = min(t_end, acc - 0.2)
    rel = [x - t_in for x in times]
    if c["type"] == "slide":
        f = slides9.render(c["kick"], [l[0] for l in c["lines"]], rel, t_end - t_in, f"{D_}/anim{ci}.mov"); hide.append((t_in, t_end))
    else:
        f = cards.render(c.get("kick"), [l[0] for l in c["lines"]], rel, t_end - t_in, f"{D_}/anim{ci}.mov")
    ovs.append((f, t_in, c["type"])); print(f"anim {ci} {c['type']} {t_in:.1f}-{t_end:.1f}")
subwords = [w for w in subwords if not any(a - 0.05 <= (w["start"] + w["end"]) / 2 <= b + 0.05 for a, b in hide)]
CARD_BOTTOM = 1180
json.dump({"words": subwords}, open(f"{D_}/words.json", "w"), ensure_ascii=False, indent=0)
run(sys.executable, f"{REPO}/tools/subtitles.py", f"{D_}/words.json", f"{D_}/subs.ass", "--style", f"{REPO}/jobs/ads-c1/work/substyle.json", "--mode", "build")
run(sys.executable, f"{REPO}/jobs/ppc-ads/work/fix_ass.py", f"{D_}/subs.ass")
DV = probe(cut, "format=duration"); D = DV + CTA_HOLD
run(sys.executable, f"{REPO}/jobs/anas-ads/work/endcard.py", f"{D_}/end.mov", str(CTA_HOLD))
cg = "".join(f"[{2 + i}:v]setpts=PTS+{t0:.3f}/TB[c{i}];[v{i}][c{i}]overlay=" + ("0:0" if ty == "slide" else "(W-w)/2:250") + f":eof_action=pass[v{i + 1}];\n" for i, (_, t0, ty) in enumerate(ovs))
import numpy as np, wave
photos9.click_wav(f"{D_}/click.wav"); cw_ = np.frombuffer(wave.open(f"{D_}/click.wav").readframes(10**6), np.int16).astype(np.float32)
trk = np.zeros(int((D + 1) * 48000), np.float32)
for c_ in clicks: i_ = int(c_ * 48000); trk[i_:i_ + len(cw_)] += cw_ * 0.5
sfx = f"{D_}/sfx.wav"; w_ = wave.open(sfx, "wb"); w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(48000); w_.writeframes(np.clip(trk, -32000, 32000).astype(np.int16).tobytes()); w_.close()
g = f"""[0:v]tpad=stop_mode=clone:stop_duration={CTA_HOLD},ass={D_}/subs.ass[vs];
[1:v]setpts=PTS+{DV:.3f}/TB[end];
[vs][end]overlay=0:0:eof_action=pass[v0];
{cg}[v{len(ovs)}]null[v];
[0:a]afade=t=out:st={DV - 0.08:.3f}:d=0.08,apad=pad_dur={CTA_HOLD}[ao];
[{2 + len(ovs)}:a]atrim=2:{2 + CTA_HOLD + 0.3:.3f},asetpts=PTS-STARTPTS,volume=0.37,afade=t=in:d=0.4,afade=t=out:st={CTA_HOLD - 1.3:.3f}:d=1.5,adelay={int((DV - 0.2) * 1000)}:all=1[mo];
[ao][mo][{3 + len(ovs)}:a]amix=inputs=3:duration=first:normalize=0[a]"""  # Mehdi 20/11 : rap joyeux en outro sous l'écran de fin seulement (~ -22 LUFS comme le rush)
open(f"{D_}/final_graph.txt", "w").write(g)
out = f"{H}/../out/{NAMES[name]} (apercu).mp4"
run("ffmpeg", "-v", "error", "-y", "-i", cut, "-i", f"{D_}/end.mov", *sum((["-i", f] for f, _, _ in ovs), []), "-i", M, "-i", sfx, "-/filter_complex", f"{D_}/final_graph.txt",
    "-map", "[v]", "-map", "[a]", "-t", f"{D:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
run("ffmpeg", "-v", "error", "-y", "-i", out, "-vf", f"fps=18/{D:.2f},scale=200:-2,tile=9x2", "-frames:v", "1", f"{D_}_qc.jpg")
run("ffmpeg", "-v", "error", "-y", "-i", out, "-map", "0:a", "-ac", "1", "-c:a", "libopus", "-b:a", "48k", f"{D_}_out.opus")
print("ok", out, round(D, 1), "s", os.path.getsize(out) // 1_000_000, "Mo")
