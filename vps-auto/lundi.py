#!/usr/bin/env python3
"""Cron lundi 6h Maroc : 14 histoires Pixar pour la semaine (Pixar SEULEMENT), dans le coffre, lien à Mehdi par Telegram."""
import sys, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commun as _c
_c.SUJET = "🎬 Pixar"
import meta
from commun import ETAT, VAULT, Verrou, journal, lancer_claude, maintenant, nouveau_job, pret, tg_texte


def main() -> None:
    if maintenant().hour != 6 and "--force" not in sys.argv:
        return
    import time
    recents = [f for f in (VAULT / "Claude/Livrables/scripts-semaine").glob("*.md") if time.time() - f.stat().st_mtime < 3 * 86400]
    if recents and "--force" not in sys.argv:  # semaine déjà écrite (lancement anticipé) : pas de doublon
        journal(f"lundi : déjà fait ({recents[0].name})")
        return
    if (ETAT / "pixar-gel").exists():
        journal("lundi : automatique Pixar gelé (etat/pixar-gel)")
        return
    if not pret("les histoires du lundi"):
        return
    jour = f"{maintenant():%Y-%m-%d}"
    rel = f"Claude/Livrables/scripts-semaine/{jour}.md"
    sortie = VAULT / rel
    sortie.parent.mkdir(parents=True, exist_ok=True)
    chiffres = meta.resume()
    job = nouveau_job("scripts-semaine")
    prompt = (
        f"Agent du lundi ({jour}). C'est JÉRÉMY (anthropic-skills:jeremy-haynes-mehdi), chef de l'équipe marketing, qui pilote : "
        "il choisit les 14 histoires, fait le classement organique et les propositions de pub ; il consulte le copywriter, l'ICP, "
        "le conseil ou Dakota si besoin, puis il tranche. Lis ses leçons : /root/vault/Claude/Agents/jeremy-haynes/lecons.md.\n"
        f"{chiffres}\n\n"
        "Utilise les skills anthropic-skills:copywriter-mehdi, anthropic-skills:conseil-des-mentors "
        "(Jérémy Haynes, Alex Hormozi, Dakota : anthropic-skills:jeremy-haynes-mehdi, anthropic-skills:alex-hormozi-offre, "
        "anthropic-skills:dakota-hermes-meta) et anthropic-skills:icp-debutant-mehdi. Applique la checklist QC et le tableau darija "
        "du copywriter. Lis aussi /root/vault/Claude/Agents/copywriter/lecons.md et kit-pixar-v1/2-style/lecons.md.\n"
        f"Écris dans {sortie} :\n"
        "A. Le classement ORGANIQUE (chiffres ci-dessus) : top 10 des reels par leads organiques, relié aux histoires du registre, "
        "+ les 2-3 Pixar à proposer à Mehdi pour un test en publicité (rien n'est publié : c'est Mehdi qui décide).\n"
        "B. Prends les 14 PROCHAINES idées au statut « à faire » de kit-pixar-v1/2-style/banque-histoires-6-mois.md (dans l'ordre ; "
        "Jérémy peut en échanger une s'il a une raison chiffrée) et développe-les en 14 histoires Pixar (2 par jour, Mehdi 2026-11-23). "
        "ICP VERROUILLÉ : héros = salarié 25-35 ans, 6 000-10 000 dh, métier UNIQUEMENT dans la liste officielle de kit-pixar-v1/2-style/matrice-histoires.md § 1 ; une idée de la banque avec un métier interdit = remplace-la par la suivante. "
        "TEMPS FORTS : GELÉS (2026-11-23), ne les utilise pas. Écris « grille: N » (le N de la banque) "
        "dans chaque histoire et dans sa ligne du registre, + « grille: N » (le N de la banque) dans le frontmatter. Darija : kit-pixar-v1/2-style/darija-pixar.md. Chaque plan a une colonne « Logique du lieu ». Jamais une phrase reprise d'une autre histoire. "
        "Passe leur statut à « écrite ». Histoire ≤ 42 s + fin 3 s, ICP salarié frustré, dialogues en darija, "
        "règles fixes du kit (README). VARIÉTÉ OBLIGATOIRE : lis kit-pixar-v1/2-style/matrice-histoires.md et "
        "kit-pixar-v1/2-style/registre-histoires.md. Chaque histoire prend une case nouvelle (métier × douleur × objection × raison "
        "d'acheter × fin) ; jamais le même métier + la même objection qu'une histoire des 30 derniers jours ; varie homme/femme, âge, ville. "
        "Les 1-2 gagnantes en organique reviennent en variantes de HOOK (scène 1 réécrite, le reste identique), comptées dans les 14. "
        "STRUCTURE (gel Jérémy + Mehdi 2026-11-23) : moule M1 EXACT du prof v3 (kit-pixar-v1/3-exemple-prof-v3/structure.md : 13 scènes, même ordre, mêmes durées) ; les squelettes O-X-F et la colonne S de la grille sont GELÉS (écris « moule: M1 »). 1re phrase = qui il est + métier + 1 chiffre, claire en 1 s. Titre « (titre à écrire) » : écris-le (darija latine · français). "
        "Règle Video Editor : le moins cher pour le meilleur résultat = réutiliser la banque (kit-pixar-v1/5-banque-pixar/INDEX.md) "
        "quand la scène s'y prête, mais jamais d'histoire pensée pour économiser des crédits. Chaque histoire relue par l'ICP. "
        "AUCUN script à filmer.\n"
        "C. Ajoute une ligne par nouvelle histoire dans /root/vault/Claude/Livrables/kit-pixar-v1/2-style/registre-histoires.md.\n"
        "Écris aussi chaque histoire dans un fichier /root/vault/Claude/Livrables/pixar-nuit/histoires-validees/"
        f"{jour}-NN-titre.md au format de pixar-nuit/README.md, avec « ok1: jeremy » (Jérémy valide = OK n°1 ; "
        "Mehdi garde un veto : la nuit en fabrique 2, dans l'ordre NN).\n"
        "Pas de génération Higgsfield (0 crédit). Français simple, style Hormozi."
    )
    with Verrou(attente_s=2 * 3600):
        lancer_claude(job, prompt, budget=0, quoi="classement organique + 14 histoires Pixar de la semaine", minutes=30,
                      outils=meta.OUTILS)
    if sortie.exists():
        lien = "obsidian://open?vault=" + urllib.parse.quote("Obsidian Vault") + "&file=" + urllib.parse.quote(rel[:-3])
        tg_texte(f"📝 Classement organique + 14 histoires Pixar de la semaine prêts (les 2-3 à tester en pub sont en haut).\n{lien}\n\n"
                 "Réponds dans Claude : « ok » ou tes corrections, en texte libre.")
    else:
        tg_texte(f"⚠️ Scripts du lundi pas écrits. Journal : {job}/claude.log")
    journal(f"lundi : {'ok' if sortie.exists() else 'raté'}")


if __name__ == "__main__":
    main()
