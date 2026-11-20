#!/usr/bin/env python3
"""Chaîne Pixar de nuit (SOP 1 v3).

  nuit.py nuit          cron 23h Maroc : 2 Pixar max à partir de pixar-nuit/histoires-validees/
                        - histoire sans planche -> voix + images + planche (OK n°2 attendu), pas de vidéo
                        - histoire avec « ok2: oui » -> vidéos, montage, qc_clignote.py OK, résultat dans le coffre
  nuit.py matin         cron 8h Maroc : envoie à Mehdi par Telegram ce que la nuit a produit
  nuit.py bunny         cron 15 min : histoires avec « ok3: oui » -> Bunny (bunny.py), puis suppression locale
  nuit.py test FICHIER  le test du 20/11 : script + planche considérés validés (« go build » de Mehdi), budget 60 cr
"""
import json, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from commun import (ETAT, KIT, VAULT, Verrou, boite_matin, frontmatter, journal, lancer_claude,
                    maj_frontmatter, maintenant, nouveau_job, tg_fichier, tg_texte)

PIXAR = VAULT / "Claude/Livrables/pixar-nuit"
VALIDEES = PIXAR / "histoires-validees"
RESULTATS = PIXAR / "resultats"
PAR_NUIT = 2
BUDGET = 50  # crédits max par Pixar : 2 par nuit x 7 = 700 ≤ 750 (Mehdi 20/11)

LIRE_KIT = (
    "Lis d'abord, dans cet ordre : kit-pixar-v1/3-exemple-prof-v3/README.md + structure.md (modèle OBLIGATOIRE, un moule : "
    "on change l'histoire, jamais la structure, les sous-titres ni le montage), kit-pixar-v1/5-banque-pixar/SOP-1-pixar-par-jour.md "
    "(section Garde-fous), kit-pixar-v1/1-reglages/reglages-defaut.json (OBLIGATOIRE), kit-pixar-v1/2-style/lecons.md "
    "(une correction déjà faite ne revient JAMAIS), la skill anthropic-skills:montage-video-mehdi, puis kit-pixar-v1/README.md, "
    "kit-pixar-v1/2-style/STYLE.md, kit-pixar-v1/2-style/feedback-video.md, kit-pixar-v1/4-voix/REGLES-VOIX.md, kit-pixar-v1/5-banque-pixar/INDEX.md. "
    "Interdits : histoire écrite ou coupée pour économiser des crédits (budget insuffisant = arrête-toi et écris-le dans resultat.md), "
    "personnage en image fixe, version au rabais. Les chemins « banque-pixar/ » et « tools/pixar/ » du kit = kit-pixar-v1/5-banque-pixar/ et kit-pixar-v1/6-outils/. "
    "N'utilise JAMAIS mapwarp.py. Voix : kit-pixar-v1/4-voix/tts-boucle.py (Gemini, jamais de voix clonée, aucun traitement)."
)
CREDITS = (
    "Crédits Higgsfield : budget {b} crédits MAX pour ce Pixar (bloqué automatiquement au-delà), plafond 750/semaine. "
    "Prends les plans les moins chers : plans de kit-pixar-v1/5-banque-pixar/plans/ = 0 crédit, images animées pour les plans calmes, "
    "Seedance 2.0 720p 5 s max SEULEMENT pour action/dialogue. Vérifie avec estimate_video_cost / estimate_image_cost avant. "
    "Jamais d'achat de crédits. Écris le coût réel dans {j}/out/cout.md : crédits ET dollars (1 cr = 0,017 $)."
)

BANQUE_SEULE = (" 0 CRÉDIT pour ce Pixar (plafond hebdo déjà atteint) : n'utilise QUE ce qui est déjà payé dans "
                "kit-pixar-v1/5-banque-pixar/ (plans/, plans/2026-11-20/, images/, decors/, personnages/). Toute génération sera refusée.")


def histoires():
    return sorted(VALIDEES.glob("*.md")) if VALIDEES.exists() else []


def prompt_planche(h: Path, job: Path, extra: str = "") -> str:
    return (f"Pixar de nuit, étape PLANCHE (OK n°2 pas encore donné). Histoire validée par Mehdi (OK n°1) : {h}. "
            f"Dossier de travail : {job}/. {LIRE_KIT}\n"
            "Fais : voix (tts-boucle.py) puis images (Nano Banana 2 + Elements <<<ID>>> de la banque, même personnage = même ID) "
            f"et la planche de tous les plans dans {job}/out/planche.jpg. AUCUNE vidéo Seedance (pas d'OK n°2). "
            "Range les images générées dans kit-pixar-v1/5-banque-pixar/images/AAAA-MM-JJ-titre/ et copie-les aussi dans "
            f"/root/vault/Claude/Livrables/kit-pixar-v1/5-banque-pixar/images/AAAA-MM-JJ-titre/. "
            + CREDITS.format(b=25, j=job) +
            extra + f" Termine par {job}/out/resultat.md (3 à 6 lignes : plans prévus, lesquels en vidéo, coût prévu de la vidéo).")


def prompt_video(h: Path, job: Path, planche: str, budget: int = BUDGET, extra: str = "") -> str:
    return (f"Pixar de nuit, étape VIDÉO. Histoire : {h}. Planche validée (OK n°2) : {planche} "
            f"(voix et images dans le dossier du job de la planche, à réutiliser). Dossier de travail : {job}/. {LIRE_KIT}\n"
            "Fais : vidéos (Seedance 720p seulement action/dialogue, sinon images animées x4 + zoom ≤ 1.08 ou plans banque), "
            f"range chaque clip Seedance payé dans {job}/plans/ (nom = scène), "
            f"montage avec une copie adaptée de kit-pixar-v1/3-exemple-prof-v3/build.py lancée depuis {job}/ (sous-titres darija latine "
            "Avenir Next + mots-clés verts sur toute l'histoire, écran de fin 3 s, mix pic ≤ -1 dB), 24 i/s, 1080x1920, ≤ 45 s. prog.py est interdit (pas de sous-titres). "
            f"Livrable : {job}/out/final.mp4 + {job}/subs.ass. CONTRÔLE BLOQUANT (corrige et revérifie jusqu'à tout OK) : "
            f"1) python3 kit-pixar-v1/6-outils/qc_pixar.py {job}/out/final.mp4 {job}/subs.ass = verdict OK ; "
            "2) l'œil : skill anthropic-skills:regarde, la vidéo seconde par seconde ; "
            "3) planche contact (python3 tools/frames.py) comparée à kit-pixar-v1/3-exemple-prof-v3/planche-fin-v3.jpg ; "
            "4) python3 kit-pixar-v1/6-outils/judge.py ; 5) avis de Jérémy (anthropic-skills:jeremy-haynes-mehdi) oui/non ; "
            "6) note de l'ICP (anthropic-skills:icp-debutant-mehdi) sur 10. "
            f"Écris {job}/out/controle.json : {{\"qc_pixar\": \"OK|KO\", \"oeil\": \"…\", \"planche\": \"…\", \"judge\": \"…\", "
            "\"jeremy\": \"oui|non\", \"jeremy_avis\": \"…\", \"icp_note\": 0-10, \"icp_avis\": \"…\"}. "
            + CREDITS.format(b=budget, j=job) +
            extra + f" Termine par {job}/out/resultat.md (3 à 6 lignes, verdict qc, doutes).")


def qc_ok(video: Path) -> bool:
    r = subprocess.run(["python3", str(KIT / "6-outils/qc_clignote.py"), str(video)], capture_output=True, text=True)
    return r.returncode == 0 and '"verdict": "OK"' in r.stdout


def controle(job: Path) -> tuple[bool, str]:
    """Contrôle BLOQUANT (Mehdi 20/11) : qc_pixar.py (sous-titres, ≤ 45 s, fin 3 s, -1 dB, clignote) + Jérémy oui + ICP ≥ 7."""
    video, ass = job / "out/final.mp4", job / "subs.ass"
    r = subprocess.run(["python3", str(KIT / "6-outils/qc_pixar.py"), str(video), str(ass)], capture_output=True, text=True)
    try:
        q = json.loads(r.stdout)
        ko = [k for k, v in q.items() if isinstance(v, dict) and not v.get("ok")]
    except ValueError:
        ko = ["qc_pixar illisible"]
    try:
        c = json.loads((job / "out/controle.json").read_text())
    except (OSError, ValueError):
        c = {}
    try:
        icp = float(c.get("icp_note", 0))
    except (TypeError, ValueError):
        icp = 0
    if str(c.get("jeremy", "")).strip().lower() != "oui":
        ko.append("Jérémy ≠ oui")
    if icp < 7:
        ko.append(f"ICP {icp:g}/10 < 7")
    txt = (f"Contrôle : {'OK' if not ko else 'KO → ' + ', '.join(ko)}\n"
           f"qc_pixar {'OK' if r.returncode == 0 else 'KO'} · Jérémy {c.get('jeremy', '?')} · ICP {icp:g}/10\n"
           f"Œil : {str(c.get('oeil', '?'))[:200]}\nJudge : {str(c.get('judge', '?'))[:150]}")
    return not ko, txt


def lire(p: Path, defaut="") -> str:
    return p.read_text().strip() if p.exists() else defaut


def faire_planche(h: Path, test=False, extra="") -> bool:
    job = nouveau_job("planche-" + h.stem)
    lancer_claude(job, prompt_planche(h, job, extra), 0 if extra else 25, quoi=f"planche Pixar « {h.stem} »", minutes=15)
    planche = job / "out/planche.jpg"
    if not planche.exists():
        journal(f"planche ratée pour {h.name} ({job.name})")
        boite_matin(f"⚠️ Planche ratée : {h.stem}. Journal : {job}/claude.log")
        return False
    RESULTATS.mkdir(parents=True, exist_ok=True)
    copie = RESULTATS / f"{h.stem}-planche.jpg"
    shutil.copy(planche, copie)
    maj_frontmatter(h, planche=str(copie), job_planche=str(job), ok2="oui" if test else "non")
    if not test:
        boite_matin(f"🖼️ Planche prête : {h.stem}\n{lire(job / 'out/resultat.md')}\n\nOK n°2 ? Écris « ok2: oui » en haut du fichier {h.name}.", str(planche))
    return True


def faire_video(h: Path, budget=BUDGET, extra="") -> bool:
    fm = frontmatter(h)
    job = nouveau_job("video-" + h.stem)
    lancer_claude(job, prompt_video(h, job, f"{fm.get('planche')} (job {fm.get('job_planche')})", budget, extra), budget,
                  quoi=f"vidéo Pixar « {h.stem} »", minutes=40)
    video = job / "out/final.mp4"
    ok, ctl = controle(job) if video.exists() else (False, "vidéo absente")
    if not ok:
        journal(f"vidéo ratée ou contrôle KO pour {h.name} ({job.name})")
        boite_matin(f"⚠️ Vidéo Pixar pas livrable (contrôle bloquant) : {h.stem}\n{ctl}\nJournal : {job}/claude.log")
        maj_frontmatter(h, video="ratee", job_video=str(job))
        return False
    RESULTATS.mkdir(parents=True, exist_ok=True)
    copie = RESULTATS / f"{h.stem}.mp4"
    shutil.copy(video, copie)
    maj_frontmatter(h, video=str(copie), job_video=str(job), ok3="non")
    boite_matin(f"🎬 Pixar prêt : {h.stem}\n{ctl}\n{lire(job / 'out/resultat.md')}\n{lire(job / 'out/cout.md')}\n\n"
                f"OK n°3 (Bunny) ? Écris « ok3: oui » en haut du fichier {h.name}. "
                f"Refus : « ok3: refus » (+ « plans_critiques: s3, s7 » si des plans sont à jeter).", str(video))
    return True


def nuit() -> None:
    if maintenant().hour != 23:  # cron lancé à 22h et 23h heure du VPS : on ne garde que 23h Maroc
        return
    faits = 0
    with Verrou(attente_s=2 * 3600):
        for h in histoires():
            if faits >= PAR_NUIT:
                break
            fm = frontmatter(h)
            if fm.get("video") or fm.get("bunny"):
                continue
            if fm.get("ok2") == "oui":
                faits += faire_video(h)
            elif not fm.get("planche"):
                faits += faire_planche(h)
    journal(f"nuit : {faits} Pixar avancé(s)")


def matin() -> None:
    if maintenant().hour != 8:
        return
    f = ETAT / "boite-matin.jsonl"
    if not f.exists():
        return
    lignes = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    f.unlink()
    for m in lignes:
        if m.get("fichier") and Path(m["fichier"]).exists():
            tg_fichier(m["fichier"], m["texte"][:1000])
            if len(m["texte"]) > 1000:
                tg_texte(m["texte"])
        else:
            tg_texte(m["texte"])


def garder_plans(h: Path, fm: dict) -> int:
    """Version refusée : plans Seedance payés gardés dans la banque (sauf critiqués), avec une note."""
    job = Path(fm.get("job_video") or "/x")
    critiques = {c.strip().lower() for c in str(fm.get("plans_critiques", "")).split(",") if c.strip()}
    dest = VAULT / "Claude/Livrables/kit-pixar-v1/5-banque-pixar/plans" / f"{maintenant():%Y-%m-%d}-{h.stem}"[:80]
    n = 0
    for p in sorted((job / "plans").glob("*.mp4")) if (job / "plans").is_dir() else []:
        if p.stem.lower() in critiques:
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(p, dest / p.name)
        n += 1
    if n:
        (dest / "note.md").write_text(f"Plans payés de la version refusée de « {fm.get('titre') or h.stem} » ({h.name}). "
                                      f"Exclus (critiqués par Mehdi) : {', '.join(sorted(critiques)) or 'aucun'}.\n")
    return n


def bunny() -> None:
    import bunny as b
    for h in histoires():
        fm = frontmatter(h)
        if fm.get("ok3") == "refus" and fm.get("video", "").endswith(".mp4"):
            # Refusée : JAMAIS sur Bunny. Plans payés non critiqués -> banque, puis suppression du reste.
            n = garder_plans(h, fm)
            for d in (fm.get("job_video"),):
                if d and Path(d).is_dir() and Path(d).parent.name == "jobs":
                    shutil.rmtree(d)
            Path(fm["video"]).unlink(missing_ok=True)
            maj_frontmatter(h, video="refusee", ok2="non", planche="")
            tg_texte(f"🗑️ « {fm.get('titre') or h.stem} » refusée : pas sur Bunny. {n} plan(s) payé(s) gardé(s) dans la banque, le reste supprimé.")
            continue
        if fm.get("ok3") != "oui" or fm.get("bunny") or not fm.get("video", "").endswith(".mp4"):
            continue
        titre = fm.get("titre") or h.stem
        date = fm.get("date") or f"{maintenant():%Y-%m-%d}"
        vid = b.envoyer(Path(fm["video"]), f"{date} · {titre}")
        if not vid:
            tg_texte(f"⚠️ Envoi Bunny raté pour « {titre} ». Rien supprimé, je réessaie dans 15 min.")
            continue
        for d in (fm.get("job_video"), fm.get("job_planche")):
            if d and Path(d).is_dir() and Path(d).parent.name == "jobs":
                shutil.rmtree(d)
        for p in (fm.get("video"), fm.get("planche")):
            if p:
                Path(p).unlink(missing_ok=True)
        maj_frontmatter(h, bunny=vid, video="sur-bunny")
        anciennes = b.supprimer_anciennes(titre, vid)  # 1 seule version par histoire, après vérif que la nouvelle est en ligne
        tg_texte(f"☁️ « {date} · {titre} » est sur Bunny (collection Stories AI Funnels). Vidéo et brouillons supprimés du VPS."
                 + (f" Ancienne(s) version(s) supprimée(s) de Bunny : {anciennes}." if anciennes else ""))


def test(h: Path) -> None:
    """Test du 20/11 : planche puis vidéo dans la foulée, budget total 60 cr."""
    with Verrou(attente_s=3600):
        extra = ""  # plus jamais de version 100 % banque (refusée par Mehdi le 20/11)
        if not frontmatter(h).get("planche"):
            faire_planche(h, test=True, extra=extra)
        if frontmatter(h).get("planche"):
            faire_video(h, budget=0 if extra else max(0, int(BUDGET - planche_cout(h))), extra=extra)
    journal("test : résultat dans la boîte du matin (envoi 8h)")


def planche_cout(h: Path) -> float:
    f = Path(frontmatter(h).get("job_planche", "/x")) / "credits.json"
    return json.loads(f.read_text())["depense"] if f.exists() else 25


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else ""
    {"nuit": nuit, "matin": matin, "bunny": bunny}.get(a, lambda: test(Path(sys.argv[2])) if a == "test" else print(__doc__))()
