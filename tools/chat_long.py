"""Hook UserPromptSubmit : passé 150 tours, rappelle à Claude de proposer un chat neuf (règle Mehdi 20/11 : 1 vidéo = 1 chat).

Chaque message relit tout le chat : un chat de 600 tours coûte 10x plus par message qu'un chat neuf.
"""
import json
import sys

SEUIL = 150

try:
    path = json.load(sys.stdin).get("transcript_path") or ""
    tours = sum('"type":"assistant"' in l for l in open(path, errors="ignore"))
except Exception:
    sys.exit(0)
if tours >= SEUIL:
    print(f"Chat long ({tours} tours) : chaque message relit tout l'historique. À la fin de l'étape en cours, "
          "propose à Mehdi (QCM) d'ouvrir un chat neuf. Avant, écris le résumé de reprise dans le dossier du job "
          "(work/reprise.md) : consignes de Mehdi, minutages, chemin de plan.json, style utilisé, ce qui reste à faire.")
