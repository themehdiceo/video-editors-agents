# Style vsl-v1 : VSL face caméra de Mehdi (validé « à 2000 % » le 2026-11-16, VSL ebook)

S'applique à toute VSL / vidéo face caméra de Mehdi (note « VSL », « lead magnet », « face caméra avec motion »). Ne pas faire répéter Mehdi : ces règles sont acquises.

## 0. Après validation de l'aperçu final (règle de Mehdi, 2026-11-17)
- Aperçu final validé par Mehdi = tous les aperçus et brouillons de cette vidéo (480p « a valider », v2…vN) vont à la Corbeille, par défaut, sans redemander. Jamais de suppression définitive.
- La finale part sur Bunny. Sur le Mac, garder seulement la finale et les originaux (rushs, voix CapCut, photos) dans ~/Desktop/Profit Partners Capital/09 Sources vidéo brutes.

## 1. Voix et coupes
- Mehdi fait la voix lui-même dans CapCut (« Normaliser le niveau sonore » + « Réduire le bruit », rien d'autre) et envoie un MP3 pleine longueur. On le garde TEL QUEL (pas d'afftdn / de-esser / loudnorm). Recaler par corrélation avec l'audio d'origine, puis couper. (Remplace le défaut « voix nettoyée » pour ce style.)
- Coupes autorisées sans demander : silences, hésitations, ratés/reprises (garder la dernière prise), mots qu'il nomme.
- JAMAIS couper une phrase de contenu sans son OK (même hors script : ça fait sa personnalité). Lister passage + timecode → avis Jeremy + conseil (vault, filtre Maroc) → Mehdi tranche → rendu.
- Lire le script qu'il donne et couper selon ses timecodes exacts ; ne rien oublier de ce qu'il a listé.
- Preuve élève (ex. Anas) : extrait d'origine, brut, avec ses propres sous-titres ; garder le moment où il entre dans Shopify ET où il rapproche la caméra (on voit le chiffre). Valider l'extrait avant de l'insérer.

## 2. Fond
- Garder le fond d'origine (version sans fond IA) sauf demande. Si fond : c'est Mehdi qui détoure dans CapCut.

## 3. Sous-titres
- Darija en lettres latines + français tel qu'il parle (orthographe de son script : 3, 7, 9, kh, ch…). Style interview-v1 : blanc, mots-clés vert 1FBF6F italique, phrase qui se construit mot à mot, **Avenir Next Heavy taille 53**, MarginV 130 sur 1080p (un peu plus haut que le bas, pas trop près du visage).
- Rendu des sous-titres sur le Mac (police système).
- Masquer les sous-titres quand une animation montre déjà ses mots en bas de l'écran.

## 4. Zooms (OBLIGATOIRES, à chaque vidéo)
- Zoom avant / zoom arrière en cut sur les débuts de phrase, toutes les 6 à 9 s ; ×1,08 maximum, crop ancré en haut (tête entière visible). Pas de zoom sur les inserts (preuve élève).

## 5. Animations (motion, skill motion-ppc)
- Cartes BLANCHES, textes NOIRS en gras, police premium Plus Jakarta Sans ExtraBold (800). Jamais de texte fin.
- Vert du logo PPC #D0FE16 seulement en touche (icône, ligne, étiquette avec texte noir dessus). Pas de grande surface verte ni de halo/glow.
- Petites : environ 0,5 à 0,6 de l'écran, sous le menton ou sur les côtés. Elles ne touchent JAMAIS la tête. Vérifier image par image avant d'envoyer.
- Uniquement ses mots exacts, aucun chiffre inventé (enlever les badges par défaut). Pas de motion « doubler ton salaire en 2 h/jour » (promesse de revenu).
- Listes : chaque ligne apparaît quand il la dit (pas de cases vides).
- Placement validé par Jeremy (le master) : là où le spectateur risque de décrocher, jamais 2 animations à moins de 10 s.
- Densité : voir le dernier choix de Mehdi dans learning.md (VSL ebook : 6 trouvé « trop léger » → viser ~1 toutes les 15 s).

## 6. Process
- Une étape validée à la fois : sous-titres → motion → musique (« suspense + joyeuse », 3 choix) → rendu final.
- Aperçus en 480p ; Bunny seulement après son OK ; il nomme la version validée, on supprime les autres.

## Couleur / HDR (validé par Mehdi 2026-11-17, VSL ebook FINAL)
- Les rushs iPhone de Mehdi sont en HDR HLG (bt2020, arib-std-b67). TOUJOURS vérifier `ffprobe color_transfer` et convertir en SDR bt709 AVANT le montage, sinon son visage sort délavé / trop lumineux.
- Filtre validé : `zscale=tin=arib-std-b67:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p`
- Sortie taguée bt709 (`-color_primaries bt709 -color_trc bt709 -colorspace bt709`). Ne pas convertir les inserts déjà SDR. Référence de rendu : son export CapCut.

## Intro / hook (Mehdi 2026-11-17)
- Pas d'intro news/TV sur l'IA devant une VSL lead magnet (ebook) : incohérent avec la pub (conseil Jeremy + Hormozi). La VSL démarre directement sur Mehdi.

## VSL ebook v7 validée par Mehdi (2026-11-17) : réglages à reprendre sur TOUTES les prochaines vidéos
- Intro TV : cette VSL l'a gardée (v5/v6/v7 « avec intro » validées). Elle remplace la règle « pas d'intro TV » quand Mehdi la demande.
- Musique (v6, script `jobs/vsl-ebook-0156/work/reorder/v6/mix.py`) : voix laissée telle quelle (-23,5 LUFS). Musique continue après l'intro : sur la partie forte, départ ≈ 9 LU sous la voix, fondu sur 30 s jusqu'à ≈ 13 LU sous la voix, puis stable. Ducking léger `sidechaincompress=threshold=0.02:ratio=2:attack=30:release=400`. Fondu de sortie 1 s sur le fondu au noir, pas de musique sur l'endcard. Musique trop courte : boucle calée sur le tempo (corrélation), fondu de 1 s. Toujours vérifier par corrélation que la voix n'a pas bougé.
- Slides (v7, script `jobs/vsl-ebook-0156/work/reorder/v7/slides.py`) : écran noir plein cadre #000, la voix continue dessous. Police Plus Jakarta Sans 800 (`assets/fonts/PlusJakartaSans[wght].ttf`). Texte blanc, mots-clés vert #D0FE16, petites pastilles rondes vertes (✓) ou rouges (✗) avec le symbole en noir. Surtitre gris #A3A3A3 en capitales espacées, précédé d'un trait vert. Cartes #0d0d0d, bord #262626, coins arrondis 28 px. « PROFIT PARTNERS CAPITAL » en gris #555, petit, en bas à droite. Chaque élément apparaît sur le mot (glisse de 26 px, 0,32 s, pas de glow). Fondu 0,25 s à l'entrée et à la sortie.
- Motions + slides : garder les DEUX, jamais en même temps (au moins 0,5 s d'écart). Une slide se place dans un trou entre deux motions et se cale sur un début ou une fin de phrase (temps des mots : le .ass des sous-titres).
- Rendu : ne ré-encoder que les morceaux modifiés, découpés aux images clés (segment muxer `-segment_frames`). Recoller en h264 annexb (pas le concat demuxer : il décale d'une image). Le reste est copié. Vérifier par PSNR que l'image est identique au rendu d'avant.
- Photos (v8 validée le 2026-11-17, script `jobs/vsl-ebook-0156/work/reorder/v8/photos.py` + `build_v8.py`) :
  - Produit dont il parle : ses photos (WEBP) sur noir, carte arrondie, surtitre du produit (ex. « PERIOD PAIN RELIEF »), environ 2 s par photo, pile sur la phrase.
  - « Ça a changé ma vie » : diaporama lifestyle (business class, voyages, montre…), environ 0,7 s par photo, la vidéo environ 1,2 s, léger zoom. Plein cadre si la photo est horizontale, sinon carte sur noir.
  - Preuves (Shopify, notif « Money received ») juste après la motion du chiffre, environ 2 s puis 1,5 s, zoom vers le chiffre clé.
  - Captures d'écran : recadrer pour enlever l'interface (Insta, barres, « Next payout », « live visitors »).
  - Ne jamais montrer : alcool, cigarettes, nom « Thaïlande », photo vide sans lui.
  - Toujours au moins 0,5 s d'écart avec les motions.
