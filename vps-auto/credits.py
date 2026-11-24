#!/usr/bin/env python3
"""Plafond de crédits Higgsfield : 750 / semaine (lundi→dimanche, heure du Maroc). Jamais d'achat.

Branché en hook sur chaque génération Higgsfield (claude-settings.json) :
  credits.py avant   (PreToolUse)  -> estime le coût, BLOQUE si semaine > PLAFOND ou job > CREDITS_JOB_MAX, prévient Mehdi
  credits.py apres   (PostToolUse) -> ajoute l'estimation au compteur
  credits.py etat                  -> affiche le compteur de la semaine
  credits.py test                  -> auto-contrôle
Estimation volontairement haute (Seedance 720p = 4,5 cr/s, autre vidéo = 9 cr/s, Nano Banana 2 = 1,5 cr, autre image = 3 cr).
"""
import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ETAT, journal, maintenant, tg_texte

PLAFOND = 1500  # Mehdi 2026-11-23 : 3 Pixar/jour en Kling (21 × ≈ 70 cr)
DOLLAR = 0.017  # 1 crédit Ultra
FICHIER = ETAT / "credits.json"
TAUX_VIDEO = {"kling_4_0_flash": 1.5, "kling3_0_turbo": 1.5, "wan2_6": 1.5, "minimax_hailuo": 1.0, "grok_video_v15_lite": 1.0}


def semaine() -> str:
    y, w, _ = maintenant().isocalendar()  # ISO = lundi→dimanche
    return f"{y}-S{w:02d}"


def _demandes(x):
    """Toutes les demandes de génération (dicts avec 'model') dans l'entrée de l'outil."""
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except ValueError:
            return []
    if isinstance(x, dict):
        if "model" in x:
            return [x]
        return [d for v in x.values() for d in _demandes(v)]
    if isinstance(x, list):
        return [d for v in x for d in _demandes(v)]
    return []


def estimer(outil: str, entree: dict) -> float:
    total = 0.0
    for d in _demandes(entree) or [{}]:
        n = int(d.get("count") or 1)
        if "video" in outil:
            res, mod = str(d.get("resolution", "720p")), str(d.get("model", ""))
            # crédits par seconde, devis Higgsfield 2026-11-23 (9:16) ; modèle inconnu = 9/s (prudent)
            taux = TAUX_VIDEO.get(mod, 9.0)
            if mod == "seedance_2_0":
                taux = 3.0 if "480" in res else 4.5
            total += n * taux * float(d.get("duration") or 5)
        else:
            total += n * (1.5 if d.get("model") == "nano_banana_2" else 3.0)
    return round(total, 1)


def charger() -> dict:
    d = json.loads(FICHIER.read_text()) if FICHIER.exists() else {}
    return d if d.get("semaine") == semaine() else {"semaine": semaine(), "depense": 0.0, "lignes": [], "alerte": False}


def depense_job() -> float:
    f = Path(os.environ.get("JOB_DIR", "/nonexistent")) / "credits.json"
    return json.loads(f.read_text())["depense"] if f.exists() else 0.0


def verifier(cout: float) -> str | None:
    """None si OK, sinon la raison du refus."""
    d = charger()
    # EXCEPTION_MEHDI : seulement pour un job que Mehdi a validé lui-même (ex. « go test » du 20/11) ; le budget du job reste bloquant.
    if d["depense"] + cout > PLAFOND and not os.environ.get("EXCEPTION_MEHDI"):
        return (f"Plafond hebdo atteint : {d['depense']:.0f} + {cout:.0f} > {PLAFOND} crédits "
                f"(≈ {PLAFOND * DOLLAR:.2f} $). Arrêt jusqu'à lundi. JAMAIS d'achat de crédits.")
    job_max = float(os.environ.get("CREDITS_JOB_MAX") or PLAFOND)
    if depense_job() + cout > job_max:
        return f"Budget du job dépassé : {depense_job():.0f} + {cout:.0f} > {job_max:.0f} crédits. Prends des plans moins chers (banque = 0 cr, image animée) ou arrête-toi."
    return None


def ajouter(cout: float, quoi: str) -> None:
    d = charger()
    d["depense"] = round(d["depense"] + cout, 1)
    d["lignes"].append({"quand": f"{maintenant():%Y-%m-%d %H:%M}", "cout": cout, "quoi": quoi})
    FICHIER.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    if os.environ.get("JOB_DIR"):
        f = Path(os.environ["JOB_DIR"]) / "credits.json"
        j = json.loads(f.read_text()) if f.exists() else {"depense": 0.0}
        j["depense"] = round(j["depense"] + cout, 1)
        f.write_text(json.dumps(j))


def hook(mode: str) -> int:
    ev = json.load(sys.stdin)
    outil, entree = ev.get("tool_name", ""), ev.get("tool_input", {})
    if "generate_" not in outil:
        return 0
    cout = estimer(outil, entree)
    if mode == "avant":
        raison = verifier(cout)
        if raison:
            d = charger()
            if "hebdo" in raison and not d.get("alerte"):
                tg_texte(f"⛔ {raison}\nDépensé cette semaine : {d['depense']:.0f} cr (≈ {d['depense'] * DOLLAR:.2f} $).")
                d["alerte"] = True
                FICHIER.write_text(json.dumps(d, ensure_ascii=False, indent=1))
            journal(f"génération refusée ({cout} cr) : {raison}")
            print(raison, file=sys.stderr)
            return 2  # bloque l'appel
        return 0
    ajouter(cout, outil.split("__")[-1])
    return 0


def test() -> None:
    import tempfile
    global FICHIER
    FICHIER = Path(tempfile.mkdtemp()) / "c.json"
    os.environ["JOB_DIR"] = str(FICHIER.parent)
    os.environ["CREDITS_JOB_MAX"] = "60"
    assert estimer("x__generate_video", {"params": {"model": "seedance_2_0", "duration": 5, "resolution": "720p"}}) == 22.5
    assert estimer("x__generate_image", {"params": json.dumps({"model": "nano_banana_2", "count": 2})}) == 3.0
    assert estimer("x__generate_image_batch", {"requests": [{"model": "nano_banana_2"}] * 4}) == 6.0
    assert verifier(22.5) is None
    ajouter(45, "t")
    assert verifier(22.5) and "job" in verifier(22.5)
    os.environ["CREDITS_JOB_MAX"] = "9999"
    ajouter(700, "t")
    assert "hebdo" in verifier(10)
    print("credits.py : test OK")


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "etat"
    if a in ("avant", "apres"):
        sys.exit(hook(a))
    if a == "test":
        test()
    else:
        d = charger()
        print(f"Semaine {d['semaine']} : {d['depense']:.0f} / {PLAFOND} crédits (≈ {d['depense'] * DOLLAR:.2f} $ / {PLAFOND * DOLLAR:.2f} $)")
