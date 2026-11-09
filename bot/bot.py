#!/usr/bin/env python3
"""Bot Telegram privé : la porte d'entrée de l'équipe de montage.

Commandes (seul TELEGRAM_ALLOWED_USER_ID est écouté) :
  /script <lien>        recherche + script
  /clip <lien> [n]      vidéo longue -> n shorts (1 par défaut)
  (envoi d'une vidéo)   montage d'un A-roll ; légende "clip" ou "clip 3" = vidéo longue
  (chemin d'un fichier) mode Mac : /Users/.../video.mov, puis ton prompt à la ligne suivante
  « style <nom> » dans le prompt : monte avec un style appris (sinon choix auto solo-v1 / interview-v1)
  « mode guidé » dans le prompt (ou /phrases) : je t'envoie la liste numérotée des phrases, tu réponds
    avec les numéros dans l'ordre (« intro : 12, 45, 7 ») et je monte exactement ça.
  « mode plan » dans le prompt : je t'envoie d'abord un PLAN (4 idées par scène), tu réponds
    avec tes choix (« 1B 2A… » ou « ok »), puis je monte.
  /style <nom> [liens]  apprend un style de montage sur 2 à 5 vidéos (liens, ou style/<nom>/refs.txt)
  (réponse à un rendu)  retour -> nouvelle version + mise à jour des skills
  « valide » en réponse  rendu final 1080p du brouillon (ffmpeg seul, sans Claude)
  /musique [ambiance]   3 musiques de fond à écouter, tu choisis, je l'ajoute à ta dernière vidéo
  /stop                 arrête tout (montage en cours + file d'attente), puis renvoie ta demande
  /statut               job en cours et file d'attente
  /mac                  le bot passe sur ton Mac (vidéos du Mac, montages longs)
  /serveur              le bot passe sur le serveur (24 h/24, Mac éteint possible)
  /maj                  installe tout de suite les dernières améliorations (sinon : automatique)
  /bilan                propose des améliorations des skills
  /annuler              annule la dernière mise à jour des skills (git revert)
"""
import asyncio
import json
import logging
import os
import re
import unicodedata
import shutil
import subprocess
import sys
import time
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters)

import switch
from runner import JOBS, PROCS, REPO, new_job, run_job

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
current: dict = {}  # jobs en cours : nom -> dossier
current_bg: set = set()  # bilans en arrière-plan (pas de mise à jour/redémarrage pendant ce temps)
MAX_JOBS = int(os.environ.get("MAX_JOBS", "1"))  # vidéos montées en même temps
RATINGS = REPO / "style" / "ratings.jsonl"  # notes de Mehdi : la mémoire de ce qui marche


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


# « demande à Jeremy / Hormozi / au copywriter … » : une question à l'équipe, sans montage.
ASK_RE = re.compile(r"\b(demande|demandes|demander|pose|question)\b.{0,40}\b(j[eé]r[eé]m\w*|haynes|hormo\w*|alex|copy\s*writ\w*|copywriter)", re.I | re.S)
PLAN_RE = re.compile(r"\b(mode plan|avec (le )?plan|plan d'abord)\b", re.I)
GUIDE_RE = re.compile(r"(mode guid|\bguid[ée]\b|je (te )?guide|liste des phrases|^/?phrases\s*$)", re.I)


def set_phase(job_dir: Path) -> None:
    """Montage direct par défaut. « mode plan » dans le prompt : d'abord un plan que Mehdi valide."""
    job = json.loads((job_dir / "job.json").read_text())
    if job.get("type") == "edit" and not job.get("phase"):
        note = job.get("note", "")
        job["phase"] = "phrases" if GUIDE_RE.search(note) else "plan" if PLAN_RE.search(note) else "build"
        (job_dir / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))


def derive_job(parent_id: str, **fields) -> Path:
    """Nouveau job edit qui reprend la vidéo et le travail (work/) d'un job précédent."""
    src = JOBS / parent_id
    parent = json.loads((src / "job.json").read_text())
    d = new_job("edit", parent=parent_id, **({"note": parent.get("note", ""), "input_file": parent.get("input_file"),
                                              "source_path": parent.get("source_path")} | fields))
    for f in (src / "input").iterdir():
        try:
            os.link(f, d / "input" / f.name)  # instantané, sans place en plus
        except OSError:
            if subprocess.run(["cp", "-c", str(f), str(d / "input" / f.name)], capture_output=True).returncode != 0:
                shutil.copy2(f, d / "input" / f.name)
    for f in (src / "work").iterdir():
        if f.is_file():
            shutil.copy2(f, d / "work" / f.name)
    return d


def parse_picks(text: str) -> list[int]:
    """« intro : 12, 45, 7-9 » -> [12, 45, 7, 8, 9] (dans l'ordre donné)."""
    out = []
    # Les numéros sont dans la 1re phrase ; la suite (« commence la 221 à… ») est une consigne, pas un choix.
    text = re.split(r"\n|\.\s+(?=[^\d\s])", text, maxsplit=1)[0]
    for m in re.finditer(r"(?<![\d:.])(\d+)(?:\s*(?:-|à)\s*(\d+))?(?![\d:.]|\s*(?:s\b|sec|min|p\b|%|k\b|dh|\$|€))", text):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        out += list(range(a, b + 1)) if 0 <= b - a <= 30 else [a]
    return list(dict.fromkeys(out))


def start_guided(parent_id: str, text: str) -> tuple[Path | None, str]:
    """Réponse à la liste des phrases : montage exact des phrases choisies par Mehdi."""
    src = JOBS / parent_id
    pj = src / "work" / "phrases.json"
    if not pj.exists():
        return None, "La liste des phrases est introuvable pour ce job."
    phrases = {p["n"]: p for p in json.loads(pj.read_text()).get("phrases", [])}
    nums = parse_picks(text)
    picks = [phrases[n] for n in nums if n in phrases]
    missing = [n for n in nums if n not in phrases]
    if not picks:
        return None, "Je n'ai pas trouvé de numéros de phrases. Exemple : « intro : 12, 45, 7 »."
    pdata = json.loads((src / "job.json").read_text())
    d = derive_job(parent_id, phase="guided", instruction=text, history=pdata.get("history", []),
                   picks=[{k: p.get(k) for k in ("n", "start", "end", "speaker", "latin", "text", "cough")} for p in picks])
    try:  # mémoire du goût : les vrais choix de Mehdi (le skill-keeper et le copywriter s'en inspirent)
        with open(REPO / "style" / "guided_picks.jsonl", "a") as f:
            f.write(json.dumps({"date": time.strftime("%Y-%m-%d"), "job": d.name, "source": pdata.get("source_path"),
                                "instruction": text, "picks": [p.get("latin") or p.get("text") for p in picks]},
                               ensure_ascii=False) + "\n")
    except OSError:
        pass
    note = f"{len(picks)} phrases" + (f" (introuvables : {', '.join(map(str, missing))})" if missing else "")
    return d, note


def start_build(parent_id: str, choices: str) -> Path:
    """Réponse au plan : nouveau job qui reprend la vidéo et le travail de la phase plan."""
    src = JOBS / parent_id
    d = derive_job(parent_id, phase="build", choices=choices)
    if (src / "out" / "plan.md").exists():
        shutil.copy2(src / "out" / "plan.md", d / "work" / "plan.md")
    return d


async def enqueue(update: Update, job_dir: Path, label: str) -> None:
    set_phase(job_dir)
    await queue.put((update.effective_chat.id, job_dir))
    pos = queue.qsize() + max(0, len(current) - MAX_JOBS + 1)
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


MUSIC_RE = re.compile(r"(\b(propose|envoie|donne|choisir|choix|montre|cherche|trouve)\b.{0,30}\bmusiques?\b|^\s*/?musiques?\b)", re.I)
MUSIC_MOODS = [
    ("Suspense discret", "subtle conversational suspense, soft piano and light strings pad, slow pulse, calm tension, documentary interview"),
    ("Tension moderne", "light modern tension, pizzicato strings and ambient pad, minimal, curious, documentary"),
    ("Inspirant sobre", "minimal emotional piano with soft electronic pulse, hopeful, understated, entrepreneur story"),
]


async def propose_music(update: Update, ctx, extra: str = "") -> None:
    """3 musiques de fond à écouter ; Mehdi choisit, le bot l'ajoute à la dernière vidéo."""
    m = update.message
    last = last_video_job()
    dur = 45.0
    if last and (last / "out" / "final.mp4").exists():
        try:
            out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(last / "out" / "final.mp4")], capture_output=True, text=True).stdout
            dur = min(120.0, float(out.strip()) + 2)
        except (OSError, ValueError):
            pass
    await m.reply_text(f"🎵 Je te prépare 3 musiques de {round(dur)} s (1 à 3 min)…")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    sent = 0
    for i, (label, mood) in enumerate(MUSIC_MOODS, 1):
        prompt = f"{mood}. {extra}".strip(". ") if extra else mood
        dst = REPO / "assets" / "music" / f"choix-{stamp}-{i}.mp3"
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = await asyncio.to_thread(subprocess.run, [sys.executable, str(REPO / "tools" / "music.py"), prompt, str(dst),
                                                     "--dur", str(dur)], capture_output=True, text=True)
        if r.returncode != 0 or not dst.exists():
            continue
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Choisir la {i}", callback_data=f"music:{dst.name}")]])
        with open(dst, "rb") as fh:
            await m.reply_audio(fh, title=f"{i}. {label}", caption=f"{i}. {label}", reply_markup=kb)
        sent += 1
    if not sent:
        await m.reply_text("⚠️ Je n'ai pas pu créer de musique (ElevenLabs refuse ou n'est pas configuré). "
                           "Envoie-moi un mp3 que tu aimes, je l'utiliserai.")
    else:
        await m.reply_text("Écoute et appuie sur « Choisir » sous celle que tu veux : je l'ajoute à ta dernière vidéo. "
                           "Aucune ne va ? Écris « musiques plus calmes » (ou ton ambiance) pour en avoir 3 autres.")


async def on_music_pick(update: Update, ctx):
    q = update.callback_query
    if not q.from_user or q.from_user.id != ALLOWED:
        return
    name = q.data.split(":", 1)[1]
    await q.answer("Choisie !")
    await q.edit_message_reply_markup(None)
    last = last_video_job()
    if not last:
        await q.message.reply_text("🎵 Gardée. Envoie ta vidéo, je l'utiliserai.")
        return
    root = root_job(last)
    d = new_job("feedback", parent=last.name, source_job=root.name, history=history(last), conseils=recent_advice(),
                feedback=f"Ajoute la musique de fond assets/music/{name} (choisie par Mehdi) sous l'intro, avec "
                         "tools/add_music.py (volume ~0,08, baisse sous la voix, fondu avant le noir) et "
                         "music_after dans plan.json. Ne change rien d'autre.")
    await q.message.reply_text("🎵 Je l'ajoute à ta dernière vidéo, rien d'autre ne change.")
    set_phase(d)
    await queue.put((q.message.chat_id, d))


@only_me
async def cmd_musique(update: Update, ctx):
    await propose_music(update, ctx, " ".join(ctx.args or []))


@only_me
async def on_audio(update: Update, ctx):
    """Un mp3 envoyé = une musique de fond pour les prochains montages (assets/music/, choisie par ambiance)."""
    m = update.message
    media = m.audio or m.document
    name = re.sub(r"[^\w.-]+", "-", (getattr(media, "file_name", None) or "musique.mp3").lower()).strip("-")
    if (m.caption or "").strip():
        name = re.sub(r"[^\w-]+", "-", m.caption.strip().lower())[:40].strip("-") + "-" + name
    dst = REPO / "assets" / "music" / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    f = await ctx.bot.get_file(media.file_id)
    await f.download_to_drive(dst)
    await m.reply_text(f"🎵 Musique ajoutée à ta bibliothèque ({name}). Je l'utilise quand l'ambiance correspond "
                       "(mets un mot dans la légende, ex. « suspense », pour l'aider). Dis « avec la musique "
                       f"{name} » pour l'imposer.")


@only_me
async def on_video(update: Update, ctx):
    m = update.message
    media = m.video or m.document
    caption = (m.caption or "").strip()
    kind = "clip" if caption.lower().startswith("clip") else "edit"
    count = int(re.search(r"\d", caption).group()) if kind == "clip" and re.search(r"\d", caption) else 1
    job_dir = new_job(kind, note=caption, count=count, input_file="input/source.mp4", conseils=recent_advice())
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
        if pjob and pjob.exists() and json.loads(pjob.read_text()).get("phase") == "phrases":
            d, info = await asyncio.to_thread(start_guided, parent, m.text or "")
            if not d:
                await m.reply_text(info)
                return
            await m.reply_text(f"👍 Je monte exactement tes {info}, dans ton ordre.")
            await enqueue(update, d, "montage guidé")
            return
        if pjob and pjob.exists() and json.loads(pjob.read_text()).get("phase") == "plan":
            await m.reply_text("👍 Plan reçu, je lance le montage avec tes choix.")
            await enqueue(update, await asyncio.to_thread(start_build, parent, m.text or "ok"), "montage")
            return
        if parent and VALIDATE_RE.match(m.text or ""):
            await validate(update, ctx, parent)
            return
        if parent and json.loads((JOBS / parent / "job.json").read_text()).get("type") == "ask":
            prev = json.loads((JOBS / parent / "job.json").read_text())
            hist = prev.get("history", []) + [f"Question : {prev.get('question')}",
                                                f"Réponse : {(JOBS / parent / 'out' / 'answer.md').read_text()[:3000] if (JOBS / parent / 'out' / 'answer.md').exists() else ''}"]
            await enqueue(update, new_job("ask", question=m.text, history=hist), "question")
            return
        if parent:
            pdir = JOBS / parent
            await enqueue(update, new_job("feedback", parent=parent, feedback=m.text, source_job=root_job(pdir).name,
                                          history=history(pdir)), "retour")
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


def _nfc_norm(x: str) -> str:
    # macOS écrit les accents en NFD (« é » = e + accent) : on normalise avant de comparer.
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFC", x).lower())


def known_video(line: str):
    """Vidéo déjà reçue dans un job (ex. copiée du Mac vers le VPS) : (fichier du job, chemin d'origine)."""
    line = line.strip().strip("'\"").replace("\\ ", " ")
    if not line or len(line) > 300:
        return None
    want = _nfc_norm(Path(line).stem if Path(line).suffix.lower() in VIDEO_EXT else line)
    if len(want) < 6:
        return None
    for jf in sorted(JOBS.glob("*/job.json"), reverse=True):
        try:
            j = json.loads(jf.read_text())
        except ValueError:
            continue
        src, inp = j.get("source_path"), j.get("input_file")
        if not src or not inp or not (jf.parent / inp).is_file():
            continue
        if _nfc_norm(Path(src).stem).startswith(want):
            return jf.parent / inp, src
    return None


def reuse_transcript(local, job_dir: Path) -> None:
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
    src_key = str(local) if local else None
    if not local and (kv := known_video(first)):
        local, src_key = kv
    if not local and first.strip().strip("'\"").startswith(("/Users/", "~/")) and sys.platform != "darwin":
        await m.reply_text("Cette vidéo est sur ton Mac, et je tourne sur le serveur : je ne la vois pas. Envoie /mac "
                           "pour que je passe sur ton Mac, puis renvoie le chemin. Ou envoie la vidéo ici (jusqu'à 2 Go).")
        return
    if local:
        rest = rest.strip()
        kind = "clip" if rest.lower().startswith("clip") else "edit"
        count = int(re.search(r"\d", rest[:10]).group()) if kind == "clip" and re.search(r"\d", rest[:10]) else 1
        job_dir = new_job(kind, note=rest, count=count, input_file="input/source" + local.suffix.lower(),
                          source_path=src_key, history=previous_notes(src_key), conseils=recent_advice())
        dst = job_dir / "input" / ("source" + local.suffix.lower())
        await m.reply_text(f"🎞️ Vidéo trouvée : {Path(src_key).name}\nJe la prépare…")
        # Vraie copie (pas un lien) : les agents n'ont accès qu'au dossier du dépôt.
        # Sur Mac, « cp -c » fait un clone APFS instantané qui ne prend pas de place en plus.
        try:
            os.link(local, dst)  # même disque (VPS) : instantané, sans place en plus
        except OSError:
            r = await asyncio.to_thread(subprocess.run, ["cp", "-c", str(local), str(dst)], capture_output=True)
            if r.returncode != 0:
                await asyncio.to_thread(shutil.copy2, local, dst)
        reuse_transcript(src_key, job_dir)
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
    if ASK_RE.search(text):
        await m.reply_text("🧠 Je pose ta question à l'équipe (copywriter, Hormozi, Haynes), réponse dans quelques minutes.")
        await enqueue(update, new_job("ask", question=text), "question")
        return
    if MUSIC_RE.search(first) and len(text) < 160:
        extra = re.sub(r"(?i)\b(propose|envoie|donne|moi|des|3|trois|musiques?|de fond|choisir|stp)\b", " ", text)
        await propose_music(update, ctx, " ".join(extra.split()))
        return
    if STOP_RE.fullmatch(text):
        await stop_current(update)
        return
    if STATUS_RE.fullmatch(text):  # « alors ? » n'est pas une consigne de montage : on donne l'avancement
        await cmd_statut(update, None)
        return
    if re.fullmatch(r"\s*(mode guid[ée]|guid[ée]|phrases|liste des phrases)\s*[.!]*\s*", text, re.I):
        await start_phrases(update)
        return
    # Pas de vidéo ni de lien : on continue sur la dernière vidéo travaillée (Mehdi n'a pas à tout redire).
    fb = ctx.chat_data.pop("feedback_for", None)
    last = JOBS / fb if fb and (JOBS / fb / "job.json").exists() else last_video_job()
    if last and not first.lower().endswith(VIDEO_EXT):
        root = root_job(last)
        name = Path(json.loads((root / "job.json").read_text()).get("source_path") or "la dernière vidéo").name
        d = new_job("feedback", parent=last.name, source_job=root.name, feedback=text, history=history(last),
                    conseils=recent_advice())
        await m.reply_text(f"🔁 Je reprends « {name} » ({last.name}) là où on en était, avec tes instructions.")
        await enqueue(update, d, "retour")
        return
    if len(first) < 300 and not first.startswith("/"):
        await m.reply_text(f"Je n'ai pas de vidéo en cours pour « {first[:80]} ». Envoie la vidéo ici dans "
                           "Telegram (jusqu'à 2 Go), avec ton prompt en légende.")
        return
    await m.reply_text("Envoie un lien (script), une vidéo (montage), ou réponds à un rendu pour donner un retour.")


async def start_phrases(update: Update) -> None:
    """Mode guidé sur la dernière vidéo : liste numérotée des phrases, Mehdi choisit."""
    last = last_video_job()
    if not last:
        await update.message.reply_text("Envoie d'abord une vidéo (ou son chemin sur le Mac) avec « mode guidé ».")
        return
    root = root_job(last)
    d = await asyncio.to_thread(derive_job, root.name, phase="phrases", history=history(last))
    await update.message.reply_text("📝 Je te prépare la liste numérotée des phrases (5 à 10 min). Tu me répondras "
                                    "avec les numéros, dans l'ordre que tu veux.")
    await enqueue(update, d, "liste des phrases")


STATUS_RE = re.compile(r"\s*(alors|et alors|alors frérot|\?+|ça avance|ca avance|t'?en es où|t'?en es ou|statut|status|"
                       r"c'est bon|cbon|ça donne quoi|ca donne quoi|il en est où|il en est ou|toujours rien)\s*[?!.]*\s*", re.I)
STOP_RE = re.compile(r"\s*/?(stop|stoppe|stopper|arr[eê]te|arr[eê]te tout|annule le montage)\s*[.!]*\s*", re.I)


async def stop_current(update: Update) -> None:
    """Arrête tout : le montage en cours et ceux en attente. Mehdi renvoie ensuite UNE demande propre."""
    dropped = 0
    while not queue.empty():
        try:
            _, d = queue.get_nowait()
            queue.task_done()
            dropped += 1
            j = json.loads((d / "job.json").read_text())
            j["stopped"] = True
            (d / "job.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))
        except (asyncio.QueueEmpty, OSError, ValueError):
            break
    if not current and not dropped:
        await update.message.reply_text("Rien ne tourne en ce moment.")
        return
    for name, d in list(current.items()):
        try:
            j = json.loads((d / "job.json").read_text())
            j["stopped"] = True
            (d / "job.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))
        except (OSError, ValueError):
            pass
        proc = PROCS.get(name)
        if proc and proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
    await update.message.reply_text(f"🛑 Tout est arrêté ({len(current)} en cours, {dropped} en attente). "
                                    "Envoie ta nouvelle demande, je repars de la dernière version que tu as reçue.")


@only_me
async def cmd_stop(update: Update, ctx):
    await stop_current(update)


@only_me
async def cmd_phrases(update: Update, ctx):
    await start_phrases(update)


def recent_advice(limit: int = 3) -> list:
    """Dernières réponses de l'équipe aux questions de Mehdi (« fais comme Jeremy a dit »)."""
    out = []
    for jf in sorted(JOBS.glob("*-ask*/job.json"), reverse=True)[:limit]:
        ans = jf.parent / "out" / "answer.md"
        if ans.exists():
            out.append(f"Question : {json.loads(jf.read_text()).get('question', '')}\nRéponse : {ans.read_text()[:2500]}")
    return list(reversed(out))


def last_video_job():
    """Dernier job de montage (edit, clip ou retour) : c'est « là où on en était »."""
    for d in sorted((p for p in JOBS.iterdir() if (p / "job.json").exists()), key=lambda p: p.name, reverse=True):
        try:
            if json.loads((d / "job.json").read_text()).get("type") in ("edit", "clip", "feedback"):
                return d
        except ValueError:
            continue
    return None


def root_job(d: Path) -> Path:
    """Remonte la chaîne des retours jusqu'au job qui a reçu la vidéo."""
    for _ in range(30):
        j = json.loads((d / "job.json").read_text())
        parent = j.get("parent")
        if j.get("type") != "feedback" or not parent or not (JOBS / parent / "job.json").exists():
            return d
        d = JOBS / parent
    return d


def history(d: Path) -> list:
    """Toutes les consignes déjà données sur cette vidéo, de la plus ancienne à la plus récente."""
    out = []
    for _ in range(30):
        j = json.loads((d / "job.json").read_text())
        txt = j.get("feedback") or j.get("note") or ""
        if txt:
            out.append(f"{j.get('id', d.name)} : {txt}")
        parent = j.get("parent")
        if not parent or not (JOBS / parent / "job.json").exists():
            break
        d = JOBS / parent
    return list(reversed(out))


def previous_notes(source) -> list:
    """Consignes données lors des montages précédents de la même vidéo (même fichier source)."""
    notes = []
    for jf in sorted(JOBS.glob("*/job.json")):
        try:
            j = json.loads(jf.read_text())
        except ValueError:
            continue
        if j.get("source_path") == str(source) and j.get("note"):
            notes.append(f"{j.get('id')} : {j['note']}")
    return notes


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
    ma = json.loads(plan.read_text()).get("music_after")  # musique posée après coup (tools/add_music.py)
    if ma and ma.get("file"):
        tmp = final.with_name("final_1080_music.mp4")
        cmd = [sys.executable, str(REPO / "tools" / "add_music.py"), str(final), str(JOBS / job_id / ma["file"]
               if not Path(ma["file"]).is_absolute() and (JOBS / job_id / ma["file"]).exists() else REPO / ma["file"]),
               str(tmp), "--volume", str(ma.get("volume", 0.08))]
        if ma.get("until"):
            cmd += ["--until", str(ma["until"])]
        if ma.get("duck") is False:
            cmd.append("--no-duck")
        r2 = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)
        if r2.returncode == 0 and tmp.exists():
            tmp.replace(final)
    if not API_URL and final.stat().st_size > 49 * 1024 * 1024:
        await update.message.reply_text(f"🎞️ Version finale prête (trop lourde pour Telegram) :\n{final}")
        return
    with open(final, "rb") as fh:
        msg = await ctx.bot.send_video(update.effective_chat.id, fh, caption=f"{job_id} · version finale 1080p",
                                       supports_streaming=True, read_timeout=600, write_timeout=600)
    remember(msg.message_id, job_id)


@only_me
async def cmd_style(update: Update, ctx):
    text = (update.message.text or "").replace("/style", "", 1)
    urls = URL_RE.findall(text)
    name = re.sub(r"[^a-z0-9-]+", "-", URL_RE.sub("", text).strip().split("\n")[0].lower()).strip("-")[:40]
    if not name:
        have = sorted(p.name for p in (REPO / "style").iterdir() if p.is_dir())
        await update.message.reply_text("Donne un nom : /style interview-v1 (puis des liens YouTube, ou rien pour "
                                        f"utiliser style/<nom>/refs.txt). Styles existants : {', '.join(have) or 'aucun'}")
        return
    refs = REPO / "style" / name / "refs.txt"
    if not urls and refs.exists():
        urls = [x.strip() for x in refs.read_text().splitlines() if x.strip().startswith("http")]
    if not urls:
        await update.message.reply_text(f"Aucun lien pour le style {name}. Envoie : /style {name} <lien1> <lien2> …")
        return
    await enqueue(update, new_job("style", name=name, urls=urls, note=text.strip()), f"style {name}")


@only_me
async def cmd_statut(update: Update, ctx):
    if not current:
        await update.message.reply_text("Rien en cours.")
        return
    parts = []
    for name, d in current.items():
        lines = Path(d, "progress.log").read_text().strip().splitlines()[-3:]
        parts.append(f"▶️ {name}\n" + "\n".join(lines))
    await update.message.reply_text(f"En cours : {len(current)}/{MAX_JOBS} · en attente : {queue.qsize()}\n\n"
                                    + "\n\n".join(parts))


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


# ---------- Mises à jour automatiques (plus besoin du Terminal) ----------
def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def pull_updates():
    """Récupère les nouveautés de GitHub. Renvoie (True, liste des changements), (False, erreur) ou None si rien."""
    if git("fetch", "-q", "origin", "main").returncode != 0:
        return None
    if git("rev-list", "--count", "HEAD..origin/main").stdout.strip() in ("", "0"):
        return None
    news = git("log", "--format=• %s", "HEAD..origin/main").stdout.strip()
    r = git("pull", "-q", "--rebase", "--autostash", "origin", "main")
    if r.returncode != 0:
        git("rebase", "--abort")
        return False, r.stderr.strip()[-300:]
    return True, news


async def update_and_restart(app: Application, force_msg: bool = False) -> None:
    if current_bg:
        return  # un bilan tourne en arrière-plan : on se mettra à jour après
    res = await asyncio.to_thread(pull_updates)
    if res is None:
        if force_msg:
            await app.bot.send_message(ALLOWED, "✅ Déjà à jour.")
        return
    ok, info = res
    if not ok:
        await app.bot.send_message(ALLOWED, "⚠️ Mise à jour impossible (conflit avec une modification locale). "
                                            "Préviens Claude dans le projet.\n" + info)
        return
    await app.bot.send_message(ALLOWED, "🔄 Mise à jour installée, je redémarre (10 s) :\n" + "\n".join(info.splitlines()[:6]))
    os._exit(0)  # le lanceur (run-mac.sh ou systemd) relance le bot avec le nouveau code


async def updater(app: Application) -> None:
    """Toutes les 10 min, quand aucun job ne tourne : installe les nouveautés et redémarre."""
    while True:
        await asyncio.sleep(600)
        if not current and queue.empty():
            try:
                await update_and_restart(app)
            except Exception:  # noqa: BLE001
                log.exception("mise à jour")


@only_me
async def cmd_maj(update: Update, ctx):
    if current or not queue.empty():
        await update.message.reply_text("Un job est en cours : je me mettrai à jour tout seul dès qu'il sera fini.")
        return
    await update_and_restart(ctx.application, force_msg=True)


async def send_outputs(app: Application, chat_id: int, job_dir: Path, code: int) -> None:
    out = job_dir / "out"
    sent_any = False
    for script in sorted(out.glob("*.md")):
        if script.name in ("summary.md", "skill_update.md"):
            continue
        chunk = ""
        for line in script.read_text().splitlines(keepends=True) + ["\0"]:
            if line == "\0" or len(chunk) + len(line) > 3900:
                if chunk.strip():
                    msg = await app.bot.send_message(chat_id, chunk[:3900])
                    remember(msg.message_id, job_dir.name)
                chunk = ""
            if line != "\0":
                chunk += line
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
    job = json.loads((job_dir / "job.json").read_text())
    is_plan = job.get("phase") == "plan"
    if job.get("type") == "ask":
        if not sent_any:
            await app.bot.send_message(chat_id, f"⚠️ Pas de réponse pour {job_dir.name} (code {code}).")
        return
    if job.get("type") in ("style", "bilan") and (out / "summary.md").exists():
        if job["type"] == "style":
            await app.bot.send_message(chat_id, f"🎨 Style « {job.get('name')} » prêt. Écris « style {job.get('name')} » "
                                                "dans ton prompt pour monter avec (ou laisse l'équipe le choisir).")
        return
    if not sent_any:
        await app.bot.send_message(chat_id, f"⚠️ Job {job_dir.name} terminé sans livrable (code {code}). "
                                            f"Journal : {job_dir / 'claude.log'}")
    elif (out / "question.md").exists() and not any(out.glob("*.mp4")):
        msg = await app.bot.send_message(chat_id, "❓ J'ai besoin de ta réponse avant de monter. Réponds à ma question "
                                                  "(glisse le message vers la droite).")
        remember(msg.message_id, job_dir.name)
    elif job.get("phase") == "phrases":
        msg = await app.bot.send_message(chat_id, "☝️ Réponds à un de ces messages (glisse vers la droite) avec les numéros "
                                                  "dans l'ordre voulu. Ex. « intro : 12, 45, 7-9 ». Ajoute tes consignes si "
                                                  "besoin (« coupe la fin de la 45 »).")
        remember(msg.message_id, job_dir.name)
    elif is_plan:
        await app.bot.send_message(chat_id, "☝️ Réponds au PLAN (glisse le message vers la droite) avec tes choix : "
                                            "« 1B 2A 3C… », tes idées, ou « ok » pour mes ⭐.")
    else:
        stars = [InlineKeyboardButton("⭐" * n, callback_data=f"rate:{job_dir.name}:{n}") for n in range(1, 6)]
        msg = await app.bot.send_message(chat_id, "Brouillon en 480p. Note-le (ça m'apprend ton goût). Réponds « valide » "
                                                  "à la vidéo pour la 1080p, ou réponds avec tes corrections.",
                                         reply_markup=InlineKeyboardMarkup([stars[:3], stars[3:]]))
        remember(msg.message_id, job_dir.name)


async def on_rate(update: Update, ctx) -> None:
    """Note de 1 à 5 sur un rendu : rangée dans style/ratings.jsonl ; toutes les 5 notes, l'équipe tire les leçons."""
    q = update.callback_query
    if not q.from_user or q.from_user.id != ALLOWED:
        return
    _, jid, n = q.data.split(":")
    n = int(n)
    jf = JOBS / jid / "job.json"
    job = json.loads(jf.read_text()) if jf.exists() else {}
    job["rating"] = n
    if jf.exists():
        jf.write_text(json.dumps(job, ensure_ascii=False, indent=1))
    with open(RATINGS, "a") as f:
        f.write(json.dumps({"job": jid, "rating": n, "type": job.get("type"),
                            "consignes": history(JOBS / jid) if jf.exists() else []}, ensure_ascii=False) + "\n")
    await q.answer("Noté, merci !")
    await q.edit_message_reply_markup(None)
    if n <= 3:
        ctx.chat_data["feedback_for"] = jid
        await q.message.reply_text(f"{'⭐' * n} noté. Dis-moi en une phrase ce qui ne va pas, je refais la version "
                                   "(pas besoin de répondre à la vidéo).")
    else:
        await q.message.reply_text(f"{'⭐' * n} noté. Je garde ce qui a marché pour les prochaines vidéos.")
    done = sum(1 for _ in open(RATINGS))
    if done % 5 == 0:
        # En arrière-plan, sans passer par la file : le bilan ne doit jamais retarder un montage (retour du 09/11).
        d = new_job("bilan", auto=True)
        asyncio.get_running_loop().create_task(background_bilan(ctx.bot, q.message.chat_id, d))


async def background_bilan(bot, chat_id: int, d: Path) -> None:
    """Bilan des notes en silence, à côté des montages. Un seul message à la fin, s'il a changé quelque chose."""
    current_bg.add(d.name)
    try:
        code = await run_job(d)
        summary = (d / "out" / "summary.md")
        if code == 0 and summary.exists():
            await bot.send_message(chat_id, "🧠 J'ai relu tes 5 dernières notes et mis à jour ton style :\n"
                                   + summary.read_text()[:1500])
    except Exception:  # noqa: BLE001
        log.exception("bilan")
    finally:
        current_bg.discard(d.name)


def last_claude_text(log_path: Path) -> str:
    """Dernière phrase écrite par Claude dans le journal stream-json (pour l'avancement entre deux étapes)."""
    try:
        with open(log_path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            tail = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return ""
    for line in reversed(tail):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict) or not isinstance(d.get("message"), dict):
            continue  # ligne coupée ou d'un autre format (cause du blocage du 09/11)
        content = d["message"].get("content")
        if d.get("type") == "assistant" and isinstance(content, list):
            for c in reversed(content):
                if isinstance(c, dict) and c.get("type") == "text" and str(c.get("text", "")).strip():
                    return c["text"].strip().splitlines()[0]
    return ""


DURATIONS = JOBS / "durees.jsonl"
DEFAULT_MIN = {"phrases": 10, "guided": 20, "build": 25, "plan": 20, "feedback": 25, "edit": 25, "clip": 30,
               "script": 8, "ask": 4, "style": 40, "bilan": 10}


def job_kind(job_dir: Path) -> str:
    try:
        j = json.loads((job_dir / "job.json").read_text())
    except (OSError, ValueError):
        return "edit"
    return j.get("phase") or j.get("type") or "edit"


def estimate_min(kind: str) -> float:
    """Durée prévue : médiane des 5 derniers jobs du même genre (sinon une valeur par défaut)."""
    past = []
    try:
        for line in DURATIONS.read_text().splitlines()[-200:]:
            d = json.loads(line)
            if d.get("kind") == kind and d.get("ok"):
                past.append(d["min"])
    except (OSError, ValueError):
        pass
    if not past:  # pas encore d'historique : on mesure les anciens jobs (nom = heure de départ, claude.log = fin)
        for d in sorted(JOBS.glob("2*-*"))[-60:]:
            try:
                if job_kind(d) != kind or not any((d / "out").glob("*")):
                    continue
                start = time.mktime(time.strptime(d.name[:15], "%Y%m%d-%H%M%S"))
                m = ((d / "claude.log").stat().st_mtime - start) / 60
                if 1 < m < 180:
                    past.append(round(m, 1))
            except (OSError, ValueError):
                continue
    past = sorted(past[-5:])
    return past[len(past) // 2] if past else DEFAULT_MIN.get(kind, 25)


def progress_bar(elapsed: float, total: float) -> str:
    frac = min(elapsed / total, 0.97) if total else 0
    n = round(frac * 12)
    left = total - elapsed
    eta = (f"encore ~{round(left)} min" if left >= 1.5 else "moins d'1 min" if left > 0
           else "presque fini (un peu plus long que prévu)")
    return f"{'▰' * n}{'▱' * (12 - n)} {round(frac * 100)} % · {eta}"


async def worker(app: Application) -> None:
    """Ne meurt jamais : une erreur sur un job ne bloque pas toute la file (blocage du 09/11)."""
    while True:
        chat_id, job_dir = await queue.get()
        try:
            await process_job(app, chat_id, job_dir)
        except Exception as e:  # noqa: BLE001
            log.exception("job %s", job_dir.name)
            current.pop(job_dir.name, None)
            queue.task_done()
            try:
                await app.bot.send_message(chat_id, f"⚠️ {job_dir.name} a planté ({type(e).__name__}), je passe à la suite.")
            except Exception:  # noqa: BLE001
                pass


async def process_job(app: Application, chat_id: int, job_dir: Path) -> None:
    if True:  # (corps historique du worker)
        current[job_dir.name] = job_dir
        kind, t0 = job_kind(job_dir), time.time()
        total = estimate_min(kind)
        bar_msg = await app.bot.send_message(chat_id, f"🎬 Je commence {job_dir.name}\n" + progress_bar(0, total))
        bar_at, bar_text = t0, ""
        task = asyncio.create_task(run_job(job_dir))
        seen, quiet, last_note = 0, 0, ""
        while not task.done():
            await asyncio.sleep(20)
            el = (time.time() - t0) / 60
            text = f"⏳ {job_dir.name}\n" + progress_bar(el, total)
            try:
                if time.time() - bar_at >= 300:  # toutes les 5 min : nouvelle barre en bas de la conversation
                    try:
                        await bar_msg.delete()
                    except Exception:  # noqa: BLE001
                        pass
                    bar_msg, bar_at = await app.bot.send_message(chat_id, text), time.time()
                elif text != bar_text:
                    await bar_msg.edit_text(text)
                bar_text = text
            except Exception:  # noqa: BLE001
                log.debug("barre", exc_info=True)
            try:
                lines = (job_dir / "progress.log").read_text().splitlines()
            except OSError:
                lines = []
            if len(lines) > seen:
                await app.bot.send_message(chat_id, "\n".join("• " + x for x in lines[seen:])[-3900:])
                seen, quiet = len(lines), 0
                continue
            quiet += 20
            # Silence de plus de 3 min : on dit ce que l'équipe est en train de faire (dernier message de Claude).
            if quiet >= 180:
                note = last_claude_text(job_dir / "claude.log")
                if note and note != last_note:
                    await app.bot.send_message(chat_id, "⏳ " + note[:600])
                    last_note = note
                quiet = 0
        stopped = json.loads((job_dir / "job.json").read_text()).get("stopped")
        try:
            await bar_msg.edit_text(f"{'✅' if not stopped else '🛑'} {job_dir.name} · {round((time.time() - t0) / 60)} min")
            ok = not stopped and task.exception() is None and task.result() == 0
            with open(DURATIONS, "a") as f:
                f.write(json.dumps({"kind": kind, "min": round((time.time() - t0) / 60, 1), "ok": ok}) + "\n")
        except Exception:  # noqa: BLE001
            pass
        try:
            if not stopped:
                await send_outputs(app, chat_id, job_dir, task.result())
        except Exception as e:  # noqa: BLE001
            log.exception("envoi")
            await app.bot.send_message(chat_id, f"⚠️ Erreur à l'envoi : {e}")
        current.pop(job_dir.name, None)
        queue.task_done()
        if queue.empty() and not current:  # job fini : on installe les améliorations en attente
            try:
                await update_and_restart(app)
            except Exception:  # noqa: BLE001
                log.exception("mise à jour")


async def watch_switch(app: Application) -> None:
    """L'autre machine a pris la main (/mac ou /serveur) : on se met en veille dès qu'aucun job ne tourne."""
    while True:
        await asyncio.sleep(30 if switch.ON_MAC else 10)
        if not switch.vps_host() and switch.ON_MAC:
            continue
        if not current and queue.empty() and await asyncio.to_thread(switch.mode) != switch.here():
            log.warning("L'autre machine a pris la main : je passe en veille.")
            os._exit(0)  # le lanceur relance bot.py, qui attend son tour


async def post_init(app: Application) -> None:
    JOBS.mkdir(parents=True, exist_ok=True)
    if WOKE_UP:
        await app.bot.send_message(ALLOWED, "💻 Je tourne maintenant sur ton Mac. Tu peux m'envoyer des chemins de "
                                            "fichiers du Mac. /serveur pour repasser sur le serveur."
                                   if switch.ON_MAC else
                                   "🟢 Je tourne maintenant sur le serveur, 24 h/24. Envoie tes vidéos directement ici. "
                                   "/mac pour repasser sur ton Mac.")
    asyncio.get_running_loop().create_task(watch_switch(app))
    try:  # nom choisi par Mehdi (08/11)
        if (await app.bot.get_my_name()).name != BOT_NAME:
            await app.bot.set_my_name(BOT_NAME)
            await app.bot.set_my_short_description("Ton monteur vidéo : interviews, intros, shorts. Darija et français.")
    except Exception:  # noqa: BLE001
        log.exception("nom du bot")
    for _ in range(MAX_JOBS):
        asyncio.get_running_loop().create_task(worker(app))
    asyncio.get_running_loop().create_task(updater(app))


@only_me
async def cmd_vps(update: Update, ctx):
    """/vps IP MOTDEPASSE API_ID API_HASH : le bot installe le VPS lui-même, puis lui passe le relais."""
    m = update.message
    args = (m.text or "").split()[1:]
    try:
        await m.delete()  # le mot de passe ne reste pas dans la conversation
        deleted = True
    except Exception:  # noqa: BLE001
        deleted = False
    if len(args) != 4:
        await ctx.bot.send_message(ALLOWED, "Écris : /vps IP MOTDEPASSE API_ID API_HASH (sur une ligne, séparés par des espaces).")
        return
    if current or not queue.empty():
        await ctx.bot.send_message(ALLOWED, "Un montage est en cours : renvoie /vps quand il sera fini.")
        return
    ip, pwd, api_id, api_hash = args
    ip = re.sub(r"^(https?://|root@)", "", ip.strip("<>[]()")).rstrip("/")
    if not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}|[\w.-]+\.[a-z]{2,}", ip):
        await ctx.bot.send_message(ALLOWED, f"⚠️ « {ip[:30]} » n'est pas une adresse IP. Elle ressemble à 185.12.34.56 "
                                            "(dans le mail de Contabo, ligne « IP address »). Renvoie /vps avec l'IP en 1er.")
        return
    if not api_id.isdigit():
        await ctx.bot.send_message(ALLOWED, "⚠️ L'api_id doit être uniquement des chiffres (3e élément). Ordre : "
                                            "/vps IP MOTDEPASSE API_ID API_HASH")
        return
    await ctx.bot.send_message(ALLOWED, "🚀 Je m'occupe du VPS." + ("" if deleted else
                               " Supprime ton message avec le mot de passe (appui long > Supprimer)."))
    loop = asyncio.get_running_loop()
    report = lambda t: asyncio.run_coroutine_threadsafe(ctx.bot.send_message(ALLOWED, t), loop)
    import importlib
    import vps
    importlib.reload(vps)  # toujours la dernière version du fichier
    try:
        ok, tail = await asyncio.to_thread(vps.install, ip, pwd, api_id, api_hash, report)
    except Exception as e:  # noqa: BLE001
        await ctx.bot.send_message(ALLOWED, f"⚠️ Connexion au VPS impossible : {type(e).__name__} {e}. "
                                            "Vérifie l'IP et le mot de passe, puis renvoie /vps.")
        return
    if not ok:
        await ctx.bot.send_message(ALLOWED, "⚠️ L'installation a échoué. Fin du journal (à transmettre à Claude) :\n" + tail[-3000:])
        return
    (REPO / ".vps-host").write_text(ip + "\n")
    await ctx.bot.send_message(ALLOWED, "✅ Serveur installé. Je reste sur ton Mac : envoie /serveur pour basculer "
                                        "dessus, /mac pour revenir.")


@only_me
async def cmd_switch(update: Update, ctx):
    """/mac ou /serveur : une seule machine lit Telegram, l'autre attend en veille."""
    m = update.message
    want = "mac" if (m.text or "").lstrip("/").lower().startswith("mac") else "vps"
    label = "ton Mac" if want == "mac" else "le serveur"
    if want == switch.here():
        await m.reply_text(f"Je suis déjà sur {label}. 👍")
        return
    if current or not queue.empty():
        await m.reply_text(f"Un montage est en cours : je passe sur {label} dès qu'il est fini. Renvoie la commande à ce moment-là.")
        return
    if want == "mac" and not switch.mac_alive():
        await m.reply_text("Ton Mac ne répond pas (éteint, en veille ou sans internet). Allume-le et ouvre la session : "
                           "le bot du Mac démarre tout seul. Puis renvoie /mac.")
        return
    if want == "vps":
        code, out = await asyncio.to_thread(switch.ssh, "systemctl is-enabled video-bot")
        if code != 0:
            await m.reply_text("Je n'arrive pas à joindre le serveur depuis ton Mac. Je reste sur le Mac.")
            log.warning("serveur injoignable : %s", out[-300:])
            return
    await m.reply_text(f"🔀 Je passe sur {label}, prêt dans 1 min environ." +
                       (" (Pour revenir sur le Mac, attends 10 min : délai imposé par Telegram.)" if want == "vps" else ""))
    ok, out = await asyncio.to_thread(switch.set_mode, want)
    if not ok:
        await m.reply_text("⚠️ Bascule impossible, je reste ici : " + out[-300:])
        return
    try:
        # Telegram : un bot ne doit être connecté qu'à un seul serveur (cloud pour le Mac, serveur local pour le VPS).
        await ctx.bot.log_out()
    except Exception:  # noqa: BLE001
        log.exception("log_out")
    await asyncio.sleep(1)
    os._exit(0)


_conflict_since = [0.0]


async def on_error(update, ctx) -> None:
    """Deux bots avec le même jeton (le Mac et le VPS) : le Mac s'efface et laisse le VPS travailler."""
    import time
    from telegram.error import Conflict, InvalidToken
    if not isinstance(ctx.error, (Conflict, InvalidToken)):
        log.error("erreur", exc_info=ctx.error)
        return
    now = time.time()
    if not _conflict_since[0] or now - _conflict_since[0] > 120:
        _conflict_since[0] = now  # premier conflit : peut-être juste un redémarrage, on attend
        return
    if now - _conflict_since[0] > 60 and not current:
        log.warning("Telegram refuse ce bot (autre machine active ou délai après bascule) : je redémarre.")
        await asyncio.sleep(30)
        os._exit(0)


def stop_other_bots() -> None:
    """Un seul bot à la fois : deux bots avec le même jeton se volent les messages."""
    try:
        out = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True).stdout
    except OSError:
        return
    for line in out.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if not pid.isdigit() or int(pid) == os.getpid():
            continue
        prog = cmd.split()[0].rsplit("/", 1)[-1].lower() if cmd.split() else ""
        if prog.startswith("python") and re.search(r"(^|\s|/)bot\.py(\s|$)", cmd):
            try:
                os.kill(int(pid), 15)
                log.warning("Ancien bot arrêté (pid %s).", pid)
            except OSError:
                pass


WOKE_UP = False
BOT_NAME = "Cutmaster"


def main() -> None:
    global WOKE_UP
    stop_other_bots()
    WOKE_UP = switch.wait_my_turn(log)  # l'autre machine travaille : veille jusqu'à /mac ou /serveur
    log.info("Bot démarré. Utilisateur autorisé : %s", ALLOWED)
    b = Application.builder().token(TOKEN).post_init(post_init)
    if API_URL:
        b = b.base_url(API_URL).base_file_url(API_URL.replace("/bot", "/file/bot")).local_mode(True)
    app = b.read_timeout(600).write_timeout(600).build()
    app.add_handler(CommandHandler(["start", "aide"], cmd_start))
    app.add_handler(CommandHandler("script", cmd_script))
    app.add_handler(CommandHandler("clip", cmd_clip))
    app.add_handler(CommandHandler("statut", cmd_statut))
    app.add_handler(CommandHandler("style", cmd_style))
    app.add_handler(CommandHandler("maj", cmd_maj))
    app.add_handler(CommandHandler("bilan", cmd_bilan))
    app.add_handler(CommandHandler("annuler", cmd_annuler))
    app.add_error_handler(on_error)
    app.add_handler(CommandHandler("vps", cmd_vps))
    app.add_handler(CommandHandler(["mac", "serveur", "server"], cmd_switch))
    app.add_handler(CommandHandler(["phrases", "guide"], cmd_phrases))
    app.add_handler(CommandHandler(["stop", "stoppe"], cmd_stop))
    app.add_handler(CallbackQueryHandler(on_rate, pattern=r"^rate:"))
    app.add_handler(CallbackQueryHandler(on_music_pick, pattern=r"^music:"))
    app.add_handler(CommandHandler(["musique", "musiques"], cmd_musique))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, on_video))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.AUDIO, on_audio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
