---
name: long-to-short
description: Extraire d'une vidéo longue (podcast, live, vidéo YouTube) le ou les meilleurs passages de 30-60 s et les monter en shorts 9:16 finis. Utiliser pour tout job de type clip.
---
# Vidéo longue → short

## Étapes
1. **Récupérer** : si c'est un lien, `yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o input/long.mp4 <url>`.
2. **Transcrire** toute la vidéo : `tools/transcribe.py input/long.mp4 work/words_long.json`. Pour plus de 30 min, utilise `--model base` d'abord pour repérer, puis retranscris le passage choisi en `small`.
3. **Choisir le passage** : lis la transcription (segments) et note chaque candidat de 30 à 60 s sur 10 selon :
   - un hook fort dans les 3 premières secondes (affirmation surprenante, question, chiffre) ;
   - une idée complète, compréhensible sans contexte ;
   - une fin nette (chute, punchline, conclusion).
   Écris le classement dans `work/candidates.md`. Garde le meilleur, ou les N meilleurs si `job.json` demande `count`.
4. **Extraire** avec une marge : `ffmpeg -ss <début-1> -to <fin+1> -i input/long.mp4 -c:v libx264 -crf 18 -c:a aac work/clip_raw.mp4`
5. **Monter** ce clip comme un A-roll en suivant la skill `short-editor` (coupes, sous-titres, musique, QA).
   - Si plusieurs personnes parlent : recadre sur la personne qui parle (`crop_x` par plan), ou utilise un split haut/bas.
   - Le B-roll est optionnel ici : le passage doit tenir seul. Ajoute-en seulement si le sujet s'y prête.
6. Livrables : `out/final.mp4` (et `out/clip_2.mp4`… si plusieurs), `out/summary.md` avec le timecode d'origine de chaque clip.

## Leçons apprises
<!-- Le skill-keeper ajoute ici les retours de Mehdi, datés. -->
