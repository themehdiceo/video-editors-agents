#!/usr/bin/env python3
"""Met un Pixar fini dans la file Instagram (Mehdi 2026-11-22 : 2 par jour, veto 2 h avant).
Fonction Supabase pixar-enqueue (projet PPC) : envoi de la vidéo (bucket public pixar-ig), puis ligne ppc_ig_posts
au prochain créneau libre 10h00 / 18h30 Maroc, depuis @themehdiceo en collab @profitpartnerscapital + @mehdiceotalks.
  publier.py VIDEO.mp4 "Titre" legende.txt HISTOIRE.md   -> imprime l'heure du créneau (refus si métier hors ICP)
"""
import json, sys, urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import MAROC, journal, secrets

FONCTION = "https://zbpvlcqfzanjflabpggf.supabase.co/functions/v1/pixar-enqueue"


def _appel(corps: dict) -> dict:
    req = urllib.request.Request(FONCTION, json.dumps(corps).encode(), method="POST", headers={
        "Content-Type": "application/json", "x-pixar-key": secrets()["PIXAR_ENQUEUE_SECRET"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def file_attente(video: Path, titre: str, legende: str, histoire: Path) -> str | None:
    """Renvoie l'heure Maroc du créneau (« lun. 23/11 18h30 ») ou None si raté ou refusé ICP (journalisé)."""
    import icp
    ok, raison = icp.verifier_metier(histoire, legende)  # garde-fou BLOQUANT (Mehdi 2026-11-24)
    if not ok:
        journal(f"file Instagram REFUSÉE (ICP) pour {titre} : {raison}")
        return None
    try:
        u = _appel({"action": "upload_url", "name": video.name})
        put = urllib.request.Request(u["signedUrl"], video.read_bytes(), method="PUT", headers={"Content-Type": "video/mp4"})
        urllib.request.urlopen(put, timeout=600).read()
        q = _appel({"action": "queue", "path": u["path"], "title": titre, "caption": legende})
        quand = datetime.fromisoformat(q["scheduled_at"].replace("Z", "+00:00")).astimezone(MAROC)
        journal(f"file Instagram : {titre} -> {quand:%Y-%m-%d %H:%M} (post {q['id']})")
        return f"{quand:%d/%m %Hh%M}"
    except Exception as e:
        journal(f"file Instagram ratée pour {titre} : {type(e).__name__} {e}")
        return None


if __name__ == "__main__":
    print(file_attente(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]).read_text().strip(), Path(sys.argv[4])))
