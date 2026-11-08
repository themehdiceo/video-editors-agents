"""Bascule Mac <-> serveur (VPS) depuis Telegram : /mac et /serveur.

Un seul bot à la fois peut lire les messages Telegram. Le fichier « .actif » du VPS dit lequel travaille
(« mac » ou « vps »). L'autre reste en veille et regarde ce fichier :
- le VPS le lit sur son disque toutes les 10 s ;
- le Mac le lit en SSH (clé du Mac) toutes les 30 s, et y laisse un signe de vie (.mac-vu).
"""
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(os.environ.get("REPO_DIR", Path(__file__).resolve().parents[1]))
VPS_DIR = "/opt/video-editors-agents"
MODE_FILE = REPO / ".actif"  # côté VPS
SEEN_FILE = REPO / ".mac-vu"  # côté VPS : dernier signe de vie du Mac
ON_MAC = sys.platform == "darwin"


def vps_host() -> str:
    host = os.environ.get("VPS_HOST", "").strip()
    f = REPO / ".vps-host"
    if not host and f.exists():
        host = f.read_text().strip()
    return host


def ssh(cmd: str, timeout: int = 20) -> tuple[int, str]:
    host = vps_host()
    if not host:
        return 255, "pas d'adresse du serveur (.vps-host)"
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=accept-new",
                            f"root@{host}", cmd], capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 255, str(e)


def mode() -> str:
    """« mac » ou « vps » : qui doit lire Telegram. Serveur injoignable depuis le Mac -> le Mac travaille."""
    if ON_MAC:
        code, out = ssh(f"cat {VPS_DIR}/.actif 2>/dev/null; date +%s > {VPS_DIR}/.mac-vu; "
                        f"chown editor:editor {VPS_DIR}/.mac-vu 2>/dev/null; true")
        if code != 0:
            return "mac"  # serveur injoignable : le Mac travaille
        word = out.split()[0] if out.split() else "vps"  # pas de fichier = le serveur travaille (par défaut)
        return "mac" if word == "mac" else "vps"
    try:
        return "mac" if MODE_FILE.read_text().strip() == "mac" else "vps"
    except OSError:
        return "vps"


def here() -> str:
    return "mac" if ON_MAC else "vps"


def wait_my_turn(log) -> bool:
    """Bloque tant que c'est l'autre machine qui travaille. Retourne True s'il a fallu attendre."""
    waited = False
    while mode() != here():
        if not waited:
            log.info("En veille : c'est %s qui travaille. Envoie /%s sur Telegram pour me réveiller.",
                     "le serveur" if ON_MAC else "le Mac", "mac" if ON_MAC else "serveur")
        waited = True
        time.sleep(30 if ON_MAC else 10)
    return waited


def mac_alive() -> bool:
    """Côté VPS : le Mac a donné signe de vie il y a moins de 2 min."""
    try:
        return time.time() - int(SEEN_FILE.read_text().split()[0]) < 120
    except (OSError, ValueError, IndexError):
        return False


def set_mode(word: str) -> tuple[bool, str]:
    if ON_MAC:
        code, out = ssh(f"echo {word} > {VPS_DIR}/.actif && chown editor:editor {VPS_DIR}/.actif")
        return code == 0, out
    MODE_FILE.write_text(word + "\n")
    return True, ""
