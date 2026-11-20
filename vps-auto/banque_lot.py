#!/usr/bin/env python3
"""Lots de la banque Pixar 6 mois (OK Mehdi « ok banque » 20/11) : lundi 23/11 et lundi 30/11, 10h Maroc.
41 images par lot, 123 cr max par lot (2 essais max par image), sous le plafond 750/semaine (hook credits.py).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ETAT, Verrou, boite_matin, journal, lancer_claude, maintenant, nouveau_job, pret

LOTS = {"2026-11-23": 1, "2026-11-30": 2}
BUDGET = 123
PLAN = "/root/vault/Claude/Livrables/kit-pixar-v1/5-banque-pixar/plan-banque-6-mois.md"
BANQUE = "/root/vault/Claude/Livrables/kit-pixar-v1/5-banque-pixar"


def main() -> None:
    jour = f"{maintenant():%Y-%m-%d}"
    lot = LOTS.get(jour)
    fait = ETAT / f"banque-lot{lot}.ok"
    if not lot or fait.exists() or (maintenant().hour != 10 and "--force" not in sys.argv):
        return
    if not pret(f"le lot {lot} de la banque Pixar"):
        return
    job = nouveau_job(f"banque-lot{lot}")
    prompt = (
        f"Lot {lot} de la banque Pixar 6 mois, validé par Mehdi (« ok banque »). Lis {PLAN} (section 6 : la liste du lot {lot}, "
        "dans l'ordre), kit-pixar-v1/2-style/STYLE.md, kit-pixar-v1/2-style/lecons.md, kit-pixar-v1/5-banque-pixar/INDEX.md, "
        "et la planche du modèle kit-pixar-v1/3-exemple-prof-v3/planche-fin-v3.jpg (même style Pixar exactement).\n"
        "Pour chaque ligne du lot : 1 image Nano Banana 2 (vertical 9:16, style Pixar du modèle, Maroc réaliste, règles fixes du kit), "
        "2 essais MAX par image (garde la meilleure). Personnage : fiche de référence plein pied, fond neutre ; la tenue « succès » "
        "reprend le même visage (même Element). Décor : sans personnage. "
        "Enregistre chaque personnage et chaque décor gardé dans Higgsfield Elements (manage_reference_elements). "
        f"Range les images dans {BANQUE}/personnages/ ou {BANQUE}/decors/ (nom en minuscules, ex. perso-infirmiere-F-travail.png) "
        f"et ajoute une ligne par élément dans {BANQUE}/INDEX.md (§ 1 personnages ou § 2 décors : nom, ID Element, fichier, date, crédits). "
        f"Coche la ligne dans {PLAN} (« - [x] »). Fais une planche contact de tout le lot dans {job}/out/planche.jpg. "
        f"Budget : {BUDGET} crédits MAX (bloqué au-delà), plafond 750/semaine. S'il manque des crédits : arrête-toi, "
        "écris ce qui reste à faire dans out/resultat.md, jamais d'achat. Vérifie le coût avec estimate_image_cost avant. "
        f"Écris {job}/out/cout.md (crédits ET dollars, 1 cr = 0,017 $) et {job}/out/resultat.md (3 à 6 lignes : fait, reste, coût)."
    )
    with Verrou(attente_s=2 * 3600):
        lancer_claude(job, prompt, BUDGET, quoi=f"lot {lot}/2 de la banque Pixar (41 images : persos + décors)", minutes=60)
    res = job / "out/resultat.md"
    texte = res.read_text().strip() if res.exists() else f"⚠️ Pas de résultat. Journal : {job}/claude.log"
    cout = (job / "out/cout.md").read_text().strip() if (job / "out/cout.md").exists() else ""
    planche = job / "out/planche.jpg"
    boite_matin(f"🗂️ Banque Pixar, lot {lot}/2 :\n{texte}\n{cout}\n\nUn perso ou un décor à refaire ? Dis-le dans Claude.",
                str(planche) if planche.exists() else None)
    fait.touch()
    journal(f"banque lot {lot} : {'ok' if res.exists() else 'raté'}")


if __name__ == "__main__":
    main()
