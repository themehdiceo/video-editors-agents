"""Lance ffmpeg en écrivant l'avancement et le temps restant dans le progress.log du job.

Utilisé par compose.py et cut.py. Le bot relaie progress.log à Mehdi sur Telegram.
"""
import os
import subprocess
import time


def find_log(path: str):
    """Remonte depuis un fichier du job jusqu'à trouver progress.log."""
    d = os.path.dirname(os.path.abspath(path))
    for _ in range(4):
        p = os.path.join(d, "progress.log")
        if os.path.exists(p):
            return p
        d = os.path.dirname(d)
    return None


def run(cmd: list, total_s: float, log_path, label: str) -> None:
    """cmd = commande ffmpeg complète. Écrit « label : 40 % (encore ~6 min) » toutes les ~2 min."""
    cmd = cmd[:1] + ["-progress", "pipe:1", "-nostats"] + cmd[1:]
    t0 = last = time.time()  # 1re nouvelle après 2 min
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    for line in proc.stdout:
        if not line.startswith("out_time_us=") or not log_path or total_s <= 0:
            continue
        try:
            done = int(line.split("=")[1]) / 1e6
        except ValueError:
            continue
        now = time.time()
        if now - last < 120 or done <= 0:
            continue
        last = now
        pct = min(99, int(100 * done / total_s))
        left = (now - t0) * (total_s - done) / done
        with open(log_path, "a") as f:
            f.write(f"{label} : {pct} % (encore ~{max(1, round(left / 60))} min)\n")
    if proc.wait() != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)
    if log_path:
        with open(log_path, "a") as f:
            f.write(f"{label} : terminé en {max(1, round((time.time() - t0) / 60))} min\n")
