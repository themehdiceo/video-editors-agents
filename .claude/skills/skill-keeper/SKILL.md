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
