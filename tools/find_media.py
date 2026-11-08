#!/usr/bin/env python3
"""Cherche et télécharge de VRAIES images ou vidéos libres de droits, avec leurs crédits.

Usage: find_media.py "requête en anglais" <dossier_sortie> [--n 4] [--video] [--credits work/credits.json]

Sources sans clé : Openverse (images CC / domaine public) et Wikimedia Commons (images et vidéos).
Optionnel : PEXELS_API_KEY dans l'environnement -> vidéos Pexels (licence Pexels, sans crédit obligatoire).
Chaque fichier téléchargé est ajouté à credits.json : {file, title, author, license, source}.
Regarde ensuite les fichiers (tools/frames.py ou Read) : une recherche ramène aussi du hors-sujet.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "video-editors-agents/1.0 (montage video; usage personnel)"}


def get_json(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, path, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def openverse(q, n):
    url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
        {"q": q, "page_size": n * 2, "license_type": "commercial", "mature": "false"})
    out = []
    for r in get_json(url).get("results", []):
        if (r.get("width") or 0) < 800:
            continue
        out.append({"url": r["url"], "title": r.get("title"), "author": r.get("creator"),
                    "license": f"{r.get('license', '').upper()} {r.get('license_version', '')}".strip(),
                    "source": r.get("foreign_landing_url"), "kind": "image"})
    return out


def commons(q, n, video):
    ftype = "filetype:video" if video else "filetype:bitmap"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "generator": "search", "gsrsearch": f"{q} {ftype}",
        "gsrnamespace": 6, "gsrlimit": n * 2, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size", "iiurlwidth": 1920})
    out = []
    for p in (get_json(url).get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        if not video and (ii.get("width") or 0) < 800:
            continue
        out.append({"url": ii.get("url") if video else (ii.get("thumburl") or ii.get("url")),
                    "title": p.get("title", "").replace("File:", ""),
                    "author": strip_html(meta.get("Artist", {}).get("value")),
                    "license": strip_html(meta.get("LicenseShortName", {}).get("value")),
                    "source": ii.get("descriptionurl"), "kind": "video" if video else "image"})
    return out


def pexels(q, n):
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "per_page": n, "size": "medium"})
    out = []
    for v in get_json(url, {"Authorization": key}).get("videos", []):
        files = sorted((f for f in v.get("video_files", []) if (f.get("height") or 0) <= 1080),
                       key=lambda f: f.get("height") or 0, reverse=True)
        if files:
            out.append({"url": files[0]["link"], "title": v.get("url"), "author": v.get("user", {}).get("name"),
                        "license": "Pexels License", "source": v.get("url"), "kind": "video"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("outdir")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--credits", default=None, help="fichier credits.json (défaut : <outdir>/credits.json)")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    credits_path = a.credits or os.path.join(a.outdir, "credits.json")
    credits = json.load(open(credits_path)) if os.path.exists(credits_path) else []

    cands, errors = [], []
    sources = [lambda: pexels(a.query, a.n), lambda: commons(a.query, a.n, True)] if a.video else \
              [lambda: openverse(a.query, a.n), lambda: commons(a.query, a.n, False)]
    for src in sources:
        try:
            cands += src()
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))
    slug = re.sub(r"[^a-z0-9]+", "-", a.query.lower()).strip("-")[:40]
    got = 0
    for c in cands:
        if got >= a.n or not c.get("url"):
            continue
        ext = os.path.splitext(urllib.parse.urlparse(c["url"]).path)[1].lower() or (".mp4" if c["kind"] == "video" else ".jpg")
        if ext in (".svg", ".gif", ".tif", ".tiff", ".pdf"):
            continue
        path = os.path.join(a.outdir, f"{slug}-{got + 1}{ext}")
        try:
            download(c["url"], path)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{c['url']}: {e}")
            continue
        credits.append({"file": path, **{k: c[k] for k in ("title", "author", "license", "source")}})
        print(f"{path}  [{c['license']}] {c.get('title') or ''}")
        got += 1
    json.dump(credits, open(credits_path, "w"), ensure_ascii=False, indent=1)
    if errors:
        print("avertissements : " + " | ".join(errors[:3]), file=sys.stderr)
    if not got:
        print("Aucun résultat : essaie une requête plus simple, en anglais, ou --video.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
