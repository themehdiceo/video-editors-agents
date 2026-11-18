#!/usr/bin/env python3
"""sub_text.txt (phrases darija latine écrites à la main, temps source) -> sub_words.json.
Chaque mot est posé sur les trames de voix (énergie > 92 dB) de sa phrase, au prorata de sa longueur."""
import json, re, numpy as np
D = "jobs/20261118-062812-edit/work/"
e = np.load(D + "env_db.npy"); H = 0.02
# passages réellement gardés par cut.py (timemap) : un mot posé hors passage disparaîtrait des sous-titres
K = [{"start": r["src_start"] + 0.04, "end": r["src_end"] - 0.04} for r in json.load(open(D + "aroll_cut.mp4.timemap.json"))["ranges"]]
inkeep = lambda t: any(k["start"] <= t <= k["end"] for k in K)
out = []
for line in open(D + "sub_text.txt", encoding="utf-8"):
    if not line.strip() or line.startswith("#"): continue
    t, txt = line.split("|", 1); a, b = map(float, t.split())
    toks, key = [], False
    txt = re.sub(r"(\d) (\d{3})", "\\1\u00a0\\2", txt.strip())
    txt = re.sub(r"(\d) ([%$])", "\\1\u00a0\\2", txt)
    for w in txt.split(" "):
        if not w: continue
        k0 = w.startswith("*") or key
        key = (k0 and not w.rstrip(".,!?:;").endswith("*"))
        toks.append((w.replace("*", ""), k0))
    fr = [i for i in range(int(a / H), int(b / H)) if e[i] > 92 and inkeep(i * H)] or list(range(int(a / H), int(b / H)))
    wt = np.array([len(w) + 2 for w, _ in toks], float); cum = np.concatenate([[0], np.cumsum(wt)]) / wt.sum()
    n = len(fr)
    for j, (w, k) in enumerate(toks):
        i0 = fr[min(int(cum[j] * n), n - 1)]; i1 = fr[min(max(int(cum[j + 1] * n) - 1, 0), n - 1)]
        st = i0 * H; en = max(i1 * H + H, st + 0.08)
        kk = next((k for k in K if k["start"] <= st <= k["end"]), None)
        if kk: en = min(en, kk["end"]); st = min(st, en - 0.02)  # le mot reste dans UN passage gardé
        d = {"w": w, "start": round(st, 3), "end": round(en, 3), "k": k}
        if j == len(toks) - 1: d["br"] = True
        out.append(d)
json.dump({"words": out}, open(D + "sub_words.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "mots ;", sum(w["k"] for w in out), "mots-clés")
