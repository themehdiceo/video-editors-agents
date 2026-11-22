#!/usr/bin/env python3
"""keep.json à partir de l'énergie (bande voix 250-3500 Hz, trames 20 ms) : on ne coupe QUE dans le silence.
Prises ratées retirées = segments dont le milieu tombe dans DROP (on garde la dernière prise)."""
import json, numpy as np
D = "jobs/20261118-062812-edit/work/"
e = np.load(D + "env_db.npy"); H = 0.02
THR, BRIDGE, MINSEG, PRE, POST, MERGE = 92, 0.35, 0.10, 0.08, 0.12, 0.15  # v3 = complet-v1 : pauses > 0,35 s coupées, marges 0,08 / 0,12
DROP = [(73.8, 75.0, "faux départ 'ila tsennit' (reprise 76.6)"),
        (224.5, 234.6, "1re prise Profit Partners Capital (reprise 235.1)"),
        (287.5, 290.6, "1re prise '500 $ howa l minimum' (reprise 293.4)"),
        (391.0, 408.8, "1res prises question 3 (reprise 409.0)"),
        (418.8, 422.9, "1re prise 'ta famille ma ghatchaj3ekch' (reprise 423.7 = script)"),
        (578.0, 581.6, "1re prise 'produit b 390 $' (reprise 582.2)"),
        (678.5, 680.2, "faux départ 'En plus de ça c'est...'"),
        (694.5, 695.9, "faux départ 'Alors, bach--'"),
        (722.9, 728.6, "1re prise 'l7aja li ta 7ed maygoulha lik' (reprise 730.0)"),
        (336.0, 340.6, "1re prise 'makanbi3lekch lwahm' (reprise 348.1)"),
        (1031.4, 1032.8, "faux départ '7it ila jab...' (reprise 1037.7)")]
# doute gardé : 913.5-914.9 ('kaynin des gens li kaygoulo l'truc--' ou 'ma kaynch des trucs') : on garde
on = e > THR
segs, cur = [], None
for k, v in enumerate(on):
    t = k * H
    if v:
        if cur and t - cur[1] <= BRIDGE: cur[1] = t + H
        else:
            if cur: segs.append(cur)
            cur = [t, t + H]
if cur: segs.append(cur)
segs = [s for s in segs if s[1] - s[0] >= MINSEG]
kept, dropped = [], []
for a, b in segs:
    m = (a + b) / 2
    d = next((r for r in DROP if r[0] <= m <= r[1]), None)
    (dropped if d else kept).append((a, b, d[2] if d else ""))
# marges sans empiéter sur le segment voisin (gardé ou retiré)
allb = sorted(segs)
def nb(t, side):
    xs = [s[1] for s in allb if s[1] <= t - 1e-6] if side < 0 else [s[0] for s in allb if s[0] >= t + 1e-6]
    return (max(xs) if xs else 0) if side < 0 else (min(xs) if xs else 1e9)
out = []
for a, b, _ in kept:
    pa = max(a - PRE, (nb(a, -1) + a) / 2); pb = min(b + POST, (b + nb(b, 1)) / 2)
    if out and pa - out[-1][1] <= MERGE: out[-1][1] = pb
    else: out.append([pa, pb])
# v2 : hésitations et mots répétés retirés au mot près (temps words2.json), bornes calées sur le creux d'énergie le plus proche
WCUTS = [(664.33, 665.03, "c'est une, (répété)"), (958.92, 959.63, "ah,"), (1115.33, 1115.74, "c'est, (répété)"),
         (1122.6, 1124.02, "flous lmabi3at, (répété)"), (1127.1, 1127.86, "ah, dyal--"), (1147.06, 1147.85, "ma 3mmer--"),
         # v3 (corrigé v6) : repérés par Gemini, bornes posées sur la FORME D'ONDE (les minutages Gemini sont approximatifs)
         (142.3, 147.6, "souffle avant 'chefti, derrière chaque obstacle'"), (209.04, 212.32, "faux départ 'tu n'as p-'"),
         (241.23, 242.84, "1re prise 'w 99 % f lmya katmchi'"), (331.4, 347.68, "souffle + 1re prise avant '7tta ana'"),
         (848.5, 853.7, "souffle après 'wa7ed.'"), (936.2, 938.7, "1re prise 'w ghanchoufo b l'ar9am' + souffle")]
def snap(t):
    i = int(t / H); r = range(max(i - 4, 0), i + 5)
    return min(r, key=lambda k: e[k]) * H
for a, b, _ in WCUTS:
    a, b = snap(a), snap(b); new = []
    for x, y in out:
        if b <= x or a >= y: new.append([x, y]); continue
        if x < a: new.append([x, a])
        if b < y: new.append([b, y])
    out = new
json.dump({"keep": [{"start": round(a, 3), "end": round(b, 3)} for a, b in out]}, open(D + "keep.json", "w"), indent=0)
json.dump([{"start": a, "end": b, "why": w} for a, b, w in dropped], open(D + "dropped.json", "w"), ensure_ascii=False, indent=0)
print(len(out), "passages,", round(sum(b - a for a, b in out), 1), "s gardées ;", len(dropped), "segments retirés")
