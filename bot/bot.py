#!/usr/bin/env python3
"""Bot Telegram privé : la porte d'entrée de l'équipe de montage.

Commandes (seul TELEGRAM_ALLOWED_USER_ID est écouté) :
  /script <lien>        recherche + script
  /clip <lien> [n]      vidéo longue -> n shorts (1 par défaut)
  (envoi d'une vidéo)   montage d'un A-roll ; légende "clip" ou "clip 3" = vidéo longue
  (chemin d'un fichier) mode Mac : /Users/.../video.mov, puis ton prompt à la ligne suivante
  Montage en 2 temps : je t'envoie d'abord un PLAN (4 idées par scène). Réponds-y avec
    tes choix (« 1B 2A… » ou « ok »), puis je monte. Écris « direct » dans ton prompt pour sauter le plan.
  (réponse à un rendu)  retour -> nouvelle version + mise à jour des skills
  « valide » en réponse  rendu final 1080p du brouillon (ffmpeg seul, sans Claude)
  /statut               job en cours et file d'attente
  /bilan                propose des améliorations des skills
  /annuler              annule la dernière mise à jour des skills (git revert)
"""
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes, MessageHandler, filters)

from runner import JOBS, REPO, new_job, run_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")
# httpx affiche chaque URL appelée, jeton du bot compris : on le fait taire.
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
if not re.fullmatch(r"\d+:[\w-]{30,}", TOKEN):
    raise SystemExit("TELEGRAM_BOT_TOKEN mal copié : il doit ressembler à 123456789:AAH... "
                     "(chiffres, deux-points, puis environ 35 caractères). Corrige-le avec : "
                     "open -e ~/.video-editors-agents.env")
ALLOWED = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
API_URL = os.environ.get("TELEGRAM_API_URL", "")  # ex: http://127.0.0.1:8081/bot (serveur Bot API local)
URL_RE = re.compile(r"https?://\S+")
INDEX = JOBS / "index.json"  # message_id Telegram -> job id (pour les retours)

queue: asyncio.Queue = asyncio.Queue()
current: dict = {}


def load_index() -> dict:
    try:
        return json.loads(INDEX.read_text())
    except Exception:  # noqa: BLE001
        return {}


def remember(message_id: int, job_id: str) -> None:
    idx = load_index()
    idx[str(message_id)] = job_id
    INDEX.write_text(json.dumps(idx))


def only_me(fn):
    async def wrap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or update.effective_user.id != ALLOWED:
            log.warning("Message ignoré : l'identifiant %s n'est pas TELEGRAM_ALLOWED_USER_ID (%s)",
                        update.effective_user.id if update.effective_user else "?", ALLOWED)
            return
        return await fn(update, ctx)
    return wrap


DIRECT_RE = re.compile(r"\b(direct|sans plan)\b", re.I)


def set_phase(job_dir: Path) -> None:
    """Montage : d'abord un plan que Mehdi valide, sauf s'il écrit « direct » ou « sans plan »."""
    job = json.loads((job_dir / "job.json").read_text())
    if job.get("type") == "edit" and not job.get("phase"):
        job["phase"] = "build" if DIRECT_RE.search(job.get("note", "")) else "plan"
        (job_dir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))


def start_build(parent_id: str, choices: str) -> Path:
    """Réponse au plan : nouveau job qui reprend la vidéo et le travail de la phase plan."""
    src = JOBS / parent_id
    parent = json.loads((src / "job.json").read_text())
    d = new_job("edit", phase="build", parent=parent_id, choices=choices, note=parent.get("note", ""),
                input_file=parent.get("input_file"), source_path=parent.get("source_path"))
    for f in (src / "input").iterdir():
        if subprocess.run(["cp", "-c", str(f), str(d / "input" / f.name)], capture_output=True).returncode != 0:
            shutil.copy2(f, d / "input" / f.name)
    for f in (src / "work").iterdir():
        if f.is_file():
            shutil.copy2(f, d / "work" / f.name)
    if (src / "out" / "plan.md").exists():
        shutil.copy2(src / "out" / "plan.md", d / "work" / "plan.md")
    return d


async def enqueue(update: Update, job_dir: Path, label: str) -> None:
    set_phase(job_dir)
    await queue.put((update.effective_chat.id, job_dir))
    pos = queue.qsize() + (1 if current else 0)
    msg = f"✅ Job {label} reçu ({job_dir.name})."
    if pos > 1:
        msg += f" Position dans la file : {pos}."
    await update.message.reply_text(msg)


@only_me
async def cmd_start(update: Update, ctx):
    await update.message.reply_text(__doc__.split("\n\n", 1)[1])


@only_me
async def cmd_script(update: Update, ctx):
    urls = URL_RE.findall(update.message.text or "")
    if not urls:
        await update.message.reply_text("Donne-moi un lien : /script https://...")
        return
    note = URL_RE.sub("", update.message.text.replace("/script", "")).strip()
    await enqueue(update, new_job("script", url=urls[0], note=note), "script")


@only_me
async def cmd_clip(update: Update, ctx):
    text = update.message.text or ""
    urls = URL_RE.findall(text)
    if not urls:
        await update.message.reply_text("Envoie la vidéo avec la légende « clip », ou /clip https://...")
        return
    n = re.search(r"\s(\d)\s*$", text)
    await enqueue(update, new_job("clip", url=urls[0], count=int(n.group(1)) if n else 1), "clip")


@only_me
async def on_video(update: Update, ctx):
    m = update.message
    media = m.video or m.document
    caption = (m.caption or "").strip()
    kind = "clip" if caption.lower().startswith("clip") else "edit"
    count = int(re.search(r"\d", caption).group()) if kind == "clip" and re.search(r"\d", caption) else 1
    job_dir = new_job(kind, note=caption, count=count, input_file="input/source.mp4")
    await m.reply_text("⬇️ Je récupère la vidéo…")
    f = await ctx.bot.get_file(media.file_id)
    await f.download_to_drive(job_dir / "input" / "source.mp4")
    await enqueue(update, job_dir, "montage" if kind == "edit" else "clip")


@only_me
async def on_text(update: Update, ctx):
    m = update.message
    if m.reply_to_message:
        parent = load_index().get(str(m.reply_to_message.message_id))
        pjob = JOBS / parent / "job.json" if parent else None
        if pjob and pjob.exists() and json.loads(pjob.read_text()).get("phase") == "plan":
            await m.reply_text("👍 Plan reçu, je lance le montage avec tes choix.")
            await enqueue(update, await asyncio.to_thread(start_build, parent, m.text or "ok"), "montage")
            return
        if parent and VALIDATE_RE.match(m.text or ""):
            await validate(update, ctx, parent)
            return
        if parent:
            await enqueue(update, new_job("feedback", parent=parent, feedback=m.text), "retour")
            return
    # Telegram découpe les longs messages : on regroupe ce qui arrive en quelques secondes.
    buf = ctx.chat_data.setdefault("buf", [])
    buf.append(m.text or "")
    if t := ctx.chat_data.get("timer"):
        t.cancel()
    ctx.chat_data["timer"] = asyncio.get_running_loop().create_task(flush_text(update, ctx))


VIDEO_EXT = (".mp4", ".mov", ".mkv", ".m4v", ".webm")
SEARCH_DIRS = ("Movies", "Desktop", "Downloads", "Documents", "Pictures")


def find_local_video(line: str):
    """Chemin complet, ou simple nom de fichier cherché dans les dossiers habituels du Mac."""
    line = line.strip().strip("'\"").replace("\\ ", " ")
    if not line or len(line) > 300:
        return None
    p = Path(os.path.expanduser(line))
    if p.is_absolute():
        return p.resolve() if p.suffix.lower() in VIDEO_EXT and p.is_file() else None
    norm = lambda x: re.sub(r"[\W_]+", "", x.lower())
    want = norm(Path(line).stem if Path(line).suffix.lower() in VIDEO_EXT else line)
    if len(want) < 6:
        return None
    for d in SEARCH_DIRS:
        base = Path.home() / d
        if not base.is_dir():
            continue
        for f in [*base.glob("*"), *base.glob("*/*"), *base.glob("*/*/*")]:
            if f.suffix.lower() in VIDEO_EXT and norm(f.stem).startswith(want) and f.is_file():
                return f.resolve()
    return None


def reuse_transcript(local: Path, job_dir: Path) -> None:
    """Même vidéo déjà transcrite dans un job précédent : on recopie la transcription (gain de 10 min)."""
    for prev in sorted(JOBS.glob("*/job.json"), reverse=True):
        try:
            if json.loads(prev.read_text()).get("source_path") != str(local):
                continue
        except Exception:  # noqa: BLE001
            continue
        for name in ("words.json", "silences.json"):
            if (prev.parent / "work" / name).exists() and prev.parent != job_dir:
                shutil.copy2(prev.parent / "work" / name, job_dir / "work" / name)
        if (job_dir / "work" / "words.json").exists():
            return


async def flush_text(update: Update, ctx) -> None:
    await asyncio.sleep(6)
    text = "\n".join(ctx.chat_data.pop("buf", [])).strip()
    ctx.chat_data.pop("timer", None)
    m = update.message
    # Instructions attendues pour une vidéo déjà reçue (message éventuellement découpé, déjà regroupé)
    if pending := ctx.chat_data.pop("awaiting_note", None):
        job_dir, kind = Path(pending[0]), pending[1]
        job = json.loads((job_dir / "job.json").read_text())
        job["note"] = text
        if text.lower().startswith("clip"):
            job["type"] = kind = "clip"
        (job_dir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
        await enqueue(update, job_dir, "montage" if kind == "edit" else "clip")
        return
    first, _, rest = text.partition("\n")
    local = find_local_video(first)
    if local:
        rest = rest.strip()
        kind = "clip" if rest.lower().startswith("clip") else "edit"
        count = int(re.search(r"\d", rest[:10]).group()) if kind == "clip" and re.search(r"\d", rest[:10]) else 1
        job_dir = new_job(kind, note=rest, count=count, input_file="input/source" + local.suffix.lower(),
                          source_path=str(local))
        dst = job_dir / "input" / ("source" + local.suffix.lower())
        await m.reply_text(f"🎞️ Vidéo trouvée : {local}\nJe la copie dans le dossier du job…")
        # Vraie copie (pas un lien) : les agents n'ont accès qu'au dossier du dépôt.
        # Sur Mac, « cp -c » fait un clone APFS instantané qui ne prend pas de place en plus.
        r = await asyncio.to_thread(subprocess.run, ["cp", "-c", str(local), str(dst)], capture_output=True)
        if r.returncode != 0:
            await asyncio.to_thread(shutil.copy2, local, dst)
        reuse_transcript(local, job_dir)
        if not rest:
            ctx.chat_data["awaiting_note"] = (str(job_dir), kind)
            await m.reply_text("✍️ Qu'est-ce que je dois en faire ? Envoie tes instructions dans ton prochain message "
                               "(format, langue des sous-titres, ce que tu veux).")
            return
        await enqueue(update, job_dir, "montage" if kind == "edit" else "clip")
        return
    urls = URL_RE.findall(text)
    if urls:
        await enqueue(update, new_job("script", url=urls[0], note=URL_RE.sub("", text).strip()), "script")
        return
    if len(first) < 300 and not first.startswith("/"):
        await m.reply_text(f"Je ne trouve pas la vidéo « {first[:80]} » dans Vidéos, Bureau, Téléchargements "
                           "ni Documents. Envoie son chemin complet (glisse le fichier dans le Terminal pour l'avoir), "
                           "puis ton prompt à la ligne.")
        return
    await m.reply_text("Envoie un lien (script), une vidéo (montage), ou réponds à un rendu pour donner un retour.")


# Le message entier doit être une validation : « ok mais musique trop forte » reste un retour.
VALIDATE_RE = re.compile(r"^\s*/?(valide|valid|validé|valider|ok|go|parfait|top)\s*[!.👍🔥]*\s*$", re.I)


async def validate(update: Update, ctx, job_id: str) -> None:
    """Rendu final 1080p depuis le plan du brouillon : ffmpeg seul, aucun appel à Claude."""
    plan = JOBS / job_id / "work" / "plan.json"
    if not plan.exists():
        await update.message.reply_text("Je ne trouve pas le plan de montage de ce job, impossible de faire le 1080p.")
        return
    await update.message.reply_text("👍 Validé. Rendu final en 1080p (sans Claude, ça ne consomme rien)…")
    r = await asyncio.to_thread(subprocess.run, [sys.executable, str(REPO / "tools" / "compose.py"), str(plan),
                                                 "--final"], capture_output=True, text=True)
    final = JOBS / job_id / "out" / "final_1080.mp4"
    if r.returncode != 0 or not final.exists():
        await update.message.reply_text(f"⚠️ Échec du rendu final :\n{(r.stderr or r.stdout)[-800:]}")
        return
    if not API_URL and final.stat().st_size > 49 * 1024 * 1024:
        await update.message.reply_text(f"🎞️ Version finale prête (trop lourde pour Telegram) :\n{final}")
        return
    with open(final, "rb") as fh:
        msg = await ctx.bot.send_video(update.effective_chat.id, fh, caption=f"{job_id} · version finale 1080p",
                                       supports_streaming=True, read_timeout=600, write_timeout=600)
    remember(msg.message_id, job_id)


@only_me
async def cmd_statut(update: Update, ctx):
    if not current:
        await update.message.reply_text("Rien en cours.")
        return
    lines = Path(current["dir"], "progress.log").read_text().strip().splitlines()[-5:]
    await update.message.reply_text(f"En cours : {current['dir'].name}\nEn attente : {queue.qsize()}\n\n"
                                    + "\n".join(lines))


@only_me
async def cmd_bilan(update: Update, ctx):
    await enqueue(update, new_job("bilan"), "bilan")


@only_me
async def cmd_annuler(update: Update, ctx):
    last = subprocess.run(["git", "log", "-1", "--format=%H %s", "--grep=^skills:"], cwd=REPO,
                          capture_output=True, text=True).stdout.strip()
    if not last:
        await update.message.reply_text("Aucune mise à jour de skills à annuler.")
        return
    sha, subject = last.split(" ", 1)
    r = subprocess.run(["git", "revert", "--no-edit", sha], cwd=REPO, capture_output=True, text=True)
    await update.message.reply_text(f"↩️ Annulé : {subject}" if r.returncode == 0 else f"Échec : {r.stderr[-300:]}")


async def send_outputs(app: Application, chat_id: int, job_dir: Path, code: int) -> None:
    out = job_dir / "out"
    sent_any = False
    for script in sorted(out.glob("*.md")):
        if script.name in ("summary.md", "skill_update.md"):
            continue
        text = script.read_text()
        for i in range(0, len(text), 3900):
            msg = await app.bot.send_message(chat_id, text[i:i + 3900])
            remember(msg.message_id, job_dir.name)
        sent_any = True
    for video in sorted(v for v in out.glob("*.mp4") if not v.name.endswith("_1080.mp4")):
        if not API_URL and video.stat().st_size > 49 * 1024 * 1024:
            msg = await app.bot.send_message(chat_id, f"🎞️ Vidéo trop lourde pour Telegram, elle est ici :\n{video}")
            remember(msg.message_id, job_dir.name)
            sent_any = True
            continue
        with open(video, "rb") as fh:
            msg = await app.bot.send_video(chat_id, fh, caption=f"{job_dir.name} · {video.name}",
                                           supports_streaming=True, read_timeout=600, write_timeout=600)
        remember(msg.message_id, job_dir.name)
        sent_any = True
    for name in ("summary.md", "skill_update.md"):
        p = out / name
        if p.exists():
            msg = await app.bot.send_message(chat_id, p.read_text()[:3900])
            remember(msg.message_id, job_dir.name)
    is_plan = json.loads((job_dir / "job.json").read_text()).get("phase") == "plan"
    if not sent_any:
        await app.bot.send_message(chat_id, f"⚠️ Job {job_dir.name} terminé sans livrable (code {code}). "
                                            f"Journal : {job_dir / 'claude.log'}")
    elif is_plan:
        await app.bot.send_message(chat_id, "☝️ Réponds au PLAN (glisse le message vers la droite) avec tes choix : "
                                            "« 1B 2A 3C… », tes idées, ou « ok » pour mes ⭐.")
    else:
        await app.bot.send_message(chat_id, "Brouillon en 480p. Réponds « valide » à la vidéo pour la version 1080p, "
                                            "ou réponds avec tes corrections.")


async def worker(app: Application) -> None:
    while True:
        chat_id, job_dir = await queue.get()
        current.update(dir=job_dir)
        await app.bot.send_message(chat_id, f"🎬 Je commence {job_dir.name}")
        task = asyncio.create_task(run_job(job_dir))
        seen = 0
        while not task.done():
            await asyncio.sleep(20)
            lines = (job_dir / "progress.log").read_text().splitlines()
            if len(lines) > seen:
                await app.bot.send_message(chat_id, "\n".join("• " + x for x in lines[seen:])[-3900:])
                seen = len(lines)
        try:
            await send_outputs(app, chat_id, job_dir, task.result())
        except Exception as e:  # noqa: BLE001
            log.exception("envoi")
            await app.bot.send_message(chat_id, f"⚠️ Erreur à l'envoi : {e}")
        current.clear()
        queue.task_done()


async def post_init(app: Application) -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    asyncio.get_running_loop().create_task(worker(app))


def main() -> None:
    log.info("Bot démarré. Utilisateur autorisé : %s", ALLOWED)
    b = Application.builder().token(TOKEN).post_init(post_init)
    if API_URL:
        b = b.base_url(API_URL).base_file_url(API_URL.replace("/bot", "/file/bot")).local_mode(True)
    app = b.read_timeout(600).write_timeout(600).build()
    app.add_handler(CommandHandler(["start", "aide"], cmd_start))
    app.add_handler(CommandHandler("script", cmd_script))
    app.add_handler(CommandHandler("clip", cmd_clip))
    app.add_handler(CommandHandler("statut", cmd_statut))
    app.add_handler(CommandHandler("bilan", cmd_bilan))
    app.add_handler(CommandHandler("annuler", cmd_annuler))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, on_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
