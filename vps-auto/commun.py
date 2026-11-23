"""Outils communs aux crons du VPS (SOP 1 v3) : secrets, Telegram, verrou, lancement de claude -p.

Les crons tournent en root : seul le login claude.ai de root voit Higgsfield
(le jeton CLAUDE_CODE_OAUTH_TOKEN du bot ne le voit pas).
"""
import fcntl, json, os, re, subprocess, time, urllib.request, uuid
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path("/opt/video-editors-agents")
ICI = REPO / "vps-auto"
ETAT = REPO / "etat"            # hors git
JOBS = REPO / "jobs"
VAULT = Path("/root/vault")
KIT = REPO / "kit-pixar-v1"
MAROC = ZoneInfo("Africa/Casablanca")
ENV_FILE = "/etc/video-editors-agents/.env"
ETAT.mkdir(exist_ok=True)


def secrets() -> dict:
    env = {}
    for line in Path(ENV_FILE).read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def maintenant():
    from datetime import datetime
    return datetime.now(MAROC)


def journal(msg: str) -> None:
    with open(ETAT / "journal.log", "a") as f:
        f.write(f"{maintenant():%Y-%m-%d %H:%M} {msg}\n")


# ---------- Telegram (API publique : le serveur local 8081 n'est pas toujours allumé) ----------

def _tg(method: str, fields: dict, fichier: tuple | None = None) -> bool:
    s = secrets()
    url = f"https://api.telegram.org/bot{s['TELEGRAM_BOT_TOKEN']}/{method}"
    fields = {"chat_id": s["TELEGRAM_ALLOWED_USER_ID"], **fields}
    if fichier:
        champ, chemin = fichier
        b = uuid.uuid4().hex
        corps = b""
        for k, v in fields.items():
            corps += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
        corps += (f"--{b}\r\nContent-Disposition: form-data; name=\"{champ}\"; filename=\"{Path(chemin).name}\"\r\n"
                  "Content-Type: application/octet-stream\r\n\r\n").encode() + Path(chemin).read_bytes() + f"\r\n--{b}--\r\n".encode()
        req = urllib.request.Request(url, corps, {"Content-Type": f"multipart/form-data; boundary={b}"})
    else:
        req = urllib.request.Request(url, json.dumps(fields).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r).get("ok", False)
    except Exception as e:  # jamais le jeton dans le journal
        journal(f"Telegram {method} en échec : {type(e).__name__}")
        return False


def tg_texte(texte: str) -> bool:
    return _tg("sendMessage", {"text": texte[:4000]})


def tg_fichier(chemin, legende: str = "") -> bool:
    p = Path(chemin)
    if p.suffix.lower() == ".mp4" and p.stat().st_size < 49e6:
        return _tg("sendVideo", {"caption": legende[:1000], "supports_streaming": "true"}, ("video", p))
    if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.stat().st_size < 9e6:
        return _tg("sendPhoto", {"caption": legende[:1000]}, ("photo", p))
    return _tg("sendDocument", {"caption": legende[:1000]}, ("document", p))


def boite_matin(texte: str, fichier: str | None = None) -> None:
    """Résultat envoyé dès la fin (règle Mehdi 20/11 21h46). Gardé pour 8h seulement si Telegram échoue."""
    ok = tg_fichier(fichier, texte[:1000]) if fichier and Path(fichier).exists() else tg_texte(texte)
    if ok and fichier and len(texte) > 1000:
        tg_texte(texte)
    if not ok:
        with open(ETAT / "boite-matin.jsonl", "a") as f:
            f.write(json.dumps({"texte": texte, "fichier": fichier}, ensure_ascii=False) + "\n")


# ---------- Verrou : un seul claude -p à la fois sur le VPS ----------

class Verrou:
    def __init__(self, attente_s: int = 0):
        self.attente_s = attente_s

    def __enter__(self):
        self.f = open("/run/lock/sop1-claude.lock", "w")
        fin = time.time() + self.attente_s
        while True:
            try:
                fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() >= fin:
                    raise
                time.sleep(30)

    def __exit__(self, *a):
        self.f.close()


# ---------- claude -p ----------

HIGGSFIELD_OK = [  # aucun outil d'achat, d'abonnement, de GPU ni de publication
    "balance", "transactions", "estimate_image_cost", "estimate_video_cost", "models_explore",
    "generate_image", "generate_image_batch", "generate_video", "generate_video_batch",
    "jobs_wait", "job_display", "show_generation_by_ids", "show_generations", "show_medias",
    "media_upload", "media_confirm", "media_import_url", "show_reference_elements",
    "manage_reference_elements", "get_preferences",
]
OUTILS = [
    "Read", "Write", "Edit", "Glob", "Grep", "Task", "Agent", "Skill", "ToolSearch", "WebFetch", "WebSearch",
    "Write(/root/vault/**)", "Edit(/root/vault/**)",
    "Bash(python3 *)", "Bash(ffmpeg *)", "Bash(ffprobe *)", "Bash(ls *)", "Bash(head *)", "Bash(tail *)",
    "Bash(wc *)", "Bash(cp *)", "Bash(mv *)", "Bash(mkdir *)", "Bash(curl -sSL -o *)", "Bash(curl -sL -o *)",
] + [f"mcp__claude_ai_Higgsfield__{n}" for n in HIGGSFIELD_OK]


def lancer_claude(job_dir: Path, prompt: str, budget: float, timeout_s: int = 3 * 3600, quoi: str = "", minutes: int = 30,
                  outils: list[str] = ()) -> int:
    """claude -p à la racine du dépôt (agents, skills et kit du dépôt), plafond crédits par hooks."""
    # Règle Mehdi 20/11 : annoncer quoi + durée + coût AVANT, résultat à la fin (fait par l'appelant).
    # Mehdi 2026-11-23 : Telegram = seulement le résultat utile (quoi, décision, coût). Le reste va au journal.
    journal(f"début : {quoi or job_dir.name} · ≈ {minutes} min · ≤ {budget:g} cr")
    s = secrets()
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}
    env.update(GEMINI_API_KEY=s.get("GEMINI_API_KEY", ""), JOB_DIR=str(job_dir), CREDITS_JOB_MAX=str(budget),
               PATH=f"{REPO}/.venv/bin:/root/.local/bin:/usr/local/bin:/usr/bin:/bin")
    # « user » obligatoire : sans lui, ni Higgsfield ni les skills anthropic-skills:* ne sont chargés.
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--setting-sources", "user,project,local", "--settings", str(ICI / "claude-settings.json"),
           "--permission-mode", "acceptEdits", "--allowedTools", *OUTILS, *outils]
    with open(job_dir / "claude.log", "ab") as log:
        try:
            code = subprocess.run(cmd, cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=timeout_s).returncode
        except subprocess.TimeoutExpired:
            code = -1
    subprocess.run(["chown", "-R", "editor:editor", str(job_dir)])
    return code


def nouveau_job(nom: str) -> Path:
    slug = re.sub(r"[^a-z0-9]+", "-", nom.lower())[:40].strip("-") or "job"
    d = JOBS / f"{maintenant():%Y%m%d-%H%M%S}-vps-{slug}"
    for sub in ("input", "work", "out"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "progress.log").touch()
    return d


def frontmatter(chemin: Path) -> dict:
    t = chemin.read_text()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    return dict(re.findall(r"^(\w+):\s*(.*?)\s*$", m.group(1), re.M)) if m else {}


def maj_frontmatter(chemin: Path, **champs) -> None:
    t = chemin.read_text()
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    fm, corps = (m.group(1), t[m.end():]) if m else ("", t)
    for k, v in champs.items():
        if re.search(rf"^{k}:", fm, re.M):
            fm = re.sub(rf"^{k}:.*$", f"{k}: {v}", fm, flags=re.M)
        else:
            fm += f"\n{k}: {v}"
    chemin.write_text(f"---\n{fm.strip()}\n---\n{corps}")


# ---------- Santé : rien ne se lance si un service ne répond pas (Mehdi 20/11) ----------

def sante() -> list[str]:
    """Teste Higgsfield, Supabase, Gemini, Telegram sans rien dépenser. Renvoie la liste de ceux qui ne répondent pas."""
    ko = []
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_OAUTH_TOKEN"}
    try:
        out = subprocess.run(["claude", "mcp", "list"], cwd=REPO, env=env, capture_output=True, text=True, timeout=180).stdout
    except (OSError, subprocess.TimeoutExpired):
        out = ""
    for nom in ("Higgsfield", "Supabase"):
        if not re.search(rf"claude\.ai {nom}:.*Connected", out):
            ko.append(nom)
    s = secrets()
    try:
        with urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/models?pageSize=1&key={s.get('GEMINI_API_KEY', '')}", timeout=30):
            pass
    except Exception:
        ko.append("Gemini")
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{s['TELEGRAM_BOT_TOKEN']}/getMe", timeout=30) as r:
            if not json.load(r).get("ok"):
                ko.append("Telegram")
    except Exception:
        ko.append("Telegram")
    return ko


def pret(quoi: str) -> bool:
    """Avant chaque nuit, tâche et lundi. Un service KO = alerte Telegram immédiate et rien ne se lance.
    Même alerte pas renvoyée avant 3 h (pas de spam toutes les 15 min)."""
    ko = sante()
    if not ko:
        (ETAT / "alerte.json").unlink(missing_ok=True)
        return True
    journal(f"santé KO ({', '.join(ko)}) : {quoi} en pause")
    f = ETAT / "alerte.json"
    try:
        a = json.loads(f.read_text())
    except (OSError, ValueError):
        a = {}
    if a.get("ko") != ko or time.time() - a.get("t", 0) > 3 * 3600:
        lien = " Reconnecte-le ici : https://claude.ai/settings/connectors" if {"Higgsfield", "Supabase"} & set(ko) else ""
        tg_texte(f"⚠️ {', '.join(ko)} ne répond plus, {quoi} en pause.{lien}")
        f.write_text(json.dumps({"ko": ko, "t": time.time()}))
    return False
