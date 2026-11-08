---
name: short-editor
description: Monter un A-roll face caméra en short vertical 9:16 fini - coupes propres, B-roll, split 50/50, sous-titres, musique, animations, contrôle qualité. Utiliser pour tout job de type edit.
---
# Montage d'un short à partir d'un A-roll

Lis `style/style.json` avant de commencer. C'est le goût de Mehdi, et il prime sur tes choix par défaut.

## Étapes (une ligne dans progress.log par étape)
1. **Préparer** : `ffprobe` la source (durée, résolution, orientation, fps). Copie-la en `input/aroll.<ext>` si besoin.
2. **Coupes** → agent `monteur-aroll`. Résultat : `work/aroll_cut.mp4`, `work/words.json`, `work/words_cut.json`, timemap.
3. **Script de référence** : s'il existe un `out/script.md` d'un job précédent (lien dans job.json), utilise sa shot list.
4. **B-roll** → agent `documentaliste-broll` (en parallèle de l'étape 5).
5. **Son** → agent `inge-son`.
6. **Habillage** → agent `motion-designer`, seulement pour : un chiffre clé, un nom propre important, ou un trou de B-roll de plus de 4 s.
7. **Assemblage et QA** → agent `controle-qualite`.
8. **Résumé** dans `out/summary.md`.

## Règles de montage
- Coupes : transcription ET forme d'onde. Jamais au milieu d'un mot. Pause maximale `pacing.max_pause_s`.
- Les 2 premières secondes montrent la chose en action (B-roll plein écran), pas le visage.
- Ensuite, alternance : split `top` (B-roll en haut, visage en bas) la plupart du temps, plein écran B-roll pour les moments forts, visage plein écran pour la chute.
- Un changement de plan toutes les 1,8 à 3,6 s.
- Sous-titres toujours présents, mot actif surligné.
- Musique sous la voix avec ducking. Jamais de musique plus forte que la voix.

## Leçons apprises
<!-- Le skill-keeper ajoute ici les retours de Mehdi, datés. -->
