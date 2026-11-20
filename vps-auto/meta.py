#!/usr/bin/env python3
"""Chiffres Meta de la semaine (Supabase meta_daily_insights) + règle Dakota : 12-14 $ dépensés sans lead = pub coupée.
DÉSACTIVÉ tant que SUPABASE_SERVICE_KEY manque dans /etc/video-editors-agents/.env (message clair, code 0).
ponytail: noms de colonnes supposés (ad_name, spend, leads, date) : à vérifier au 1er lancement avec la vraie clé.
"""
import json, sys, urllib.request
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import secrets

SEUIL_COUPE = 12  # $ dépensés sans lead (règle Dakota 12-14 $)


def resume() -> str:
    s = secrets()
    if not s.get("SUPABASE_SERVICE_KEY") or not s.get("SUPABASE_URL"):
        return ("Chiffres Meta : DÉSACTIVÉ (SUPABASE_SERVICE_KEY manque dans /etc/video-editors-agents/.env). "
                "Scripts écrits sans les chiffres de la semaine.")
    depuis = (date.today() - timedelta(days=7)).isoformat()
    url = f"{s['SUPABASE_URL'].rstrip('/')}/rest/v1/meta_daily_insights?select=*&date=gte.{depuis}"
    req = urllib.request.Request(url, headers={"apikey": s["SUPABASE_SERVICE_KEY"],
                                               "Authorization": f"Bearer {s['SUPABASE_SERVICE_KEY']}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        lignes = json.load(r)
    pubs = {}
    for l in lignes:
        p = pubs.setdefault(l.get("ad_name") or l.get("ad_id") or "?", {"spend": 0.0, "leads": 0})
        p["spend"] += float(l.get("spend") or 0)
        p["leads"] += int(l.get("leads") or 0)
    coupees = [n for n, p in pubs.items() if p["leads"] == 0 and p["spend"] >= SEUIL_COUPE]
    gagnantes = sorted((n for n, p in pubs.items() if p["leads"]), key=lambda n: pubs[n]["spend"] / pubs[n]["leads"])[:5]
    return ("Chiffres Meta 7 jours :\n" + "\n".join(
        f"- {n} : {p['spend']:.0f} $, {p['leads']} leads" for n, p in sorted(pubs.items(), key=lambda x: -x[1]["spend"])[:20])
        + f"\nÀ couper (≥ {SEUIL_COUPE} $ sans lead) : {', '.join(coupees) or 'aucune'}"
        + f"\nMeilleur coût/lead : {', '.join(gagnantes) or '—'}")


if __name__ == "__main__":
    print(resume())
