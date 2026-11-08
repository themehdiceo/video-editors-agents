---
name: short-editor
description: Monter une vidéo finie (YouTube 16:9 par défaut, ou short 9:16) - coupes propres, B-roll, titres et animations, sous-titres, musique, contrôle qualité. Utiliser pour tout job edit en phase build (ou sans phase).
---
# Montage (phase build)

Lis `style/style.json` avant de commencer. C'est le goût de Mehdi, et il prime sur tes choix par défaut.

## Si le job vient d'un plan validé (`parent` et `choices` dans job.json)
- Le dossier `work/` contient déjà le travail de la phase plan (words.json, silences.json, keep.json, plan_options.json) : réutilise-le, ne recommence pas.
- Lis `work/plan.md` (le plan envoyé à Mehdi) et `choices` (sa réponse). « ok » = toutes les ⭐. « 1B 3A » = ces options, ⭐ pour les autres. Une idée écrite par Mehdi remplace l'option.
- Monte EXACTEMENT ce qu'il a choisi, scène par scène. Ne rajoute pas d'effet non choisi.
- Écris `work/cuesheet.md` : chaque scène, ce qui apparaît à l'écran, à quel moment, et le son qui va avec (whoosh à l'entrée d'un titre, pop sur une notification, montée sur un compteur). L'ingé son s'en sert.

## Étapes (une ligne dans progress.log par étape)
1. **Préparer** : `ffprobe` la source `input/source.*` (durée, résolution, orientation, fps). Ne la copie pas : travaille directement dessus.
2. **Coupes** → agent `monteur-aroll`. Résultat : `work/aroll_cut.mp4`, `work/words.json`, `work/words_cut.json`, timemap.
3. **Script de référence** : s'il existe un `out/script.md` d'un job précédent (lien dans job.json), utilise sa shot list.
4. **B-roll** → agent `documentaliste-broll` (en parallèle de l'étape 5).
5. **Son** → agent `inge-son`.
6. **Habillage** → agent `motion-designer`, seulement pour : un chiffre clé, un nom propre important, ou un trou de B-roll de plus de 4 s.
7. **Assemblage et QA** → agent `controle-qualite`.
8. **Résumé** dans `out/summary.md`.

## Règles de montage (YouTube 16:9, par défaut)
- Le style choisi (`style/<nom>/STYLE.md`) prime sur les règles ci-dessous.
- **Rythme long format** : plein gaz sur le hook et au début de chaque chapitre (plans courts, B-roll, sons). Au milieu, on laisse respirer : plans de 1 à 2 s de plus, moins d'effets.
- **Hook d'interview / témoignage** : 20 à 40 s d'extraits coupés de l'interview (les phrases les plus fortes, chiffres, émotions), montés serrés pour donner envie de connaître la suite. Puis titre, puis l'interview.
- Visage environ 1/3 du temps dans les parties rythmées ; le reste en vraies images liées à ce qui est dit.
- Plein écran sur celui qui parle. Recadre pour enlever navigateur, barre Meet et vignettes inutiles.
- Titres et animations aux moments clés (chiffres, preuves, phrases fortes), pas en continu.
- Sous-titres en bas (style.json), mot actif surligné.

## Règles de montage (short 9:16, si demandé : réglages `short_9x16`)
- Coupes : transcription ET forme d'onde. Jamais au milieu d'un mot. Pause maximale `pacing.max_pause_s`.
- Les 2 premières secondes montrent la chose en action (B-roll plein écran), pas le visage.
- Ensuite, alternance : split `top` (B-roll en haut, visage en bas) la plupart du temps, plein écran B-roll pour les moments forts, visage plein écran pour la chute.
- Un changement de plan toutes les 1,8 à 3,6 s.
- Sous-titres toujours présents, mot actif surligné.
- Musique sous la voix avec ducking. Jamais de musique plus forte que la voix.

## Leçons apprises
<!-- Le skill-keeper ajoute ici les retours de Mehdi, datés. -->
