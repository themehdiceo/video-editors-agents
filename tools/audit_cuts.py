#!/usr/bin/env python3
"""Audit des coupes d'un plan hook : chaque borne de range est-elle dans un mot, sur un mot coupé, ou dans le silence ?
usage: audit_cuts.py work/plan.json work/words.json [--fix out_plan.json]
Pour chaque borne, regarde (1) les mots Scribe qui chevauchent, (2) l'énergie réelle (RMS 10 ms) de la source
autour de la borne. Une borne est SÛRE si elle tombe dans un creux d'énergie (< seuil) d'au moins 60 ms.
--fix : recale chaque borne sur le creux le plus proche (<= 0.35 s) et écrit un plan corrigé.
"""
import json, os, subprocess, sys
import array

WIN = 0.01


def rms_track(src, t0, t1):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", src, "-map", "0:a:0",
                        "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True)
    a = array.array("h"); a.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
    n = int(16000 * WIN)
    out = []
    for i in range(0, len(a) - n, n):
        seg = a[i:i + n]
        out.append((sum(x * x for x in seg) / n) ** 0.5)
    return out


def main():
    plan = json.load(open(sys.argv[1])); words = json.load(open(sys.argv[2]))["words"]
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[1]))), plan["source"])
    fix = sys.argv[sys.argv.index("--fix") + 1] if "--fix" in sys.argv else None
    bad = 0
    for sh in plan["shots"]:
        for ri, rg in enumerate(sh["ranges"]):
            for bi, t in enumerate(rg):
                lo, hi = t - 0.6, t + 0.6
                tr = rms_track(src, lo, hi)
                if not tr:
                    continue
                peak = max(tr) or 1
                thr = max(peak * 0.06, 120)
                i0 = int((t - lo) / WIN)
                quiet = [v < thr for v in tr]
                # creux autour de t : au moins 6 fenêtres (60 ms) silencieuses
                def ok_at(i):
                    return 0 <= i - 3 and i + 3 <= len(tr) and all(quiet[i - 3:i + 3])
                inside = [w["w"] for w in words if w["start"] + 0.02 < t < w["end"] - 0.02]
                safe = ok_at(i0)
                tag = "OK " if safe else "COUPE"
                if not safe:
                    bad += 1
                    # creux le plus proche
                    best = None
                    for d in range(0, 36):
                        for sgn in (1, -1):
                            if ok_at(i0 + sgn * d):
                                best = t + sgn * d * WIN; break
                        if best: break
                    if best and fix:
                        rg[bi] = round(best, 2)
                print(f"{tag} {sh['id']} r{ri} {'début' if bi == 0 else 'fin  '} {t:.2f}  mots dedans={inside}  creux≈{best if not safe else t}")
    print(f"{bad} bornes douteuses")
    if fix:
        json.dump(plan, open(fix, "w"), ensure_ascii=False, indent=1)


main()
