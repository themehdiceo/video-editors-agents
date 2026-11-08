# video-editors-agents

Une équipe d'agents Claude Code qui monte des shorts verticaux (9:16) sur un VPS, pilotée depuis Telegram.

- Tu envoies un **lien** et tu reçois un script : hook, note de potentiel, titres, shot list.
- Tu envoies un **A-roll** (face caméra) et tu reçois le short monté : coupes propres, B-roll, split 50/50, sous-titres, musique, QA.
- Tu envoies une **vidéo longue** avec la légende `clip` (ou `clip 3`) et tu reçois les meilleurs passages en shorts.
- Tu **réponds à un rendu** pour donner un retour : l'équipe fait une nouvelle version et retient la leçon dans ses skills (commit Git, `/annuler` pour revenir en arrière).

## Installation (VPS Ubuntu 22.04 / 24.04, en root)

```bash
git clone https://github.com/themehdiceo/video-editors-agents.git /opt/video-editors-agents
bash /opt/video-editors-agents/deploy/install.sh        # 10 à 20 min
bash /opt/video-editors-agents/deploy/setup-secrets.sh  # saisie masquée des clés
```

Clés demandées par `setup-secrets.sh` (stockées dans `/etc/video-editors-agents/.env`, lisible par root uniquement, jamais dans Git) :

| clé | où la trouver |
| --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | sur ton Mac : `claude setup-token` (utilise ton abonnement Max) |
| `TELEGRAM_BOT_TOKEN` | @BotFather → `/newbot` |
| `TELEGRAM_ALLOWED_USER_ID` | @userinfobot (seul ce compte peut parler au bot) |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | my.telegram.org → API development tools (vidéos jusqu'à 2 Go) |
| `ELEVENLABS_API_KEY` | optionnel : musique générée. Sans clé, le bot pioche dans `assets/music/` |

## Commandes du bot

| commande | effet |
| --- | --- |
| `/script <lien>` ou un lien seul | recherche + script |
| envoi d'une vidéo | montage d'un A-roll |
| vidéo avec la légende `clip 2` ou `/clip <lien youtube> 2` | 2 shorts tirés d'une vidéo longue |
| réponse à un rendu | retour → v2 + mise à jour des skills |
| `/statut` · `/bilan` · `/annuler` | avancement · revue des skills · annule la dernière mise à jour des skills |

## Organisation

```
CLAUDE.md                 chef de production (orchestrateur)
.claude/agents/           chercheur, scenariste, monteur-aroll, documentaliste-broll,
                          motion-designer, inge-son, controle-qualite
.claude/skills/           short-script, short-editor, long-to-short, skill-keeper
.claude/settings.json     liste blanche des commandes autorisées aux agents
style/style.json          le goût de Mehdi (sous-titres, rythme, musique), mis à jour par les retours
tools/                    scripts ffmpeg/whisper testés : transcribe, silences, cut, subtitles, compose, frames, music
bot/                      bot Telegram + file de jobs (un montage à la fois)
deploy/                   install.sh, setup-secrets.sh, services systemd
jobs/                     un dossier par job (ignoré par Git)
```

## Musique libre de droits

Sans ElevenLabs, dépose quelques mp3 libres de droits dans `assets/music/` sur le VPS (par exemple depuis la bibliothèque audio YouTube ou Pixabay Music). Mets l'ambiance dans le nom de fichier, par exemple `energique-tech-01.mp3`.
