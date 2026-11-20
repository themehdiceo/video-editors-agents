#!/usr/bin/env python3
"""Cron toutes les 15 min : prend la plus ancienne tâche de « Tâches VPS/ » dans le coffre et la fait avec claude -p.
Une seule tâche à la fois (verrou partagé avec la chaîne de nuit et l'agent du lundi).
Une tâche = un fichier .md (sauf README.md). Elle passe dans « en cours/ » puis « faites/ », résultat ajouté en bas.
"""
import shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import Verrou, VAULT, journal, lancer_claude, maintenant, nouveau_job, tg_texte

DOSSIER = VAULT / "Tâches VPS"
BUDGET = 60  # crédits max par tâche


def main() -> None:
    taches = sorted((p for p in DOSSIER.glob("*.md") if p.name != "README.md"), key=lambda p: p.stat().st_mtime)
    if not taches:
        return
    try:
        verrou = Verrou().__enter__()
    except BlockingIOError:
        return  # un autre job tourne : on réessaie dans 15 min
    try:
        src = taches[0]
        (DOSSIER / "en cours").mkdir(exist_ok=True)
        (DOSSIER / "faites").mkdir(exist_ok=True)
        tache = DOSSIER / "en cours" / src.name
        shutil.move(src, tache)
        demande = tache.read_text().strip()
        job = nouveau_job(src.stem)
        journal(f"tâche « {src.name} » -> {job.name}")
        prompt = (
            f"Tâche envoyée par Mehdi depuis son coffre Obsidian (fichier « {tache} ») :\n\n{demande}\n\n"
            f"Fais-la de bout en bout. Dossier de travail : {job}/ (work/, out/). Écris l'avancement dans {job}/progress.log.\n"
            "Règles :\n"
            "- Pixar / histoire animée / « comme Anas » : lis d'abord kit-pixar-v1/README.md et applique "
            "kit-pixar-v1/1-reglages/reglages-defaut.json. Respecte les 3 OK : écris l'histoire dans "
            "/root/vault/Claude/Livrables/pixar-nuit/a-valider/AAAA-MM-JJ-titre.md (modèle : pixar-nuit/README.md) "
            "et ARRÊTE-TOI là : pas d'image ni de vidéo sans l'OK n°1 de Mehdi, sauf si la tâche dit « sans validation ».\n"
            f"- Crédits Higgsfield : {BUDGET} max pour cette tâche, plafond 750/semaine (bloqué automatiquement). "
            "Annonce toujours crédits ET dollars (1 cr = 0,017 $). Jamais d'achat de crédits.\n"
            "- Copie, titre, offre, pub : fais travailler le copywriter (et Jérémy/conseil si choix entre options).\n"
            f"- Termine par {job}/out/resultat.md : 3 à 8 lignes en français simple, style direct, avec les chemins des livrables."
        )
        code = lancer_claude(job, prompt, BUDGET, quoi=f"tâche VPS « {src.stem} »", minutes=30)
        res = job / "out" / "resultat.md"
        texte = res.read_text().strip() if res.exists() else f"⚠️ Pas de résultat (code {code}). Journal : {job}/claude.log"
        with open(tache, "a") as f:
            f.write(f"\n\n---\n## Résultat ({maintenant():%Y-%m-%d %H:%M})\n\n{texte}\n")
        shutil.move(tache, DOSSIER / "faites" / tache.name)
        tg_texte(f"✅ Tâche VPS faite : {src.stem}\n\n{texte}")
    finally:
        verrou.__exit__()


if __name__ == "__main__":
    main()
