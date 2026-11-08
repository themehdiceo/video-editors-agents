---
name: edit-plan
description: Préparer le plan de montage qu'ouvre Mehdi avant le montage - coupes, script ligne par ligne et 4 idées de scène par ligne. Utiliser pour tout job edit en phase plan.
---
# Plan de montage (phase plan)

Principe : c'est Mehdi qui décide du montage, l'équipe exécute. Un montage où l'IA devine tout fait « monté par une IA ».
Tu ne montes PAS la vidéo dans cette phase. Tu prépares le terrain et tu proposes.

Lis `style/style.json` et la note de Mehdi dans job.json (elle prime).

## Étapes (une ligne dans progress.log par étape)
1. **Préparer** : `ffprobe` la source. `work/words.json` existe déjà (transcription faite par le bot).
2. **Silences** : `python3 tools/silences.py <source> work/silences.json`.
3. **Sélection** → agent `monteur-aroll` : choisit les passages qui répondent à la note (durée demandée, phrases citées) et écrit `work/keep.json`. Pas encore de rendu final, mais fais `work/aroll_cut.mp4` (cut.py) pour vérifier.
4. **Regarder** : planche contact de la source autour des passages retenus (`tools/frames.py --at …`). Note ce qui est à l'écran (qui parle, écran partagé, téléphone, chiffres).
5. **Écrire `out/plan.md`** (format ci-dessous), puis `work/plan_options.json` avec les mêmes données (`[{"n", "src_start", "src_end", "text", "options": {"A": "...", ...}, "reco": "B"}]`).
6. **Résumé** dans `out/summary.md` : 2 à 4 lignes (durée du montage prévu, doutes sur la transcription).

## Format de `out/plan.md` (lu sur Telegram : court, sans tableau)
```
🎬 PLAN – <titre court> (≈ 38 s)

1. [0:00–0:04] « Ana kont salarié b 12 000 dh f chher »
A) Plein écran Anas + titre animé « 12 000 DH/MOIS »
B) Compteur qui monte 12 000 DH → 60 000 $ ⭐
C) Texte plein écran blanc sur noir
D) Zoom lent sur Anas, rien d'autre

2. …

Réponds à ce message avec tes choix : « 1B 2A 3C… », une idée à toi (« 4 : zoom sur le téléphone »), ou « ok » pour prendre les ⭐.
```
- Une ligne de script = une scène de 2 à 6 s. 6 à 15 scènes pour une intro ou un short.
- Texte en darija latine (comme Mehdi l'écrit), avec le timecode du passage dans la source.
- 4 options par scène, toutes réalisables par l'équipe, adaptées à ce qui est dit. Mets ⭐ sur ta recommandation.

## Catalogue d'idées de scène (ce que l'équipe sait faire)
- **Cadrage** : plein écran sur celui qui parle (recadrage Meet), zoom lent ou punch-in, split des deux personnes, écran partagé en plein cadre avec zoom sur la zone utile.
- **Titres** : titre animé (chiffre ou mot clé), sous-titre mis en avant, texte plein écran contrasté, nom + rôle (lower third).
- **Chiffres** : compteur qui monte, avant/après (gauche → droite avec flèche), graphique qui monte.
- **UI façon logiciel** : notification type Shopify/Stripe qui glisse (« Nouvelle vente 1 240 $ »), carte de chapitre numérotée, liste qui apparaît élément par élément.
- **Preuve** : capture d'écran du téléphone ou du dashboard en plein cadre, zoom et surlignage du chiffre.
- **Rupture** : désaturation + écho sur une phrase forte, coupe sèche sur noir, silence + texte.
- **B-roll** : image d'illustration (bureau, salarié, colis, argent) si rien n'est montrable.
