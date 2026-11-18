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
- Coupes posées sur la FORME D'ONDE (énergie bande voix 250-3500 Hz) : on ne coupe que dans le silence. Vérif auto : aucune borne de passage sur de la voix.
- Transcription : Scribe fusionne les reprises (« w 99%… w 99% » écrit une fois). Donc après chaque découpe, faire RÉÉCOUTER le montage par Gemini (`templates/faq/gemini_check.py`, accord de Mehdi le 2026-11-18) : reprises, souffles, mots rognés. Gemini dit QUOI couper, jamais OÙ (ses minutages sont faux à ±0,5 s) : poser chaque borne dans le silence voisin, puis revérifier sur un extrait court. Livrer seulement quand Gemini ne trouve plus rien de réel.
- Rushs HDR : convertir UNE fois la source en SDR (`source_sdr.mp4`, h264_videotoolbox 30M, ~10 min pour 19 min), puis toutes les découpes partent de cette copie (6 min au lieu de 30).

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
- Modèle HyperFrames : `templates/hyperframes-cards/index.html` (copie de jobs/img0151). Jamais de promesse de résultat à l'écran : écrire « objectif ».

### 5 bis. Version longue (FAQ / objections, ~8 min) — validée par Mehdi le 2026-11-18 (« très parfait, pour toutes les futures vidéos »)
Modèles rejouables : `templates/faq/` (Python + Pillow, rendu qtrle avec alpha posé par compose.py `overlays`). Ordre : build_keep → cut → build_plan → build_sub_words → subtitles → words_dst → motion_times → motions_render → slides_render → compose → mix_lu.
- **Liste des motions : Jeremy la choisit** (agent jeremy-haynes, avec le script minuté) ; Mehdi valide le nombre (QCM 28 / 22 / titres seuls). FAQ de 8 min = 28 motions, ~1 toutes les 17-19 s.
  - Les questions deviennent des titres de chapitre (pastille verte « QUESTION n »). Les calculs s'écrivent ligne par ligne, chaque ligne sur son mot.
  - Rien sur les histoires émotionnelles (parents, peur) : visage seul. Rien qui ressemble à une promesse : jamais « 10 fois plus riche », « des millions ». Quand il parle d'argent, le dire en clair (« Kifach ddkhel lflous w nta f l'Maghrib ? »), jamais un titre flou.
- **Cartes motion** (style vsl-v1) : carte blanche arrondie, texte noir Plus Jakarta Sans 800 (46 px, 54 px pour un titre seul), surtitre en pastille verte #D0FE16, largeur max 640 px, côté OPPOSÉ au visage (vérifier sur une planche des 28 instants), glisse 26 px + fondu 0,3 s, ligne suivante 0,32 s sur son mot. Insécables avant « ? : % $ » et dans « 1 000 » (jamais un « ? » seul sur une ligne). Au moins 10 s entre deux débuts de motion.
- **Écrans noirs animés** (slides VSL v7) sur les passages techniques ET dans les creux sans motion : 12 pour 8 min, 5-17 s chacun, sous-titres masqués pendant l'écran, jamais à moins de 0,5 s d'une motion. Texte = ses mots raccourcis, mots-clés verts.
- Spécifications par vidéo : `motions_spec.json` / `slides_spec.json` (texte + mot déclencheur, temps SOURCE pour survivre aux re-découpes).
- Sous-titres : chaque mot reste dans UN passage gardé (sinon il disparaît aux coupes) : `build_sub_words.py` le garantit, vérifier « N mots = N événements ».

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
