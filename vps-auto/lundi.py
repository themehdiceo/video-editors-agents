#!/usr/bin/env python3
"""Cron lundi 6h Maroc : 3 scripts à filmer + 14 histoires Pixar pour la semaine, dans le coffre, lien à Mehdi par Telegram."""
import sys, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import meta
from commun import VAULT, Verrou, journal, lancer_claude, maintenant, nouveau_job, tg_texte


def main() -> None:
    if maintenant().hour != 6 and "--force" not in sys.argv:
        return
    jour = f"{maintenant():%Y-%m-%d}"
    rel = f"Claude/Livrables/scripts-semaine/{jour}.md"
    sortie = VAULT / rel
    sortie.parent.mkdir(parents=True, exist_ok=True)
    chiffres = meta.resume()
    job = nouveau_job("scripts-semaine")
    prompt = (
        f"Agent scripts du lundi ({jour}). {chiffres}\n\n"
        "Utilise les skills anthropic-skills:copywriter-mehdi, anthropic-skills:conseil-des-mentors "
        "(Jérémy Haynes, Alex Hormozi, Dakota : anthropic-skills:jeremy-haynes-mehdi, anthropic-skills:alex-hormozi-offre, "
        "anthropic-skills:dakota-hermes-meta) et anthropic-skills:icp-debutant-mehdi. Applique la checklist QC et le tableau darija "
        "du copywriter. Lis aussi /root/vault/Claude/Agents/copywriter/lecons.md et kit-pixar-v1/2-style/lecons.md.\n"
        f"Écris dans {sortie} :\n"
        "1. 3 scripts à filmer (face caméra Mehdi, darija + français comme lui), chacun avec hook, corps, CTA, et l'avis court du conseil.\n"
        "2. 14 histoires Pixar NOUVELLES (2 par jour), 40-45 s, ICP salarié frustré, règles fixes du kit (README), "
        "fin Mercedes + villa, dialogues en darija. Chaque histoire relue par l'ICP.\n"
        "Écris aussi chaque histoire dans un fichier /root/vault/Claude/Livrables/pixar-nuit/a-valider/"
        f"{jour}-NN-titre.md au format de pixar-nuit/README.md (Mehdi la déplace dans histoires-validees/ = OK n°1).\n"
        "Pas de génération Higgsfield (0 crédit). Français simple, style Hormozi."
    )
    with Verrou(attente_s=2 * 3600):
        lancer_claude(job, prompt, budget=0, quoi="scripts de la semaine (3 à filmer + 14 Pixar)", minutes=25)
    if sortie.exists():
        lien = "obsidian://open?vault=" + urllib.parse.quote("Obsidian Vault") + "&file=" + urllib.parse.quote(rel[:-3])
        tg_texte(f"📝 Scripts de la semaine prêts : 3 à filmer + 14 Pixar.\n{lien}\n\n{chiffres[:500]}")
    else:
        tg_texte(f"⚠️ Scripts du lundi pas écrits. Journal : {job}/claude.log")
    journal(f"lundi : {'ok' if sortie.exists() else 'raté'}")


if __name__ == "__main__":
    main()
