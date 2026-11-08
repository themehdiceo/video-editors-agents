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
  - **1 à 2 mots-clés par phrase** en **rouge vif** (≈ #E3173E), **italique gras, 1,5 à 2× plus gros** : chiffres (« 25 % », « €15.000 », « 10k », « 50K »), mots d'intensité (« VRAIMENT », « TOUT », « OBLIGATOIRE »), mots métier (« NICHE », « VSL », « TEAM »). Un mot sensible peut être masqué par `***`.
  - Position : **moitié basse**, collée du côté du locuteur quand l'écran est splité ; en plein écran, bas-gauche ou bas-centre (y ≈ 0,70-0,88). Le texte se déplace légèrement d'une phrase à l'autre (ref2 @0:07 haut, @0:14 milieu).
  - Aucun sous-titre pendant l'interview.
- **Étalonnage** : naturel, non retouché. Luma moyenne 90-140, saturation basse (7-12 sur 255). Pas de LUT, pas de N&B.
- **Titre** (optionnel, ref4) : carte titre sur fond noir quadrillé (grille grise, lueur), texte blanc qui s'écrit mot à mot, un mot en rouge (« fondations », « chiffrer »). Durée 2-2,7 s.

## 4. Son

- Voix : -19 à -27 LUFS dans les refs (non normalisées). **Cible pour nous : -14 LUFS** (règle générale), voix jamais compressée de façon audible.
- Musique : **aucune musique audible** pendant l'interview ni le hook (planches + niveau de voix). Pas de nappe, pas de beat.
- SFX : aucun mesuré. Un son très bas (≈ -36 dB) sous l'écran noir. Ne pas ajouter de whoosh. Règle prudente : si on ajoute un SFX, un seul « hit » doux sur la coupe hook → noir.
- Au changement d'extrait du hook : la voix de l'extrait suivant démarre **sur la coupe**, sans respiration.

## Garde-fous (vérifiables)

1. Hook entre **20 et 40 s**, jamais plus. (ref1-5 : 22-38 s)
2. Hook ≥ **10 coupes/min** et aucun plan **> 8 s**. (ref1 @8,7 = 7,3 s max)
3. Les **deux** personnes apparaissent avant **10 s** du hook.
4. Alternance A/B : jamais 3 extraits d'affilée de la même personne.
5. **1 à 2 mots rouges** par phrase de sous-titre ; au moins un **chiffre** rouge dans les 10 premières secondes quand l'invité en donne un.
6. Écran noir de **1,5 à 2 s** entre hook et interview (4-6 s seulement avec carte titre).
7. Interview : **split 50/50, 0 coupe, 0 sous-titre, 0 B-roll, 0 zoom**.
8. Pas de musique ; voix à **-14 LUFS**.
9. Pas d'image générée, pas de B-roll (aucune dans les refs).

## Ce que l'équipe sait faire / À construire

| Règle | Outil | État |
| --- | --- | --- |
| Hook d'extraits, coupes serrées | `cut.py` + `keep.json` (extraits choisis à la transcription) | OK |
| Plein écran sur A ou sur B (recadrage d'un flux splité) | `compose.py` `vf` (crop) sur les segments | OK, à vérifier au 1er job |
| Split 50/50 pour l'interview | source déjà splitée = `layout: full` sans modification | OK si la source arrive splitée |
| Sous-titres blanc + mots-clés rouges plus gros, phrase qui se construit | `subtitles.py --style style/interview-v1/style.json --range 0,<fin du hook>` (mode build : phrase cumulée, mots-clés auto ou `"k": true` dans words.json) | OK (ajouté le 2026-11-08) |
| Carte titre sur fond noir quadrillé | motion-designer (HyperFrames) | OK |
| Écran noir 1,8 s | `compose.py` plan noir | OK |
| Interview sans sous-titres | `--range` limite les sous-titres au hook | OK |

## Ce que ces refs ne disent pas
- Les refs ne montrent pas de musique ni de SFX : si Mehdi en veut, il le dira dans le retour.
- La source de l'interview doit arriver avec les 2 flux déjà côte à côte ou 2 fichiers séparés ; si c'est un seul fichier plein cadre sur 1 personne, dire dans le résumé que le split est impossible.
