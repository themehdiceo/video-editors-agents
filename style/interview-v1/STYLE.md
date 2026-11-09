# Style interview-v1 : témoignage à 2 personnes (YouTube 16:9)

Appris sur 5 références (ref1 à ref5, voir `refs.txt` et `refs/`). Note de Mehdi : **hook très agressif d'extraits coupés d'avance, PUIS l'interview**.
Mesures : `refs/ref1.json` … `ref5.json`. Détection de plans = changements de scène nets (analyze_refs).

## 1. Structure (identique sur les 5 refs)

| Partie | Durée mesurée | Contenu |
| --- | --- | --- |
| Hook | **22-38 s** (médiane 34 s) | 6-8 extraits de l'interview, enchaînés, avec sous-titres animés. Chaque extrait = 1 phrase-choc avec un chiffre ou une promesse. |
| Écran noir / titre | **1,6-1,9 s** (ref1, ref3, ref5) ; 4,1 s (ref2) ; 6,4 s (ref4 : carte titre animée « Si t'as pas les bonnes fondations / Tu vas pas chiffrer » sur fond noir quadrillé, puis noir) | Séparateur. Son très bas (≈ -36 dB), pas de voix. Place d'un logo/ident. |
| Interview | tout le reste (16-26 min) | Écran partagé 50/50, deux visages côte à côte, **sans sous-titres, sans B-roll, sans coupe**. |

Le hook ne contient JAMAIS l'intro « bonjour, aujourd'hui avec X ». Il commence direct sur une phrase d'un invité (ref1 @0:00 « Ce qui a fait ma réussite… », ref3 @0:00 « Aujourd'hui je suis à une cinquantaine de membres… », ref4 @0:00 « Je chiffrais à 0… »).

### Construction du hook
- Ordre des extraits : **pas chronologique**. Ils sont choisis pour la punch (chiffre, résultat, opinion tranchée : « 25 % instantanément », « 15 000 € par mois », « 50k », « de 10 000 à 20 000 »).
- Alternance des voix : A, B, A, B… (ref1 : 4 changements de locuteur en 38 s). Les 2 personnes apparaissent tôt (avant 8 s).
- Le dernier extrait finit sur une promesse ou une phrase de suspense (ref1 @0:36 « …et c'est ce que je prévois de faire »), puis noir.

## 2. Rythme

- **Hook : 12-14 coupes/min** (ref1 12,7 ; ref2 14 ; ref3 14 ; ref5 12,7 ; ref4 26 = outlier avec carte titre). Plan médian **3,6 s**, p10 2 s, plan le plus long **≈ 7,5 s** (ref1 @8,7-16,0 ; ref5 @12,1-19,8).
- **Interview : 0 coupe.** Un seul plan de 1 233 s à 1 585 s (ref1, ref3, ref4, ref5). Une seule coupe en 18 min sur ref2 (@10:25). Aucun zoom, aucun B-roll.
- Le plan fixe split n'a jamais de limite de durée dans l'interview. Dans le hook, aucun plan > 8 s.
- Pas de pause : les extraits sont coupés serrés (pas de silence > 0,3 s à l'intérieur d'un extrait).

## 3. Look

- **Cadre** : 16:9, 1920×1080. Interview = 2 flux webcam (ou visio) collés **50/50 gauche/droite**, chaque visage cadré à mi-poitrine, centré dans sa moitié. Pas de bordure, pas de séparateur visible (ref1 @244 s, ref4 @165 s, ref5 @446 s).
- **Hook : 3 mises en page qui alternent** : (a) plein écran sur celui qui parle ; (b) split 50/50 ; (c) plein écran sur l'autre. ≈ 20-30 % du hook en split (ref1 : 8 s sur 38).
- **Visage à l'écran : 100 %** du temps. Aucun B-roll, aucune capture, aucune image d'archive dans les 5 refs.
- **Entrées de plan** : coupe sèche. Pas de flou, pas de fondu, pas de zoom mesuré (planches 1re/dernière image identiques à l'échelle près).
- **Sous-titres (hook seulement)** :
  - Police : sans-serif ultra grasse type Montserrat ExtraBold / Black, blanc, contour noir fin + ombre douce.
  - La phrase **se construit mot à mot** (apparition progressive) et reste affichée jusqu'à la fin de la phrase : 2 à 3 lignes, 6 à 10 mots max à l'écran.
  - **1 à 2 mots-clés par phrase** en **jaune** (#FFD400, Mehdi ne veut plus de rouge), **italique gras, 1,5 à 2× plus gros** : chiffres (« 25 % », « €15.000 », « 10k », « 50K »), mots d'intensité (« VRAIMENT », « TOUT », « OBLIGATOIRE »), mots métier (« NICHE », « VSL », « TEAM »). Un mot sensible peut être masqué par `***`.
  - Position : **moitié basse**, collée du côté du locuteur quand l'écran est splité ; en plein écran, bas-gauche ou bas-centre (y ≈ 0,70-0,88). Le texte se déplace légèrement d'une phrase à l'autre (ref2 @0:07 haut, @0:14 milieu).
  - Aucun sous-titre pendant l'interview.
- **Étalonnage** : naturel, non retouché. Luma moyenne 90-140, saturation basse (7-12 sur 255). Pas de LUT, pas de N&B.
- **Titre** (optionnel, ref4) : carte titre sur fond noir quadrillé (grille grise, lueur), texte blanc qui s'écrit mot à mot, un mot en rouge (« fondations », « chiffrer »). Durée 2-2,7 s.

## 4. Son

- Voix : -19 à -27 LUFS dans les refs (non normalisées). **Cible pour nous : -14 LUFS** (règle générale), voix jamais compressée de façon audible.
- Musique : **aucune musique audible** pendant l'interview ni le hook (planches + niveau de voix). Pas de nappe, pas de beat.
- SFX : aucun mesuré. Un son très bas (≈ -36 dB) sous l'écran noir. Ne pas ajouter de whoosh. Règle prudente : si on ajoute un SFX, un seul « hit » doux sur la coupe hook → noir.
- Au changement d'extrait du hook : la voix de l'extrait suivant démarre **sur la coupe**, sans respiration.

## Retours de Mehdi (prioritaires sur tout le reste)

### Structure du hook (méthodes Hormozi et Haynes, validée par Mehdi le 2026-11-08)
Le marché de Mehdi (accompagnement e-commerce) est saturé d'arnaques : le hook doit rassurer le sceptique, pas seulement impressionner.
1. **Callout + promesse** : la cible principale (le salarié) nommée dès la 1re phrase, la situation AVANT puis le résultat (« salarié à 12 000 dh → boutique à X $ »).
2. **Le pire moment** (la peur, le doute) : un témoignage vrai, émotionnel.
3. **Le mécanisme** : pourquoi ça a marché (l'accompagnement, « pilote / copilote »).
4. **La vitesse** (« 4e jour, première vente »).
5. **La preuve à l'écran** (Shopify, chiffres réels) : la preuve vaut plus que la promesse.
6. **La vie d'après** (temps, famille, liberté), pas l'argent, en dernier.
Pour une pub Meta : jamais de promesse de revenus (retirer l'étape 1 chiffrée).

### 2026-11-08 – intro v2 : règles qui remplacent les précédentes en cas de conflit
1. **Coupes logiques** : chaque extrait est une idée complète. Il commence au début d'une phrase (pas au milieu, pas sur « et », « donc », « parce que ») et finit APRÈS la fin de la phrase (ponctuation finale ou silence ≥ 0,3 s, + 0,15 s d'air). Le suspense vient de l'ordre des extraits, jamais d'une phrase coupée. Relis chaque extrait seul : s'il n'a pas de sens sans contexte, change-le.
2. **Durée du hook : 20 à 35 s, idéal ~25 s.** Choisis ce qui rend le mieux dans cette fourchette.
3. **Pas de titres en haut ni de cartes texte** (`titles.py` interdit sauf si Mehdi le demande). Uniquement les sous-titres, qui ont plu : sous-titres sur celui qui parle, phrase qui se construit. Moments choc = simples, sans effet.
4. **Mots-clés en jaune (FFD400), plus jamais en rouge.**
5. **Toux** : `words.json` contient `events` (toux, raclements… repérés par Scribe). Dans le hook, aucun extrait ne contient de toux (coupe avant/après, au silence). Dans l'interview, coupe la toux si elle tombe entre deux phrases ; si elle est au milieu d'une phrase utile, coupe la voix sur la toux avec `"mute": [[début, fin]]` dans plan.json (temps de la vidéo montée, via la timemap).

### 2026-11-08 – intro v1 jugée ratée
1. **Zooms trop serrés** : en plein écran sur une personne, on prend TOUTE sa tuile Meet (tête + épaules visibles, de l'air au-dessus des cheveux, ≥ 8 % de la hauteur). Zoom supplémentaire max ×1,08, et seulement s'il garde la tête entière. Jamais le haut du crâne ou le menton coupés. Vérifie chaque plan sur la planche contact.
2. **Il faut du texte** : sous-titres « phrase qui se construit » sur tout le hook (`subtitles.py --range`). ~~Cartes titles.py~~ : retiré par l'intro v2, Mehdi n'aime pas les titres en haut.
3. **Les bons moments** : le hook = les questions-choc de Mehdi + les réponses les plus fortes d'Anas (chiffres, avant/après, peur, décision de quitter le salariat, preuve Shopify). Format : question de Mehdi (2-3 s) → réponse punch d'Anas, 3 ou 4 fois. Pas de phrases au hasard, pas de réponse hors sujet (ex. à « comment t'as quitté le salariat ? », la réponse doit parler de la décision, pas des chiffres). Relis la transcription avec les locuteurs (`speaker` de Scribe) pour associer chaque question à SA réponse.
4. **Intro d'abord** : quand la note dit « intro seulement », ne rends que le hook (+ 1,8 s de noir), 30-45 s. Pas de rendu de l'interview. Objectif : brouillon livré en moins de 10 min.
5. **Interview (quand Mehdi l'aura validée)** : on coupe les reprises et ratés (« on refait », « attends », « coupe », faux départs, problème technique, longs blancs). Le reste en écran partagé, sans effets.

### 2026-11-08 – intro v3 → v4 (remplace les règles 3 et 4 de la v2 en cas de conflit)
1. **Raccord promesse** : quand Mehdi annonce le sujet (« Anas qui était salarié à 12 000 dh… maintenant 50-60 000 $ »), garde la phrase entière, y compris le lien (« kifach sawbna boutique li ktdkhel haliyan »). Jamais « 12 000 » puis saut direct au « 50 000 ». Vérifie `words.json` mot à mot autour des deux chiffres avant de couper.
2. **Les cartes texte sont revenues** (Mehdi les a gardées, il veut juste mieux) : les questions de Mehdi en bandeau avec **étiquette verte QUESTION + filet vert** (`"label": "QUESTION"` dans la carte, `titles.py`), UNE seule ligne. Pas de carte à 2 lignes avec étiquette (le filet coupe le texte).
3. **Mots-clés en vert émeraude 1FBF6F** (plus de jaune, plus de rouge). Mehdi : « vert pas foncé, vert sombre, stylé ».
4. **Son** : le noir final doit avoir le même nombre de canaux que les extraits (mono), sinon `concat -c copy` casse l'audio de la fin. Contrôle le son sur les 5 dernières secondes.

### 2026-11-08 – intro v5 (intro v4 validée, sauf 2 points)
1. **Le conseil finit sa phrase** : un extrait s'arrête à la fin de la PHRASE de la personne (dernier mot avant un vrai silence / la prise de parole de l'autre), pas à la fin de la première proposition (« …un business » + « حيت… »). Vérifie `words.json` jusqu'au mot suivant l'autre locuteur. Fais un trou de contrôle : relis le dernier mot de chaque extrait, il doit conclure l'idée.
2. **Toux de Mehdi pendant qu'Anas parle** : Scribe ne la note pas toujours dans `events` (ex. 857-858 s : pic d'énergie sans mot). Pour chaque extrait où l'autre personne parle, calcule l'énergie par 0,1 s (wav) et cherche les pics sans mot dans `words.json`. Termine l'extrait avant la toux, ou saute-la avec deux plages, plutôt que de la laisser.
3. **Autocritique obligatoire** (Mehdi, énervé) : avant de livrer, relis chaque correction demandée, vérifie-la sur la planche contact ET sur les mots de fin d'extrait, puis écris dans summary.md « vérifié : … ». Pas de « corrigé » sans preuve.
6. **Mot soufflé inaudible** (2026-11-08, « 9der » à 26,64 s) : un mot de début d'extrait peut être 10-15 dB sous le reste (consonne douce, mot dit bas). Subtitle visible + son absent = Mehdi croit à un bug. Pour le 1er mot de chaque extrait, mesure l'énergie (astats, tranches de 10 ms) sur le rendu ; s'il est > 8 dB sous la phrase, ajoute `"boost": [[début_src, fin_src, dB]]` au shot dans plan.json (géré par `tools/hook_build.py`) et remesure.

## Garde-fous (vérifiables)

1. Hook entre **20 et 35 s**, idéal 25 s (retour de Mehdi, intro v2).
2. Hook ≥ **10 coupes/min** et aucun plan **> 8 s**. (ref1 @8,7 = 7,3 s max)
3. Les **deux** personnes apparaissent avant **10 s** du hook.
4. Alternance A/B : jamais 3 extraits d'affilée de la même personne.
5. **1 à 2 mots-clés jaunes** par phrase de sous-titre ; au moins un **chiffre** en jaune dans les 10 premières secondes quand l'invité en donne un. Jamais de rouge.
6. Écran noir de **1,5 à 2 s** entre hook et interview (4-6 s seulement avec carte titre).
7. Interview : **split 50/50, 0 sous-titre, 0 B-roll, 0 zoom** ; coupes seulement pour enlever reprises, ratés et longs blancs (retour de Mehdi).
10. Plein écran : tête entière visible, zoom ≤ ×1,08 (retour de Mehdi).
11. Hook : sous-titres du début à la fin, **0 carte titre** (sauf demande de Mehdi). Chaque extrait = phrase complète. 0 toux audible.
8. Pas de musique ; voix à **-14 LUFS**.
9. Pas d'image générée, pas de B-roll (aucune dans les refs).

## Ce que l'équipe sait faire / À construire

| Règle | Outil | État |
| --- | --- | --- |
| Hook d'extraits, coupes serrées | `cut.py` + `keep.json` (extraits choisis à la transcription) | OK |
| Plein écran sur A ou sur B (recadrage d'un flux splité) | `compose.py` `vf` (crop) sur les segments | OK, à vérifier au 1er job |
| Split 50/50 pour l'interview | source déjà splitée = `layout: full` sans modification | OK si la source arrive splitée |
| Sous-titres blanc + mots-clés jaunes plus gros, phrase qui se construit | `subtitles.py --style style/interview-v1/style.json --range 0,<fin du hook>` (mode build : phrase cumulée, mots-clés auto ou `"k": true` dans words.json) | OK (ajouté le 2026-11-08) |
| Carte titre sur fond noir quadrillé | motion-designer (HyperFrames) | OK |
| Écran noir 1,8 s | `compose.py` plan noir | OK |
| Interview sans sous-titres | `--range` limite les sous-titres au hook | OK |

## Ce que ces refs ne disent pas
- Les refs ne montrent pas de musique ni de SFX : si Mehdi en veut, il le dira dans le retour.
- La source de l'interview doit arriver avec les 2 flux déjà côte à côte ou 2 fichiers séparés ; si c'est un seul fichier plein cadre sur 1 personne, dire dans le résumé que le split est impossible.

## Leçons apprises (retours de Mehdi)
- **Vie privée à l'écran** : ne jamais montrer le nom de la boutique ni le logo (« BenzSkin », « Benz ») d'un dashboard partagé. Zoom sur la zone des chiffres sous l'en-tête : `"layout": "zoom", "crop": [x,y,w,h]` (pixels source) dans plan.json (`tools/hook_build.py`). Toujours vérifier la planche contact : aucun nom lisible.
- 2026-11-08 (remplace le zoom ci-dessus, préféré par Mehdi) : garder la vue entière (layout "A") et cacher le nom avec une GROSSE carte à bandeau (2 lignes, size ~118, `"y": 0.21` = position verticale libre dans titles.py) qui reste tout le plan. Le téléphone bouge : le nom change de hauteur (50-260 px en 1080p). Vérifier une planche contact de CHAQUE image du plan (fps=3), pas une seule.
- 2026-11-08 (retour Mehdi) : le plan dashboard/preuve ne doit PAS être trop court (« ça fait fake »). Minimum ~5 s, avec le geste du téléphone (« Maintenant c'est bien. Ok. ») avant le chiffre. Le dashboard n'est net que de 623 à 628,8 s dans la source : au-delà il floute puis disparaît. Avant d'allonger un plan écran, sonder la source (1 image/s) pour voir jusqu'où l'écran reste visible. La carte bandeau doit durer exactement le plan.
- **Toux de Mehdi pendant que l'invité parle** : si Scribe ne note pas de mot mais que l'énergie audio sursaute dans un trou de la voix de l'invité, c'est la toux. Finir l'extrait sur la dernière phrase complète avant (silence à l'énergie < 150). Vérifier l'énergie (rms 50 ms) de chaque extrait avant de livrer.

### 2026-11-09 – phrase sans contexte (retour de Mehdi, 00:48)
Anas dit « le 4e jour » mais la coupe tombe avant « … on a fait la première vente » : la phrase ne veut plus rien dire. Règle : un extrait qui annonce quelque chose (« le 4e jour », « ce qui m'a fait changer… ») doit contenir sa réponse. Sinon : prolonger, ou placer la question de Mehdi juste avant, ou un autre passage complet ; et si rien ne marche, poser la question à Mehdi (`out/question.md`) AVANT de monter.
Plus de cuts à l'image dans une même phrase (plein écran de celui qui parle ↔ écran partagé, toutes les 3-5 s, plan ≥ 2 s, son continu), mais pas trop.
