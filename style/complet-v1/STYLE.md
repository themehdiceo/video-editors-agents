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

## Médias perso de Mehdi (B-roll vie, voyage, preuves) — règle du 18/11
- Tu PEUX voir ses photos et vidéos : ouvre-les et regarde-les (planche contact avec Pillow + ImageOps.exif_transpose, ou sips pour les HEIC, puis Read de l'image). Ne dis JAMAIS « je ne trouve pas » avant d'avoir regardé TOUS ses dossiers.
- Où : ~/Desktop/Mes photos/ (Business class, Lifestyle (Rolex = IMG_0020.jpg), Villas et piscines, Voyages, Captures preuves). Interview Anas brute (Meet, 20 min) : disque Sandisk « Profit Partners Capital Data/03 Témoignages/Originaux/Interview Anas brut/ ».
- Vie de rêve / voyage : SES médias en priorité, jamais du stock (Mixkit) ni un avion sans contexte. Défilé rapide de plusieurs photos (~1 s chacune), chaque lieu montré UNE fois (business class une seule fois).
- Défilé photos (Mehdi 19/11) : FOND NOIR, chaque photo dans son format, en petit (h 760 max, pas d'agrandissement), glissement façon film + clic d'appareil photo à chaque photo, ~1,5-2 s chacune (le temps de voir la Rolex). Vidéo business class accélérée (×2,5) pour montrer toute la suite. Modèle : jobs/case23m/work/slideshow.py.
- Appel avec Anas : montrer le moment exact demandé (ex. « t9der t9erreb l caméra » à 620 s, il approche son téléphone avec ses chiffres), même durée que la phrase, code Meet recadré.

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

### 5 ter. Animations explicatives (validé « à 2000 % » par Mehdi le 2026-11-18, FAQ v8) — préférées aux cartes motion
- Sur un concept, une métaphore ou un calcul : un VRAI petit film schématique plein écran, calé mot à mot sur sa voix (pas une carte texte). Ex. : `jobs/20261118-062812-edit/work/mountain_render.py` (grimpeur bute sur « 3A9BA = l'identité l9dima », passe, coche « lflous », « l'business », drapeau « FORSA ») et `calc_render.py` (calcul).
- Python + Pillow, coût 0 €, style des slides (noir, Plus Jakarta Sans 800, vert #D0FE16, gris, rouge #FF6B6B pour ce qu'on enlève). Rendu 2x puis réduit pour les formes. Sous-titres masqués pendant l'écran.
- Calcul pour débutant : UNE idée par scène, l'une après l'autre (ticket « Prix − frais = rbe7 », puis « objectif ÷ rbe7 = nombre de ventes » avec les colis, puis la comparaison). Jamais deux colonnes chargées d'un coup (« pas clair », Mehdi). Version « pièces qui s'envolent vers camion/mégaphone » testée : Mehdi préfère le ticket (v8b).
- Jeremy choisit les passages ; ~8 par FAQ de 8 min. Compter TOUS les écrans pleins (anciennes slides comprises) : v9 = 47 %, au-dessus des 35 % visés, à arbitrer avec Mehdi. Jamais deux écrans pleins bout à bout : raccourcir l'ancien pour laisser ≥ 2 s de visage (sous-titres remis sur ce trou).
- Quand il dit « f akfes l7alat », l'écrire à l'écran : pastille « F AKFES L7ALAT (le pire des cas) » (Mehdi, 2026-11-18). Vérifier que deux « pires cas » de la même vidéo ne se contredisent pas (sinon : Jeremy, puis Mehdi).
- Modèles validés « parfait » (FAQ v9, 2026-11-18) : `templates/anim/` (mountain_render.py, calc_render.py, anim5_render.py : budget, angles, pire cas en ticket, enchère Facebook, circuit de l'argent Maroc → US → Maroc). Le ticket « Prix − frais = Rbe7 » est le format préféré pour tout calcul.
- Vraies personnes (voyage, vie de rêve) : B-roll Mixkit (gratuit, sans crédit, `assets.mixkit.co/videos/<id>/<id>-720.mp4`), sous-titres gardés dessus.

## 6. Musique
- Lui proposer 5 variations, en extraits de 10 s mixés sous sa voix, sauf s'il donne un morceau.
- Tonalité sur la note de sa voix, tempo de 90 à 98 BPM, pas de mélodie lead.
- Couper l'intro presque muette du morceau.
- Musique plus courte que la vidéo : la boucler SANS sa fin qui baisse. Couper juste avant la baisse de fin (Solitude M83, version from16 : à 182 s), puis enchaîner en fondu de 2 s sur le début déjà sans intro muette. Vérifier l'enveloppe : aucun creux aux raccords, la musique tourne jusqu'à la dernière seconde (Mehdi, 2026-11-18, FAQ).
- Niveau : mesurer la voix en LUFS, mettre la musique 12 à 14 dB dessous, ducking léger (`jobs/img0151/work/mix_lu.py --start 12 --end 14`). Voix jamais retouchée.
- Voix faible (micro fixe du Mac, ~-21 LUFS) : `--start 12 --end 14` donne en réalité ~20 dB d'écart (ducking compris) et Mehdi la trouve TROP FORTE (case study 2,3M, 2026-11-19). Utiliser `--start 20 --end 20` (≈ 26 dB d'écart moyen mesuré, musique −6 dB). Vérifier l'écart réel : mix − voix, par fenêtres de 20 s.

## 7. Données privées
- Partage d'écran : flouter le nom de la boutique, l'URL, les badges de commandes, les chiffres de conversion, la ligne des commandes et des litiges, et les apps privées. Le flou suit les zooms (`jobs/img0151b/work/shop_blur.py`).
- Garder le CA du jour (la preuve).

## 7 bis. Vitesse (Mehdi, 2026-11-18 : « sois plus rapide, plus smart »)
- Découpe vidéo : TOUJOURS `tools/cut.py ... --hw` (chaque passage lu seul avec -ss, encodeur du Mac, 6 en parallèle, son collé d'un bloc). L'ancien chemin sans `--hw` met chaque passage en mémoire : 16 à 33 min sur une FAQ.
- Relecture Gemini : `tools/cut.py work/audio.opus work/keep.json work/cut_audio.opus --audio-only` (9 s au lieu de 5 min), puis `gemini_check.py`. Ne redécouper la vidéo qu'une fois les coupes finies.
- Plan (passages + motions + animations) validé par Mehdi AVANT de monter, et une fiche par vidéo : vise 3-4 versions, pas 9.
- Animations : partir des modèles `templates/anim/`, les rendre en parallèle (plusieurs agents motion-designer) pendant la découpe.
- Petit correctif : lui envoyer une capture ou un extrait de 10 s, pas toute la vidéo. Envoi Bunny seulement pour la version validée.

## 8. Livraison
- Aperçu 480p « A VALIDER » dans Téléchargements, puis finale **1080p** (pas de 4K) sur Bunny Stream.
- Ensuite : aperçus à la Corbeille, finale et originaux dans « 09 Sources vidéo brutes ».

## Pubs courtes et animations (Mehdi, 2026-11-20)
- « Animations » = petits films de PERSONNAGES qui bougent (style montagne / grimpeur validé), pas des slides de texte. Modèles 9:16 : style/complet-v1/templates/ads9/anim9.py (copie de jobs/anti-guru-ads/work) (gourou qui vend la formation puis laisse le gars seul, deal qui monte ensemble + win-win, balance lflous/lwe9t, panneaux contradictoires, train « lfourssa » qui part).
- Pub de 30-45 s : 2 à 3 écrans pleins de ~3-4 s chacun, pas plus (jamais un écran de 6 s). Entre eux : cartes motion SUR sa tête (le visage reste, des éléments apparaissent). Un élément visuel toutes les 10-15 s.
- Quand il parle de son argent ou de sa vie (« 10 d lmlyon », « 20 3am », « millionnaire ») : défilé de SES photos (Rolex, business class, piscine, coucher de soleil), ~1-1,3 s par photo, clic photo (photos9.py). Ne jamais laisser ce moment avec juste sa tête.
- Rush avec musique déjà dedans : ne rien ajouter sous la voix ; rap joyeux en outro sous l écran de fin seulement. Toujours laisser finir « ntla9aw f jiha lokhra ».
