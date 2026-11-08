"""Installation du VPS pilotée depuis le bot du Mac (Mehdi ne tape rien dans un Terminal).

/vps IP MOTDEPASSE API_ID API_HASH  -> le bot se connecte en SSH, envoie les clés, lance deploy/install.sh,
puis le VPS prend le relais et le bot du Mac s'arrête.
"""
import io
import os
import re
import subprocess
import sys
import time

INSTALL_URL = "https://raw.githubusercontent.com/themehdiceo/video-editors-agents/main/deploy/install.sh"
KEYS = ("CLAUDE_CODE_OAUTH_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_ID", "ELEVENLABS_API_KEY",
        "PEXELS_API_KEY", "SCRIBE_MODEL", "WHISPER_LANG")


def ensure_paramiko():
    try:
        import paramiko  # noqa: F401
    except ImportError:
        venv = sys.prefix
        uv = os.path.expanduser("~/.local/bin/uv")
        cmd = ([uv, "pip", "install", "-q", "paramiko"] if os.path.exists(uv)
               else [sys.executable, "-m", "pip", "install", "-q", "paramiko"])
        subprocess.run(cmd, check=True, env={**os.environ, "VIRTUAL_ENV": venv}, capture_output=True)
    import paramiko
    return paramiko


def env_text(api_id: str, api_hash: str) -> str:
    lines = [f"{k}={os.environ[k].strip()}" for k in KEYS if os.environ.get(k, "").strip()]
    lines += [f"TELEGRAM_API_ID={api_id}", f"TELEGRAM_API_HASH={api_hash}"]
    return "\n".join(lines) + "\n"


def install(ip: str, password: str, api_id: str, api_hash: str, report) -> tuple[bool, str]:
    """Bloquant (à lancer dans un thread). report(texte) reçoit l'avancement. Retourne (ok, fin du journal)."""
    paramiko = ensure_paramiko()
    report("🔐 Connexion au VPS…")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # Clés SSH du Mac d abord (Contabo refuse souvent le mot de passe), puis le mot de passe.
    c.connect(ip, username="root", password=password, timeout=30, look_for_keys=True, allow_agent=True)
    sftp = c.open_sftp()
    with sftp.open("/root/vea.env", "w") as f:
        f.write(env_text(api_id, api_hash))
    sftp.chmod("/root/vea.env", 0o600)
    # Notes privées des mentors (Obsidian, hors Git) : copiées telles quelles sur le VPS.
    priv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "private")
    if os.path.isdir(priv):
        report("📚 Copie des notes copywriter / Hormozi / Haynes…")
        for root, _, files in os.walk(priv):
            rel = os.path.relpath(root, priv)
            remote = "/root/vea-private" + ("" if rel == "." else "/" + rel.replace(os.sep, "/"))
            c.exec_command(f"mkdir -p '{remote}'")[1].channel.recv_exit_status()
            for f in files:
                sftp.put(os.path.join(root, f), f"{remote}/{f}")
    sftp.close()
    # Dernière version exacte du script (l'adresse « main » de GitHub peut rester en cache 5 min).
    url = INSTALL_URL
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        subprocess.run(["git", "-C", repo, "fetch", "-q", "origin", "main"], timeout=60, check=True)
        sha = subprocess.run(["git", "-C", repo, "rev-parse", "origin/main"], capture_output=True, text=True,
                             check=True).stdout.strip()
        if re.fullmatch(r"[0-9a-f]{40}", sha):
            url = INSTALL_URL.replace("/main/", f"/{sha}/")
    except Exception:  # noqa: BLE001
        pass
    report("📦 Installation en cours (10 à 20 min). Je te donne des nouvelles régulièrement.")
    # nohup : l'installation continue même si le Mac se déconnecte (à la fin, le VPS prend le relais du bot).
    c.exec_command(f"nohup bash -c 'bash <(curl -fsSL {url}) /root/vea.env; echo FIN:$?' "
                   "> /root/vea-install.log 2>&1 < /dev/null &")
    seen, start = 0, time.time()
    while time.time() - start < 45 * 60:
        time.sleep(30)
        _, out, _ = c.exec_command("cat /root/vea-install.log")
        lines = out.read().decode("utf-8", "ignore").splitlines()
        for line in lines[seen:]:
            if line.startswith("==>"):
                report("• " + line[3:].strip())
        seen = len(lines)
        fin = [x for x in lines if x.startswith("FIN:")]
        if fin:
            c.close()
            return fin[-1] == "FIN:0", "\n".join(lines[-15:])
    c.close()
    return False, "Installation trop longue (45 min)."
