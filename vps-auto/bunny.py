#!/usr/bin/env python3
"""Envoi d'une vidéo validée (OK n°3) dans Bunny Stream, collection « Stories AI Funnels ».
  bunny.py envoyer video.mp4 "AAAA-MM-JJ · Titre"   -> imprime l'id Bunny si l'upload est vérifié
  bunny.py collections                              -> liste les collections (contrôle)
La suppression locale est faite par l'appelant (nuit.py bunny) SEULEMENT si envoyer() renvoie un id.
"""
import json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import journal, secrets

COLLECTION = "Stories AI Funnels"


def _api(methode: str, chemin: str, corps=None, brut: bytes | None = None):
    s = secrets()
    url = f"https://video.bunnycdn.com/library/{s['BUNNY_LIBRARY_ID']}{chemin}"
    data = brut if brut is not None else (json.dumps(corps).encode() if corps is not None else None)
    req = urllib.request.Request(url, data, method=methode, headers={
        "AccessKey": s["BUNNY_STREAM_API_KEY"], "Accept": "application/json",
        "Content-Type": "application/octet-stream" if brut is not None else "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        t = r.read()
        return json.loads(t) if t else {}


def collection_id() -> str:
    for c in _api("GET", f"/collections?search={urllib.request.quote(COLLECTION)}&itemsPerPage=100").get("items", []):
        if c["name"] == COLLECTION:
            return c["guid"]
    return _api("POST", "/collections", {"name": COLLECTION})["guid"]


def envoyer(video: Path, titre: str) -> str | None:
    try:
        vid = _api("POST", "/videos", {"title": titre, "collectionId": collection_id()})["guid"]
        _api("PUT", f"/videos/{vid}", brut=video.read_bytes())
        for _ in range(60):  # vérifie : encodage fini (4) ou au moins reçu sans erreur
            v = _api("GET", f"/videos/{vid}")
            if v.get("status") in (5, 6):
                raise RuntimeError(f"Bunny status {v.get('status')} (erreur d'encodage)")
            if v.get("status") in (3, 4) and v.get("storageSize", 0) > 0:
                journal(f"Bunny OK : {titre} -> {vid}")
                return vid
            time.sleep(10)
        raise RuntimeError("encodage pas fini après 10 min")
    except Exception as e:
        journal(f"Bunny raté pour {titre} : {type(e).__name__} {e}")
        return None


if __name__ == "__main__":
    if sys.argv[1:2] == ["envoyer"]:
        r = envoyer(Path(sys.argv[2]), sys.argv[3])
        print(r or "ÉCHEC")
        sys.exit(0 if r else 1)
    print([c["name"] for c in _api("GET", "/collections?itemsPerPage=100").get("items", [])])
