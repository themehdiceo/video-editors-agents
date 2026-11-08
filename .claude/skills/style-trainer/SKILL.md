---
name: style-trainer
description: Apprendre un style de montage à partir de 2 à 5 vidéos de référence (YouTube ou fichiers) - analyse image par image, puis style nommé dans style/<nom>/. Utiliser pour tout job de type style.
---
# Apprendre un style de montage

But : que Mehdi puisse écrire « style <nom> » dans un prompt et obtenir ce montage-là. On ne copie pas les vidéos : on en tire des règles mesurées et vérifiables.

Entrées (job.json) : `name` (ex. `interview-v1`), `urls` (ou `style/<name>/refs.txt`), `note` (ce que Mehdi aime dans ces vidéos : elle prime).

## Étapes (une ligne dans progress.log par étape)
1. **Télécharger** chaque référence en 720p dans `work/refs/` :
   `yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" -o "work/refs/ref%(autonumber)s.%(ext)s" <url>`.
   Une URL avec `&t=` indique le passage que Mehdi trouve intéressant : regarde-le en priorité.
   Vidéo de plus de 20 min : garde tout, mais concentre l'analyse fine sur les 3 premières minutes (le hook), le passage `t=`, et 2 minutes au milieu.
2. **Mesurer** : `python3 tools/analyze_refs.py work/refs/ref1.mp4 work/an/ref1` pour chaque vidéo.
   Lis `analysis.json` : coupes/minute (1re minute vs ensuite), durée des plans, luminosité, saturation, volume.
3. **Regarder** : lis TOUTES les planches `shots_XX.jpg` et `minute1.jpg` (outil Read). Pour chaque plan, compare la 1re et la dernière image :
   zoom avant/arrière ? flou à l'entrée ? texte qui apparaît ? split ou plein écran ? B-roll, capture d'écran, photo, vidéo d'archive ? Couleur et étalonnage (chaud, froid, contrasté, N&B) ?
   Zoome sur un moment précis avec `python3 tools/frames.py work/refs/ref1.mp4 work/an/ref1/zoom --at 12.0,12.2,12.4,12.6`.
4. **Écouter** : transcris le début de chaque référence (`python3 tools/transcribe.py work/refs/ref1.mp4 work/an/ref1/words.json --model small --lang auto`). Relie les visuels aux mots : qu'est-ce qui déclenche un plan, un titre, un zoom, un son ? Y a-t-il des jeux de mots visuels (on dit « fuite », on montre un robinet) ?
   Repère aussi les sons : whoosh sur les transitions, pop sur les textes, impacts, musique (énergie, volume sous la voix).
5. **Structure** : découpe chaque référence en parties (hook, intro, chapitres, preuve, appel à l'action) avec leurs durées. Comment le hook est-il construit ? (extraits coupés d'avance, question, chiffre, promesse…)
6. **Écrire le style** dans `style/<name>/` :
   - `STYLE.md` : le livre de règles, en 4 parties.
     1. **Structure** : ordre des parties et durées cibles (ex. hook 20-40 s fait d'extraits de l'interview, puis titre, puis l'interview).
     2. **Rythme** : coupes/minute cibles par partie (chiffres mesurés), durée max d'un plan fixe, règles de respiration.
     3. **Look** : cadrage, zooms, entrées de plan, sous-titres (place, taille, police, couleur, nombre de mots), titres et graphismes, couleurs, B-roll (quel type, quelle fréquence, quelle part du temps à l'écran pour le visage).
     4. **Son** : musique (genre, volume), SFX (où, lesquels).
     Puis une liste de **garde-fous** chiffrés et vérifiables (« aucun plan fixe de plus de 4 s dans le hook », « chaque nouveau plan B-roll entre flou », « visage à l'écran environ 1/3 du temps dans le hook »).
     Pour chaque règle, cite la mesure ou la référence qui la justifie (`ref2 @ 0:14`).
   - `style.json` : uniquement les valeurs qui changent par rapport à `style/style.json` (mêmes clés : subtitles, pacing, music, format…).
   - `refs/` : copie les `analysis.json` (renommés `ref1.json`…) et les 2 planches les plus parlantes, réduites (`ffmpeg -i in.jpg -vf scale=1200:-2 out.jpg`).
7. **Ce que l'équipe sait faire** : rapproche chaque règle des outils (compose.py : `zoom`, `blur_in`, `vf` couleur, images fixes animées ; find_media.py : vraies images ; motion-designer : titres HyperFrames). Si une règle n'est pas réalisable, écris-le dans STYLE.md sous « À construire ».
8. **Commit** : `git add style/<name>` puis `git commit -m "style: <name> appris sur N références"`.
9. **Résumé** (`out/summary.md`, 4-6 lignes pour Mehdi) : les 3 traits marquants du style en mots simples, les chiffres clés (coupes/min, durée du hook), et comment l'utiliser : « écris style <name> dans ton prompt ».

Un style s'améliore avec les retours : quand Mehdi critique un montage fait avec ce style, le skill-keeper modifie `style/<name>/STYLE.md` (pas la skill générale).
