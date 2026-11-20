#!/usr/bin/env python3
"""Test du 20/11 (« go build » de Mehdi = OK pour CE test seulement) : nouvelle histoire courte -> planche -> vidéo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nuit
from commun import Verrou, journal, lancer_claude, nouveau_job

job = nouveau_job("histoire-test")
cible = nuit.VALIDEES / "2026-11-20-test-vps.md"
prompt = (
    "Écris UNE histoire Pixar NOUVELLE et courte (40-45 s, histoire ≤ 42 s + écran de fin 3 s). "
    "Fais-la écrire par le copywriter (skill anthropic-skills:copywriter-mehdi), relire par l'ICP (anthropic-skills:icp-debutant-mehdi) "
    "et par Jérémy (anthropic-skills:jeremy-haynes-mehdi). Lis avant : kit-pixar-v1/README.md, kit-pixar-v1/2-style/STYLE.md, "
    "kit-pixar-v1/2-style/feedback-video.md, kit-pixar-v1/2-style/lecons.md, kit-pixar-v1/5-banque-pixar/INDEX.md. "
    "Règles : ICP salarié frustré (hook segment 1, jamais les arnaqués), dialogues en darija, règles fixes du README, "
    "fin Mercedes Classe C + villa. CONTRAINTE : 0 crédit Higgsfield cette semaine (plafond atteint), donc l'histoire doit se monter "
    "UNIQUEMENT avec les plans et images déjà payés de kit-pixar-v1/5-banque-pixar/ (plans/, plans/2026-11-20/, images/, decors/) : "
    "écris l'histoire plan par plan en citant le fichier de la banque utilisé pour chaque plan. Histoire différente des pubs existantes. "
    f"Écris-la dans {cible} au format de /root/vault/Claude/Livrables/pixar-nuit/README.md (frontmatter titre + date: 2026-11-20). "
    "Pas de génération Higgsfield."
)
with Verrou(attente_s=600):
    lancer_claude(job, prompt, budget=0, quoi="histoire Pixar de test", minutes=10)
if not cible.exists():
    journal(f"test : histoire pas écrite ({job}/claude.log)")
    sys.exit(1)
nuit.test(cible)
