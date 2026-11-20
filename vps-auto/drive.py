#!/usr/bin/env python3
"""DÉSACTIVÉ (2026-11-20 : rushs par Telegram, pas de Drive). Cron 30 min : nouvelles vidéos du dossier Google Drive « PPC · À monter » -> job de montage complet (v1).
Inactif tant que le remote rclone « gdrive: » n'est pas autorisé par Mehdi (voir Tâches VPS/README.md).
Le montage réutilise le runner du bot (bot/runner.py), lancé en utilisateur editor comme le bot.
"""
import asyncio, json, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import ETAT, REPO, Verrou, journal, secrets, tg_fichier, tg_texte

DOSSIER = "gdrive:PPC · À monter"
VUS = ETAT / "drive-vus.json"
VIDEO = (".mp4", ".mov", ".m4v", ".mkv", ".webm")


def monter(fichier: str) -> None:
    """Lancé en editor : crée le job, met la vidéo dedans, lance l'équipe de montage."""
    sys.path.insert(0, str(REPO / "bot"))
    import runner
    src = Path(fichier)
    d = runner.new_job("edit", note=f"Vidéo du Google Drive « PPC · À monter » : {src.name}. Montage complet v1.",
                       input_file="input/source" + src.suffix.lower(), source_path=f"drive:{src.name}")
    shutil.move(str(src), d / "input" / ("source" + src.suffix.lower()))
    asyncio.run(runner.run_job(d))
    print(d)


def main() -> None:
    if "gdrive:" not in subprocess.run(["rclone", "listremotes"], capture_output=True, text=True).stdout:
        return  # pas encore autorisé
    r = subprocess.run(["rclone", "lsjson", DOSSIER, "--files-only"], capture_output=True, text=True)
    if r.returncode:
        journal(f"drive : lecture impossible ({r.stderr.strip()[:200]})")
        return
    vus = set(json.loads(VUS.read_text())) if VUS.exists() else set()
    nouveaux = [f for f in json.loads(r.stdout) if f["Name"].lower().endswith(VIDEO) and f["ID"] not in vus]
    if not nouveaux:
        return
    try:
        verrou = Verrou().__enter__()
    except BlockingIOError:
        return
    try:
        f = nouveaux[0]  # une vidéo à la fois
        tmp = REPO / "jobs" / "_drive"
        tmp.mkdir(exist_ok=True)
        subprocess.run(["rclone", "copy", f"{DOSSIER}/{f['Name']}", str(tmp)], check=True)
        shutil.chown(tmp, "editor", "editor")
        shutil.chown(tmp / f["Name"], "editor", "editor")
        vus.add(f["ID"])
        VUS.write_text(json.dumps(sorted(vus)))
        tg_texte(f"🎞️ Nouvelle vidéo sur le Drive : {f['Name']}. Je lance le montage complet v1.")
        env = {k: v for k, v in secrets().items()} | {"REPO_DIR": str(REPO), "HOME": "/home/editor",
               "PATH": f"{REPO}/.venv/bin:/usr/local/bin:/usr/bin:/bin"}
        # secrets par l'environnement (pas en arguments : visibles dans ps)
        out = subprocess.run(["runuser", "-u", "editor", "--", f"{REPO}/.venv/bin/python", __file__, "monter", str(tmp / f["Name"])],
                             capture_output=True, text=True, cwd=REPO, env=env)
        job = Path(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else None
        final = job / "out/final.mp4" if job else None
        if final and final.exists():
            resume = (job / "out/summary.md").read_text()[:900] if (job / "out/summary.md").exists() else ""
            tg_fichier(final, f"✂️ Montage v1 : {f['Name']}\n{resume}")
        else:
            tg_texte(f"⚠️ Montage raté pour {f['Name']}. Journal : {job or '?'}")
    finally:
        verrou.__exit__()


if __name__ == "__main__":
    monter(sys.argv[2]) if sys.argv[1:2] == ["monter"] else main()
