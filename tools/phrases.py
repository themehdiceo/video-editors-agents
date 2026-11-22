#!/usr/bin/env python3
"""Découpe la transcription en phrases numérotées (idées complètes, coupes sûres) pour le mode guidé.

usage: phrases.py work/words.json work/phrases.json [--max 14]
Chaque phrase : n, start, end, speaker, text (texte brut de la transcription), cough (toux dedans).
L'équipe ajoute ensuite `latin` (darija en lettres latines) et écrit out/phrases.md.
"""
import json
import re
import sys

END_RE = re.compile(r"[.?!؟…]+[\"»”']*$")
GAP = 0.7       # silence qui sépare deux phrases
MIN_DUR = 1.8   # plus court : fusionné avec la voisine
MAX_DUR = float(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 14.0


def text_of(ws):
    return " ".join(w["w"] for w in ws).strip()


def split_long(ws):
    """Phrase trop longue : on coupe au plus grand silence (jamais au milieu d'un mot)."""
    if ws[-1]["end"] - ws[0]["start"] <= MAX_DUR or len(ws) < 6:
        return [ws]
    best, gap = None, -1.0
    for i in range(2, len(ws) - 2):
        g = ws[i]["start"] - ws[i - 1]["end"] + (0.3 if END_RE.search(ws[i - 1]["w"]) or ws[i - 1]["w"].endswith(",") else 0)
        if g > gap:
            best, gap = i, g
    return split_long(ws[:best]) + split_long(ws[best:])


def main():
    src, out = sys.argv[1], sys.argv[2]
    data = json.load(open(src))
    words = [w for w in data["words"] if str(w.get("w", "")).strip()]
    events = data.get("events", [])
    groups, cur = [], []
    for w in words:
        if cur and (w.get("speaker") != cur[-1].get("speaker") or w["start"] - cur[-1]["end"] > GAP):
            groups.append(cur)
            cur = []
        cur.append(w)
        if END_RE.search(w["w"]):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    # Fusion des fragments trop courts avec la phrase suivante du même locuteur.
    merged = []
    for g in groups:
        if merged and merged[-1][-1].get("speaker") == g[0].get("speaker") and (
                merged[-1][-1]["end"] - merged[-1][0]["start"] < MIN_DUR) and g[0]["start"] - merged[-1][-1]["end"] < 1.5:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    # Fragment court restant (fin de tour de parole) : collé à la phrase précédente du même locuteur.
    final = []
    for g in merged:
        if final and g[-1]["end"] - g[0]["start"] < MIN_DUR and final[-1][-1].get("speaker") == g[0].get("speaker") \
                and g[0]["start"] - final[-1][-1]["end"] < 1.5:
            final[-1] = final[-1] + g
        else:
            final.append(g)
    phrases = []
    for g in final:
        for part in split_long(g):
            s, e = part[0]["start"], part[-1]["end"]
            cough = any(ev.get("start", 0) < e and ev.get("end", 0) > s for ev in events
                        if re.search(r"cough|tou|throat|gorge|سعال|كحة|يكح|يسعل", str(ev.get("event", "")) + str(ev.get("type", "")), re.I))
            phrases.append({"n": len(phrases) + 1, "start": round(s, 2), "end": round(e, 2),
                            "speaker": part[0].get("speaker"), "text": text_of(part), "cough": cough})
    json.dump({"phrases": phrases}, open(out, "w"), ensure_ascii=False, indent=1)
    print(len(phrases), "phrases ->", out)


if __name__ == "__main__":
    main()
