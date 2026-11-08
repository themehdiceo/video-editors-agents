"""Lance l'équipe Claude Code sur un job, en headless.

Sécurité : on ne désactive PAS les permissions. Les outils autorisés sont
listés dans .claude/settings.json (ffmpeg, yt-dlp, scripts de tools/, git des
skills, lecture web). Tout le reste est refusé automatiquement en mode -p.
Le service tourne sous un utilisateur dédié sans sudo.
"""
import asyncio
import json
import os
import re
import sys
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

# Transcription faite par le bot AVANT de lancer Claude : pas de limite de 10 min par commande,
# et pas de session Claude consommée pendant le calcul.
BIG_MODEL = os.environ.get("WHISPER_BIG_MODEL", "large-v3-turbo")
DARIJA_RE = re.compile(r"darija|marocain|arabe", re.I)
HINT = "Interview en darija marocaine mélangée au français. Mehdi, Anas, Profit Partners, salarié, boutique, e-commerce, Shopify, dirham, dollars."

PROMPTS = {
    "script": "Job de type script. Suis la skill short-script, après avoir fait travailler l'agent chercheur.",
    "edit": ("Job de type edit. Suis la skill short-editor. Si job.json contient history, ce sont les consignes "
             "déjà données sur cette même vidéo : applique-les aussi."),
    "plan": ("Job de type edit, phase plan. Suis la skill edit-plan : prépare les coupes et écris out/plan.md "
             "avec 4 idées de scène par ligne. Ne monte pas la vidéo finale."),
    "build": ("Job de type edit, phase build : Mehdi a validé le plan (champ choices de job.json, plan dans work/plan.md). "
              "Suis la skill short-editor en montant exactement les scènes choisies. "
              "Si job.json contient history, ce sont les consignes déjà données sur cette vidéo : applique-les aussi."),
    "clip": "Job de type clip. Suis la skill long-to-short.",
    "feedback": ("Job de type feedback : Mehdi continue sur la vidéo du job parent (champ parent de job.json) ; "
                 "la vidéo source est dans jobs/<source_job>/input/ et la transcription la plus à jour (Scribe) "
                 "dans jobs/<source_job>/work/words.json. Son message est dans feedback, et history liste "
                 "TOUTES les consignes déjà données sur cette vidéo : elles restent valables sauf si feedback les contredit. "
                 "Repars des fichiers de work/ du job parent (copie-les), ne refais que ce qui est demandé, "
                 "puis applique la skill skill-keeper pour que ce retour serve aux prochaines vidéos."),
    "style": "Job de type style. Suis la skill style-trainer.",
    "bilan": ("Job de type bilan. Suis la section /bilan de la skill skill-keeper. Si job.json contient auto: true, "
              "c'est le bilan automatique toutes les 5 notes : applique toi-même les changements (section Bilan automatique)."),
}


def new_job(kind: str, **fields) -> Path:
    jid = time.strftime("%Y%m%d-%H%M%S") + f"-{kind}"
    n = 2
    while (JOBS / jid).exists():  # deux jobs dans la même seconde
        jid = time.strftime("%Y%m%d-%H%M%S") + f"-{kind}{n}"
        n += 1
    d = JOBS / jid
    for sub in ("input", "work", "out"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "job.json").write_text(json.dumps({"id": jid, "type": kind, **fields}, ensure_ascii=False, indent=1))
    (d / "progress.log").touch()
    return d


def target_model() -> str:
    return os.environ.get("SCRIBE_MODEL", "scribe_v1") if os.environ.get("ELEVENLABS_API_KEY") else BIG_MODEL


async def pretranscribe(job_dir: Path, job: dict) -> None:
    if job["type"] == "feedback" and job.get("parent") and (JOBS / job["parent"] / "job.json").exists():
        # Retour sur un rendu : on met à niveau la transcription du job d'origine (l'équipe la recopie).
        plog_child = job.get("_log") or job_dir / "progress.log"
        parent_dir = JOBS / (job.get("source_job") or job["parent"])
        await pretranscribe(parent_dir, json.loads((parent_dir / "job.json").read_text()) | {"_log": str(plog_child)})
        return
    if job["type"] not in ("edit", "clip"):
        return
    srcs = sorted((job_dir / "input").glob("source.*")) or sorted(p for p in (job_dir / "input").iterdir() if p.is_file())
    if not srcs:
        return
    words = job_dir / "work" / "words.json"
    if words.exists():
        try:
            wj = json.loads(words.read_text())
            if wj.get("model") == target_model() and ("events" in wj or wj.get("engine") != "scribe"):
                return  # déjà transcrit avec le bon modèle (job précédent sur la même vidéo)
        except Exception:  # noqa: BLE001
            pass
        words.rename(job_dir / "work" / "words_old.json")
    note = job.get("note", "")
    lang = "ar" if DARIJA_RE.search(note) else (os.environ.get("WHISPER_LANG") or "auto")
    plog = Path(job.get("_log") or job_dir / "progress.log")
    with open(plog, "a") as p:
        p.write("Étape 0 : transcription avec ElevenLabs Scribe (quelques minutes).\n" if os.environ.get("ELEVENLABS_API_KEY")
                else f"Étape 0 : transcription soignée ({BIG_MODEL}, langue {lang}).\n")
    cmd = [sys.executable, str(REPO / "tools" / "transcribe.py"), str(srcs[0]), str(words),
           "--model", BIG_MODEL, "--lang", lang, "--prompt", HINT, "--progress", str(plog)]
    with open(job_dir / "transcribe.log", "wb") as log:
        proc = await asyncio.create_subprocess_exec(*cmd, cwd=REPO, stdout=log, stderr=asyncio.subprocess.STDOUT)
        code = await proc.wait()
    with open(plog, "a") as p:
        p.write("Transcription terminée.\n" if code == 0 else f"Transcription soignée en échec (code {code}), l'équipe fera avec un modèle plus petit.\n")


async def run_job(job_dir: Path) -> int:
    job = json.loads((job_dir / "job.json").read_text())
    await pretranscribe(job_dir, job)
    rel = job_dir.relative_to(REPO)
    prompt = (
        f"Nouveau job : dossier {rel}/. Lis {rel}/job.json. {PROMPTS[job.get('phase') or job['type']]} "
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
