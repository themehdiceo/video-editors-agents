#!/usr/bin/env python3
"""Cron toutes les 15 min : prend la plus ancienne tâche de « Tâches VPS/ » dans le coffre et la fait avec claude -p.
Une seule tâche à la fois (verrou partagé avec la chaîne de nuit et l'agent du lundi).
Une tâche = un fichier .md (sauf README.md). Elle passe dans « en cours/ » puis « faites/ », résultat ajouté en bas.
Avant les tâches : les réponses de Mehdi (texte libre) écrites par Claude dans « Tâches VPS/réponses/ »
ou par le bot Telegram dans etat/reponses-tg/ sont appliquées au circuit Pixar (OK, refus, corrections).
"""
import shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commun as _c
_c.SUJET = "🛠️ VPS"
from commun import ETAT, Verrou, VAULT, journal, lancer_claude, maintenant, nouveau_job, pret, tg_texte

DOSSIER = VAULT / "Tâches VPS"
BUDGET = 60  # crédits max par tâche
REPONSES = [DOSSIER / "réponses", ETAT / "reponses-tg"]


def reponses() -> None:
    """Applique les réponses de Mehdi (« ok », « non », « change la scène 3… ») : 0 crédit, pas de génération."""
    fichiers = sorted((p for d in REPONSES if d.is_dir() for p in d.iterdir()
                       if p.is_file() and p.suffix in (".md", ".txt") and p.name != "README.md"), key=lambda p: p.stat().st_mtime)
    if not fichiers:
        return
    textes = "\n\n".join(f"[{p.name}]\n{p.read_text().strip()}" for p in fichiers)
    job = nouveau_job("reponses-mehdi")
    prompt = (
        f"Réponses de Mehdi en texte libre, à appliquer au circuit Pixar :\n\n{textes}\n\n"
        "Circuit : /root/vault/Claude/Livrables/pixar-nuit/README.md (lis-le). Ce que veut dire chaque réponse :\n"
        "- OK n°1 d'une histoire de a-valider/ : déplace le fichier dans histoires-validees/.\n"
        "- OK sur une planche : « ok2: oui » dans le frontmatter. OK sur une vidéo : « ok3: oui ».\n"
        "- Refus d'une vidéo : « ok3: refus » + « plans_critiques: s3, s7 » (les plans qu'il critique).\n"
        "- Correction (« change la scène 3… ») : applique-la dans le texte de l'histoire, remets « planche: » et « ok2: » à vide "
        "si les images changent, et ajoute 1 ligne datée dans /root/vault/Claude/Livrables/kit-pixar-v1/2-style/lecons.md.\n"
        "- Chiffres organiques ou d'une pub : ajoute-les dans /root/vault/Claude/Livrables/kit-pixar-v1/2-style/registre-histoires.md.\n"
        "Histoire non nommée : prends celle qui attend une réponse le plus récemment (planche avec ok2: non, ou vidéo avec ok3: non). "
        "Si c'est vraiment ambigu : ne touche à rien et écris la question courte dans out/resultat.md. "
        "Aucun outil Higgsfield, aucune génération, aucune publication. "
        f"Termine par {job}/out/resultat.md : 1 à 4 lignes, ce que tu as changé."
    )
    lancer_claude(job, prompt, 0, quoi="j'applique ta réponse", minutes=3)
    res = job / "out" / "resultat.md"
    for p in fichiers:
        fait = p.parent / "faites"
        fait.mkdir(exist_ok=True)
        shutil.move(p, fait / p.name)
    tg_texte("✅ Réponse appliquée :\n" + (res.read_text().strip() if res.exists() else f"⚠️ pas de résultat, journal {job}/claude.log"))


def main() -> None:
    try:
        with Verrou():
            reponses()
    except BlockingIOError:
        pass  # un job tourne : réponses appliquées dans 15 min
    taches = sorted((p for p in DOSSIER.glob("*.md") if p.name != "README.md"), key=lambda p: p.stat().st_mtime)
    if not taches or not pret("les tâches VPS"):
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
