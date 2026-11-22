---
name: skill-keeper
description: Transformer un retour de Mehdi en règle durable - mettre à jour style/style.json ou la section Leçons apprises de la bonne skill, puis commit Git. Utiliser après chaque job feedback et pour /bilan.
---
# Garder les skills à jour

Après chaque retour de Mehdi :

1. **Classe le retour** :
   - réglage chiffré (taille ou couleur des sous-titres, volume de la musique, rythme) → `style/style.json` ;
   - règle de méthode (comment couper, choisir le B-roll, écrire le hook) → section « Leçons apprises » de la skill concernée ;
   - remarque propre à cette vidéo seulement → ne touche à rien.
2. **Écris la règle de façon générale et vérifiable**, datée : `- 2026-11-08 : musique à 0.08 max, Mehdi la trouvait trop présente.`
3. Ne supprime jamais une leçon. Si une nouvelle la contredit, remplace l'ancienne et mentionne-le.
4. **Commit** : `git add -A style .claude && git commit -m "skills: <résumé en une ligne>"` puis `git push` si le remote est configuré.
5. Écris dans `out/skill_update.md` une ligne pour Mehdi : ce qui a changé. Le bot la lui envoie. Il peut annuler avec /annuler (git revert du dernier commit skills).

## /bilan (revue périodique)
Analyse les 10 derniers jobs (`jobs/*/out/summary.md`, retours reçus). Si des statistiques de chaîne sont fournies, croise-les. Propose au plus 5 changements dans `out/bilan.md` et ne les applique pas : Mehdi valide d'abord.

## Bilan automatique (toutes les 5 notes, `auto: true`)
Mehdi note chaque rendu de 1 à 5 étoiles. Les notes sont dans `style/ratings.jsonl` (job, note, consignes reçues).
1. Lis les notes depuis le dernier bilan (`style/learning.md` dit où tu t'étais arrêté), les `summary.md` et `plan.json` de ces jobs, et leurs retours (jobs `feedback` dont le parent est noté).
1b. Lis aussi `style/guided_picks.jsonl` (phrases choisies par Mehdi en mode guidé) : déduis-en ses règles de choix (ouvre sur quoi, ordre, longueur des phrases, ce qu'il évite) et écris-les dans la section « Structure du hook » du STYLE.md, avec 2 ou 3 exemples. Quand ces règles prédisent bien ses choix, le mode automatique pourra les appliquer seul.
2. Vidéos à 4-5 étoiles : ce qui a marché devient une règle « à refaire » dans le STYLE.md du style utilisé (rythme, nombre de cartes, durée du hook…). Copie leur `work/plan.json` dans `style/<nom>/exemples/<job>.json` : c'est un exemple à imiter.
3. Vidéos à 1-3 étoiles : la cause probable devient un garde-fou chiffré dans le STYLE.md.
4. Un même retour répété 2 fois = règle obligatoire (en haut du STYLE.md, section « Règles de Mehdi »).
5. Applique directement (pas besoin de validation), ajoute une ligne datée dans `style/learning.md`, commit `skills: bilan auto`, push.
6. `out/summary.md` : 3 lignes en français simple sur ce que l'équipe a appris.
