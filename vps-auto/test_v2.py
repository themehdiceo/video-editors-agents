#!/usr/bin/env python3
"""« go test » de Mehdi (20/11 21:37) : Lchher ljay en VRAI animé, 50 cr max, exception au plafond hebdo pour ce job seulement."""
import os, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
os.environ["EXCEPTION_MEHDI"] = "1"
import nuit
from commun import Verrou, journal
h = nuit.VALIDEES / "2026-11-20-test-vps.md"
t = h.read_text()
t = re.sub(r"^(video|job_video|ok3):.*\n", "", t, flags=re.M)
h.write_text(t)
extra = (" REFAIT car la v1 est REFUSÉE par Mehdi : trop d'images fixes. Style = Anas v7 (kit-pixar-v1/3-exemple-anas-v7/ : 14 plans, "
         "tous en clip vidéo). AUCUNE image fixe pour un personnage ; au plus 1 plan court (≤ 3 s) d'écran/objet en image animée. "
         "Suis la section « Plan v2 animée » du fichier de l'histoire, mais budget 50 cr MAX : 2 plans Seedance 2.0 720p 5 s "
         "(priorité : plan 9 villa face caméra en lip-sync, puis plan 8 Mercedes + cartable), images de départ = images de la banque "
         "(0 cr). Tout le reste = clips déjà payés de la banque (plans/ et plans/2026-11-20/), choisis ceux où le personnage bouge. "
         "Range les nouveaux clips dans kit-pixar-v1/5-banque-pixar/plans/2026-11-20/ ET /root/vault/Claude/Livrables/kit-pixar-v1/5-banque-pixar/plans/2026-11-20/.")
with Verrou(attente_s=600):
    nuit.faire_video(h, budget=50, extra=extra)
journal("test v2 animé : fini")
