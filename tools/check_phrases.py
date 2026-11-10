#!/usr/bin/env python3
"""Garde-fou des coupes : chaque extrait gardé commence et finit-il sur une phrase complète ?

usage: check_phrases.py words.json keep.json [--allow 3,7]
- words.json : transcription mot à mot de la SOURCE (Scribe : champs w/start/end/speaker, ponctuation incluse).
  Prends la transcription d'origine (darija + français), jamais une version traduite.
- keep.json : liste [[début, fin], ...] en secondes de la source (ou {"ranges": [...]}).
- --allow : numéros d'extraits acceptés malgré une alerte (décision humaine notée dans la fiche).

Pour chaque extrait, le script affiche les premiers et derniers mots, et surtout les mots qui
SUIVENT la coupe : c'est là que se cachent les fins de phrase oubliées (« c'est la … continuité »).
Il échoue (code 1) si :
- la fin tombe au milieu d'un mot ;
- le dernier mot n'a pas de ponctuation finale et la même personne continue à parler dans la seconde qui suit ;
- le dernier mot est un mot-outil (la, de, que, pour, c'est, lli, dyal, f…), donc la phrase n'est pas finie ;
- le début tombe au milieu d'une phrase (le mot d'avant, même personne, < 0,8 s, sans ponctuation finale).
Lance-le AVANT tout rendu. Un échec = corriger les bornes depuis words.json, pas « à l'œil ».
"""
import json
import re
import sys

END_PUNCT = re.compile(r"[.?!…؟。]$")
FUNCTION = {
    # français
    "la", "le", "les", "l'", "de", "du", "des", "d'", "que", "qu'", "qui", "pour", "et", "mais", "c'est", "un", "une",
    "à", "a", "en", "dans", "avec", "ta", "ton", "tes", "ma", "mon", "mes", "sa", "son", "ses", "ce", "cette", "est",
    "par", "sur", "au", "aux", "donc", "parce", "si", "comme", "je", "tu", "il", "on", "nous", "vous", "ils", "y",
    # darija latine
    "f", "fi", "l", "w", "b", "dyal", "dyali", "lli", "bach", "3la", "m3a", "men", "ila", "wa7ed", "had", "hadi", "kima",
    # darija en lettres arabes
    "في", "ف", "اللي", "لي", "ديال", "و", "باش", "على", "مع", "من", "إلا", "واحد", "هاد", "هادي", "كيما", "بأن", "حيت",
}


def norm(w):
    return w["w"].strip().lower().strip(",،;:«»\"-— ")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    words = [w for w in json.load(open(sys.argv[1]))["words"] if "start" in w and w.get("w", "").strip()]
    words.sort(key=lambda w: w["start"])
    keep = json.load(open(sys.argv[2]))
    keep = keep["ranges"] if isinstance(keep, dict) else keep
    allow = set()
    if "--allow" in sys.argv:
        allow = {int(x) for x in sys.argv[sys.argv.index("--allow") + 1].split(",") if x}
    fails = 0
    for i, (a, b) in enumerate(keep):
        a, b = float(a), float(b)
        inside = [w for w in words if a <= (w["start"] + w["end"]) / 2 <= b]
        after = [w for w in words if (w["start"] + w["end"]) / 2 > b][:10]
        before = [w for w in words if (w["start"] + w["end"]) / 2 < a]
        prob = []
        for w in words:
            if w["start"] < b - 0.03 < w["end"] - 0.03 and (w["end"] - w["start"]) > 0.08:
                prob.append(f"fin au milieu du mot « {w['w']} »")
            if w["start"] + 0.03 < a < w["end"] - 0.03 and (w["end"] - w["start"]) > 0.08:
                prob.append(f"début au milieu du mot « {w['w']} »")
        if inside:
            last, first = inside[-1], inside[0]
            nxt = after[0] if after else None
            if not END_PUNCT.search(last["w"].strip()):
                if nxt and nxt.get("speaker") == last.get("speaker") and nxt["start"] - last["end"] < 1.0:
                    prob.append(f"phrase pas finie : « … {last['w']} » puis « {' '.join(x['w'] for x in after[:6])} »")
                if norm(last) in FUNCTION:
                    prob.append(f"finit sur un mot-outil « {last['w']} »")
            if before:
                prev = before[-1]
                if (prev.get("speaker") == first.get("speaker") and first["start"] - prev["end"] < 0.8
                        and not END_PUNCT.search(prev["w"].strip())):
                    prob.append(f"commence au milieu d'une phrase (avant : « {' '.join(x['w'] for x in before[-5:])} »)")
        else:
            prob.append("aucun mot dans l'extrait")
        status = "OK " if not prob else ("ACCEPTÉ" if i in allow else "ÉCHEC")
        if prob and i not in allow:
            fails += 1
        txt_in = " ".join(w["w"] for w in inside)
        if len(txt_in) > 160:
            txt_in = txt_in[:70] + " … " + txt_in[-80:]
        print(f"[{i}] {status} {a:.2f}-{b:.2f} ({b - a:.1f} s) : {txt_in}")
        print(f"      après la coupe : {' '.join(w['w'] for w in after[:8])}")
        for p in prob:
            print(f"      ⚠ {p}")
    print(f"\n{len(keep)} extraits, {fails} à corriger.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
