"""Lance l'équipe Claude Code sur un job, en headless.

Sécurité : on ne désactive PAS les permissions. Les outils autorisés sont
listés dans .claude/settings.json (ffmpeg, yt-dlp, scripts de tools/, git des
skills, lecture web). Tout le reste est refusé automatiquement en mode -p.
Le service tourne sous un utilisateur dédié sans sudo.
"""
import asyncio
import json
import os
import time
from pathlib import Path

REPO = Path(os.environ.get("REPO_DIR", Path(__file__).resolve().parents[1]))
JOBS = Path(os.environ.get("JOBS_DIR", REPO / "jobs"))
TIMEOUT = int(os.environ.get("JOB_TIMEOUT_S", "7200"))

JOB_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Task", "WebFetch", "WebSearch",
    "Bash(python3 *)", "Bash(python *)", "Bash(ffmpeg *)", "Bash(ffprobe *)", "Bash(yt-dlp *)",
    "Bash(npx -y hyperframes@0.9.22 *)", "Bash(ls *)", "Bash(head *)", "Bash(tail *)", "Bash(wc *)",
    "Bash(cp *)", "Bash(mkdir *)", "Bash(git add *)", "Bash(git commit *)", "Bash(git log *)", "Bash(git diff *)",
]

PROMPTS = {
    "script": "Job de type script. Suis la skill short-script, après avoir fait travailler l'agent chercheur.",
    "edit": "Job de type edit. Suis la skill short-editor.",
    "clip": "Job de type clip. Suis la skill long-to-short.",
    "feedback": ("Job de type feedback : Mehdi a donné un retour sur le job d'origine indiqué dans job.json "
                 "(champ parent). Refais une version corrigée en repartant des fichiers de work/ du job d'origine "
                 "(copie-les), puis applique la skill skill-keeper pour que ce retour serve aux prochaines vidéos."),
    "bilan": "Job de type bilan. Suis la section /bilan de la skill skill-keeper.",
}


def new_job(kind: str, **fields) -> Path:
    jid = time.strftime("%Y%m%d-%H%M%S") + f"-{kind}"
    d = JOBS / jid
    for sub in ("input", "work", "out"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "job.json").write_text(json.dumps({"id": jid, "type": kind, **fields}, ensure_ascii=False, indent=1))
    (d / "progress.log").touch()
    return d


async def run_job(job_dir: Path) -> int:
    job = json.loads((job_dir / "job.json").read_text())
    rel = job_dir.relative_to(REPO)
    prompt = (
        f"Nouveau job : dossier {rel}/. Lis {rel}/job.json. {PROMPTS[job['type']]} "
        f"Tous les chemins work/, out/, input/ et progress.log sont relatifs à {rel}/. "
        f"Écris l'avancement dans {rel}/progress.log au fil de l'eau et termine par {rel}/out/summary.md."
    )
    # Permissions : celles de .claude/settings.json (liste blanche), rien de plus.
    # --setting-sources project,local : on ignore les plugins et hooks personnels de l'utilisateur
    # (ils changent le comportement des agents) ; seuls les réglages du dépôt comptent.
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "project,local",
           # acceptEdits : écritures de fichiers dans le dépôt (jobs/) acceptées ;
           # les commandes shell restent limitées à la liste blanche de .claude/settings.json.
           "--permission-mode", "acceptEdits",
           # Commandes shell autorisées pour les jobs (« programme * » = toute commande qui commence par ce programme).
           "--allowedTools", *JOB_TOOLS]
    if os.environ.get("CLAUDE_MODEL"):
        cmd += ["--model", os.environ["CLAUDE_MODEL"]]
    with open(job_dir / "claude.log", "wb") as log:
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=REPO, stdout=log, stderr=asyncio.subprocess.STDOUT)
        try:
            return await asyncio.wait_for(proc.wait(), TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            with open(job_dir / "progress.log", "a") as p:
                p.write(f"Temps maximum dépassé ({TIMEOUT // 60} min), job arrêté.\n")
            return -1
