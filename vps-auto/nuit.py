#!/usr/bin/env python3
"""Chaîne Pixar de nuit (SOP 1 v3).

  nuit.py nuit          cron 23h Maroc : 2 Pixar finis par nuit à partir de pixar-nuit/histoires-validees/
                        planche puis vidéo dans la foulée (plus d'OK n°2 : veto 2 h avant, Mehdi 21/11), contrôle bloquant
  nuit.py matin         cron 8h Maroc : envoie à Mehdi par Telegram ce que la nuit a produit
  nuit.py bunny         cron 15 min : histoires avec « ok3: oui » -> Bunny (bunny.py), puis suppression locale
  nuit.py test FICHIER  le test du 20/11 : script + planche considérés validés (« go build » de Mehdi), budget 60 cr
"""
import json, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commun as _c
_c.SUJET = "🎬 Pixar"
from commun import (ETAT, KIT, VAULT, Verrou, boite_matin, frontmatter, journal, lancer_claude,
                    maj_frontmatter, maintenant, nouveau_job, pret, tg_fichier, tg_texte)

REPONDRE = "Réponds dans Claude (ou en répondant à ce message) en texte libre : « ok », « non », « change la scène 3… »."

PIXAR = VAULT / "Claude/Livrables/pixar-nuit"
VALIDEES = PIXAR / "histoires-validees"
RESULTATS = PIXAR / "resultats"
PAR_NUIT = 1  # Mehdi 2026-11-23 12h27 : 1 Pixar par jour (10h00), moule du prof v3, sans OK à chaque fois (veto « stop »)
BUDGET = 140  # crédits max pour la vidéo (Seedance 2.0 720p ≈ 6 clips × 22,5) ; planche ≈ 25 cr
GEL = ETAT / "pixar-gel"  # fichier présent = automatique gelé (Mehdi valide d'abord un Pixar test)

LIRE_KIT = (
    "Lis d'abord, dans cet ordre : kit-pixar-v1/3-exemple-prof-v3/README.md + structure.md (modèle OBLIGATOIRE, un moule : "
    "on change l'histoire, jamais la structure, les sous-titres ni le montage), kit-pixar-v1/5-banque-pixar/SOP-1-pixar-par-jour.md "
    "(section Garde-fous), kit-pixar-v1/1-reglages/reglages-defaut.json (OBLIGATOIRE), kit-pixar-v1/2-style/lecons.md "
    "(une correction déjà faite ne revient JAMAIS), la skill anthropic-skills:montage-video-mehdi, puis kit-pixar-v1/README.md, "
    "kit-pixar-v1/2-style/STYLE.md, kit-pixar-v1/2-style/feedback-video.md, kit-pixar-v1/4-voix/REGLES-VOIX.md, kit-pixar-v1/5-banque-pixar/INDEX.md. "
    "ICP : si le métier du héros n'est pas dans vps-auto/icp_metiers.json « autorises » (ou « rares »), ou si le hook le montre en réparateur/ouvrier (« je répare… »), ARRÊTE-TOI sans rien générer et écris-le dans resultat.md. Darija : kit-pixar-v1/2-style/darija-pixar.md OBLIGATOIRE (Casablanca de la rue, « les clients », jamais un mot rare). Chaque plan respecte sa colonne « Logique du lieu » (objets du métier, personne debout sur un meuble, geste réaliste) : vérifie-le sur la planche, refais l'image sinon. Écrans de téléphone/chat TOUJOURS en français ou darija (jamais en anglais), en lien avec l'histoire. Interdits : histoire écrite ou coupée pour économiser des crédits (budget insuffisant = arrête-toi et écris-le dans resultat.md), "
    "personnage en image fixe, version au rabais. Les chemins « banque-pixar/ » et « tools/pixar/ » du kit = kit-pixar-v1/5-banque-pixar/ et kit-pixar-v1/6-outils/. "
    "N'utilise JAMAIS mapwarp.py. Voix : kit-pixar-v1/4-voix/tts-boucle.py (Gemini, jamais de voix clonée, aucun traitement)."
)
CREDITS = (
    "Crédits Higgsfield : budget {b} crédits MAX pour ce Pixar (bloqué automatiquement au-delà), plafond 750/semaine. "
    "Prends les plans les moins chers : plans de kit-pixar-v1/5-banque-pixar/plans/ = 0 crédit, images animées pour les plans calmes, "
    "Seedance 2.0 720p 5 s max (lip-sync) pour action/dialogue, comme le prof v3 validé (Kling gelé le 2026-11-23 : pas de lip-sync). Vérifie avec estimate_video_cost / estimate_image_cost avant. "
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
            "Range les images générées (le jour même, règle banque) dans "
            "/root/vault/Claude/Livrables/kit-pixar-v1/5-banque-pixar/images/AAAA-MM-JJ-titre/ (le coffre : la copie kit-pixar-v1/ "
            "du dépôt est écrasée par la synchro toutes les 2 min, n'y écris jamais). "
            + CREDITS.format(b=25, j=job) +
            extra + f" Termine par {job}/out/resultat.md (3 à 6 lignes : plans prévus, lesquels en vidéo, coût prévu de la vidéo).")


def prompt_video(h: Path, job: Path, planche: str, budget: int = BUDGET, extra: str = "") -> str:
    return (f"Pixar de nuit, étape VIDÉO. Histoire : {h}. Planche validée (OK n°2) : {planche} "
            f"(voix et images dans le dossier du job de la planche, à réutiliser). Dossier de travail : {job}/. {LIRE_KIT}\n"
            "Fais : vidéos (Seedance 720p pour action/dialogue, sinon images animées x4 + zoom ≤ 1.08 ou plans banque), "
            f"range chaque clip payé dans {job}/plans/ (nom = scène), "
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
            extra + f" Écris {job}/out/legende.txt : la légende Instagram (guide kit-pixar-v1/2-style/legendes-instagram.md, "
            "3 lignes max, français simple, aucun hashtag, dernière ligne mot pour mot : 💬 Commente « PLACE » pour recevoir la stratégie de @themehdiceo), "
            "relue par Jérémy, jamais la même accroche que le Pixar d'avant (registre)."
            f" Termine par {job}/out/resultat.md (3 à 6 lignes, verdict qc, doutes).")


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


def icp_ok(h: Path, legende: str = "") -> bool:
    """Garde-fou BLOQUANT (Mehdi 2026-11-24) : métier hors liste = 0 crédit, rien en file, message court."""
    import icp
    ok, raison = icp.verifier_metier(h, legende)
    if not ok:
        journal(f"ICP refus {h.name} : {raison}")
        maj_frontmatter(h, icp="refus", icp_raison=raison)
        tg_texte(f"⛔ Pixar « {frontmatter(h).get('titre') or h.stem} » bloqué : {raison}. 0 crédit dépensé.")
    return ok


def faire_planche(h: Path, test=False, extra="", auto=False) -> bool:
    if not icp_ok(h):
        return False
    job = nouveau_job("planche-" + h.stem)
    lancer_claude(job, prompt_planche(h, job, extra), 0 if extra else 25, quoi=f"planche Pixar « {h.stem} »", minutes=15)
    planche = job / "out/planche.jpg"
    if not planche.exists():
        journal(f"planche ratée pour {h.name} ({job.name})")
        boite_matin(f"⚠️ Pixar « {frontmatter(h).get('titre') or h.stem} » : images ratées, rien publié.")
        return False
    RESULTATS.mkdir(parents=True, exist_ok=True)
    copie = RESULTATS / f"{h.stem}-planche.jpg"
    shutil.copy(planche, copie)
    maj_frontmatter(h, planche=str(copie), job_planche=str(job), ok2="oui" if test or auto else "non")
    if not test and not auto:
        boite_matin(f"🖼️ Images prêtes : {frontmatter(h).get('titre') or h.stem}. OK pour la vidéo ? Réponds « ok » ou ce qu'il faut changer.", str(planche))
    return True


def faire_video(h: Path, budget=BUDGET, extra="", file=True) -> bool:
    if not icp_ok(h):
        return False
    fm = frontmatter(h)
    job = nouveau_job("video-" + h.stem)
    lancer_claude(job, prompt_video(h, job, f"{fm.get('planche')} (job {fm.get('job_planche')})", budget, extra), budget,
                  quoi=f"vidéo Pixar « {h.stem} »", minutes=40)
    video = job / "out/final.mp4"
    ok, ctl = controle(job) if video.exists() else (False, "vidéo absente")
    if not ok:
        journal(f"vidéo ratée ou contrôle KO pour {h.name} ({job.name})")
        boite_matin(f"⚠️ Pixar « {fm.get('titre') or h.stem} » pas assez bon au contrôle, rien publié.")
        maj_frontmatter(h, video="ratee", job_video=str(job))
        return False
    RESULTATS.mkdir(parents=True, exist_ok=True)
    copie = RESULTATS / f"{h.stem}.mp4"
    shutil.copy(video, copie)
    maj_frontmatter(h, video=str(copie), job_video=str(job), ok3="non")
    import publier
    legende, titre = lire(job / "out/legende.txt"), fm.get("titre") or h.stem
    quand = publier.file_attente(video, titre, legende, h) if file and "PLACE" in legende and icp_ok(h, legende) else None
    if quand:
        maj_frontmatter(h, instagram=quand)
        ig = f"Part le {quand} sur Instagram, sauf si tu réponds « stop »."
    else:
        ig = ("Test : regarde-le et réponds « ok » ou ce qu'il faut changer." if not file else
              "⚠️ Pas mis en file Instagram (envoi raté).")
    cout = lire(job / "out/cout.md")
    import re as _re
    tot = _re.findall(r"Total[^|]*\|[^|]*\|\s*\**([\d,.]+)", cout)
    cr = f" · {tot[-1]} crédits" if tot else ""
    boite_matin(f"{titre}{cr}\n{ig}", str(video))
    return True


def nuit() -> None:
    if maintenant().hour != 23:  # cron lancé à 22h et 23h heure du VPS : on ne garde que 23h Maroc
        return
    if GEL.exists():
        journal("nuit : automatique gelé (etat/pixar-gel)")
        return
    if not pret("la nuit Pixar"):
        return
    faits = 0
    with Verrou(attente_s=2 * 3600):
        for h in histoires():
            if faits >= PAR_NUIT:
                break
            fm = frontmatter(h)
            if fm.get("video") or fm.get("bunny") or fm.get("icp") == "refus":
                continue
            # Veto 2 h avant (Mehdi 21/11) : plus d'OK n°2, Jérémy contrôle ; planche puis vidéo la même nuit.
            if not fm.get("planche") and not faire_planche(h, auto=True):
                continue
            faits += faire_video(h)
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
    """Plans Seedance payés gardés dans la banque (version validée ou refusée, sauf plans critiqués), avec une note."""
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
        (dest / "note.md").write_text(f"Plans payés de « {fm.get('titre') or h.stem} » ({h.name}), version {'validée' if fm.get('ok3') == 'oui' else 'refusée'}. "
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
        garder_plans(h, fm)  # règle banque Mehdi 20/11 : tout plan payé reste réutilisable
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
