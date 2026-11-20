---
name: pixar-ad
description: Créer ou monter une pub Pixar (Profit Partners) - script, scènes générées, montage 9:16 sans clignotement. Utiliser pour tout job dont la note parle de Pixar.
---
# Pub Pixar

## 1. S'alimenter AVANT de commencer (obligatoire, à chaque job)
1. `style/pixar-v1/style.json` : réglages par défaut. Ils priment sur `style/style.json`. Seule la note du job peut les changer.
2. `private/pixar/contexte.md` : offre, cible, preuves autorisées, interdits, darija, pubs déjà validées.
3. `private/pixar/lecons.md` : toutes les validations et tous les refus de Mehdi. Ne refais jamais une erreur qui y figure.
4. Les jobs Pixar précédents : `ls jobs`, puis lis `job.json` et `out/summary.md` de ceux dont la note parle de Pixar. Reprends ce qui a été validé.
Mehdi ne répète pas ses consignes : tout ce qui est dans ces fichiers reste valable.

## 2. Script
- `copywriter-video-editor` écrit hook, scènes et CTA avec le contexte ci-dessus. 40 s max écran compris.
- Une seule raison d'agir par pub. Structure : situation du salarié, déclic, 1re vente en famille, preuve, CTA.

## 3. Scènes
- Même fiche personnage et même seed pour toutes les scènes.
- Une image clé par scène, puis image-to-video. Négatif : flicker, strobe, flashing lights, morphing.
- Mehdi n'est jamais un personnage Pixar : utilise sa vraie vidéo.

## 4. Montage sans clignotement (réglages `anti_flicker`)
- `format.fps` = fps des clips générés (24). Pas de minterpolate.
- Dans plan.json, pour chaque B-roll : `"zoom": 0`, pas de `blur_in`, `"vf": "deflicker=size=5:mode=pm"`.
- `dur` de chaque plan <= durée réelle du clip (ffprobe). Coupes sèches, pas de fondu.

## 5. Contrôle qualité
- `python3 tools/flicker_check.py jobs/<id>/out/final.mp4` : doit afficher 0 clignotement. Sinon, corrige le plan concerné et relance.
- Puis la planche contact (`tools/frames.py`), comme d'habitude.

## 6. Après un retour de Mehdi
- Ajoute 1 ligne datée dans `private/pixar/lecons.md` (validé ou refusé, et pourquoi).
- Si le retour touche un réglage (durée, fps, sous-titres, musique, clignotement), mets à jour `style/pixar-v1/style.json` (skill-keeper, commit `skills:`).
