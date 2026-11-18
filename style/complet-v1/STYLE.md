# Style « montage complet v1 » (complet-v1) — validé à 100 % par Mehdi le 2026-11-18 (IMG_0151)

Déclencheur : la note de Mehdi dit **« montage complet v1 »** (ou « montage complet »). Tout ce qui suit s'applique sans lui demander.
Modèles rejouables : `jobs/img0151/work/build.py` (face caméra), `jobs/img0151b/work/build.py` (partage d'écran).

## 1. Source
- Regarder 1 image avant tout : un .MOV 1080x1920 avec rotation -90 est un VRAI 16:9 (pas de fond flouté).
- HDR HLG → SDR bt709 avec le filtre de vsl-v1. Format YouTube 16:9.
- Transcription ElevenLabs Scribe (jamais Whisper).

## 2. Coupes
- Seulement silences, prises ratées (garder la dernière), toux, « uh ». Jamais de contenu sans son accord.
- Pauses > 0,35 s coupées, marges 0,08 s avant / 0,12 s après la voix (jamais dans un mot).
- Partage d'écran : couper aussi les longs silences de navigation. Finir sur la preuve (ex. Shopify) et pas sur un raté.

## 3. Sous-titres
- Darija en lettres latines, orthographe de son script, texte réécrit à la main par bloc et calé sur les mots Scribe.
- Avenir Next Heavy, blanc, mots-clés verts 1FBF6F en italique, la phrase se construit (style interview-v1).
- Partage d'écran : petits (36), dans la bande libre en bas, à gauche de la bulle caméra.

## 4. Zooms
- Zoom ×1,08 sur un raccord, au moins toutes les 6 s (alternance 1,0 / 1,08). Pas de zoom ajouté sur un partage d'écran qui a déjà ses zooms.

## 5. Motion (HyperFrames, `npx -y hyperframes@0.9.22`, calque webm transparent posé dans build.py)
- **Cartes à côté de la tête** : 3 à 5, à droite du visage (left 1210 px), bandeau sombre, barre verte, ligne 1 blanche et ligne 2 verte en italique, entrée glissée avec rebond, mots en cascade. Calées sur le mot.
- **Écrans noirs animés** (sa tête disparaît, la voix et les sous-titres continuent) : demander à Jeremy où les placer. Il en faut 2 à 4, sur des phrases entières, 10 s max chacun, 40 % max de la vidéo.
  - Garder le visage sur l'accueil, la confiance (contrat) et les « rkz m3aya ».
  - Chaque animation est un vrai schéma calé sur les mots : barres, grille 100 → 5, frise J1-J7, deux chemins mauvais/bon.
- Modèle : `jobs/img0151/work/hf/cards/index.html`. Jamais de promesse de résultat à l'écran : écrire « objectif ».

## 6. Musique
- Lui proposer 5 variations, en extraits de 10 s mixés sous sa voix, sauf s'il donne un morceau.
- Tonalité sur la note de sa voix, tempo de 90 à 98 BPM, pas de mélodie lead.
- Couper l'intro presque muette du morceau.
- Musique plus courte que la vidéo : la boucler SANS sa fin qui baisse. Couper juste avant la baisse de fin (Solitude M83, version from16 : à 182 s), puis enchaîner en fondu de 2 s sur le début déjà sans intro muette. Vérifier l'enveloppe : aucun creux aux raccords, la musique tourne jusqu'à la dernière seconde (Mehdi, 2026-11-18, FAQ).
- Niveau : mesurer la voix en LUFS, mettre la musique 12 à 14 dB dessous, ducking léger (`jobs/img0151/work/mix_lu.py --start 12 --end 14`). Voix jamais retouchée.

## 7. Données privées
- Partage d'écran : flouter le nom de la boutique, l'URL, les badges de commandes, les chiffres de conversion, la ligne des commandes et des litiges, et les apps privées. Le flou suit les zooms (`jobs/img0151b/work/shop_blur.py`).
- Garder le CA du jour (la preuve).

## 8. Livraison
- Aperçu 480p « A VALIDER » dans Téléchargements, puis finale **1080p** (pas de 4K) sur Bunny Stream.
- Ensuite : aperçus à la Corbeille, finale et originaux dans « 09 Sources vidéo brutes ».
