"""Assemble des morceaux de rushs (segments Gemini choisis, dans l'ordre voulu) en un seul .mov + _g.json.
usage: mkcomp.py nom '[["i0357",[0,1]],["i0356",[1,2,3]]]'"""
import json, subprocess, sys, os
import numpy as np
def envelope(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-map', '0:a:0', '-ac', '1', '-ar', '16000', '-af', 'highpass=f=250,lowpass=f=3500', '-f', 's16le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(x) // 160
    e = 20 * np.log10(np.sqrt((x[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9); return e > np.percentile(e, 5) + 11
H = os.path.dirname(os.path.abspath(__file__)); name, pieces = sys.argv[1], json.loads(sys.argv[2])
parts, segs, t = [], [], 0.0
for pc in pieces:
    src, idx = pc[0], pc[1]; OV = pc[2] if len(pc) > 2 else {}  # OV = {"b": fin exacte} mesurée à l'oreille/Gemini extrait court
    G = json.load(open(f"{H}/{src}_g.json")); dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{H}/{src}.mov"], capture_output=True, text=True).stdout)
    V = envelope(f'{H}/{src}.mov')
    runs = []  # indices consécutifs = un seul morceau
    for i in idx:
        if runs and i == runs[-1][-1] + 1: runs[-1].append(i)
        else: runs.append([i])
    for r in runs:
        g0, g1 = G[r[0]]["words"][0]["start"], G[r[-1]]["words"][-1]["end"]
        pe = G[r[0] - 1]["words"][-1]["end"] if r[0] > 0 else 0
        ns = G[r[-1] + 1]["words"][0]["start"] if r[-1] + 1 < len(G) else dur
        q = lambda k: not V[max(k, 0):k + 25].any()  # 0,25 s de vrai silence
        kb = next((k for k in range(int((g1 - 0.3) * 100), min(int((g1 + 1.5) * 100), len(V))) if q(k)), None)
        b = min(kb / 100 + 0.12, dur) if kb is not None else min(g1 + 0.6, (g1 + ns) / 2, dur)  # coupe dans le 1er vrai silence après la phrase (Gemini décale de ±1 s)
        ka = next((k for k in range(int((g0 + 0.3) * 100), max(int((g0 - 1.5) * 100), 0), -1) if q(k - 25)), None)
        a = max(ka / 100 - 0.12, 0) if ka is not None else max(g0 - 0.6, (pe + g0) / 2, 0)
        if r[-1] == idx[-1] and 'b' in OV: b = OV['b']
        if r[0] == idx[0] and 'a' in OV: a = OV['a']
        p = f"{H}/{name}_p{len(parts)}.mov"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", f"{H}/{src}.mov", "-t", f"{b - a:.3f}", "-c:v", "h264_videotoolbox", "-b:v", "20M", "-c:a", "pcm_s16le", "-ar", "48000", p], check=True)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
        for i in r:
            g = json.loads(json.dumps(G[i])); g["retake"] = False
            for w in g["words"]: w["start"] = round(w["start"] - a + t, 2); w["end"] = round(w["end"] - a + t, 2)
            segs.append(g)
        parts.append(p); t += d
open(f"{H}/{name}_list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{H}/{name}_list.txt", "-c", "copy", f"{H}/{name}.mov"], check=True)
json.dump(segs, open(f"{H}/{name}_g.json", "w"), ensure_ascii=False, indent=0)
for g in segs: print(f"{g['words'][0]['start']:6.2f}-{g['words'][-1]['end']:6.2f} {g['text'][:70]}")
