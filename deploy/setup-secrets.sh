#!/usr/bin/env bash
# Saisie des clés, en masqué. Rien ne s'affiche, rien ne part sur Internet ni dans Git.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Lance ce script en root."; exit 1; }
ENV=/etc/video-editors-agents/.env
mkdir -p "$(dirname $ENV)"; touch $ENV; chmod 600 $ENV

# Clés recopiées du Mac (fichier passé en argument) : on ne redemande que ce qui manque.
IMPORT=0
if [ -n "${1:-}" ] && [ -f "$1" ]; then
  for k in CLAUDE_CODE_OAUTH_TOKEN TELEGRAM_BOT_TOKEN TELEGRAM_ALLOWED_USER_ID ELEVENLABS_API_KEY PEXELS_API_KEY \
           TELEGRAM_API_ID TELEGRAM_API_HASH SCRIBE_MODEL WHISPER_LANG; do
    v=$(grep -E "^$k=" "$1" | tail -1 | cut -d= -f2- | tr -d '\r' || true)
    [ -n "$v" ] && { sed -i "/^$k=/d" $ENV; echo "$k=$v" >> $ENV; }
  done
  shred -u "$1" 2>/dev/null || rm -f "$1"
  IMPORT=1; echo "Clés du Mac recopiées."
fi

ask() { # nom, explication, secret(1/0)
  local cur; cur=$(grep -E "^$1=" $ENV | cut -d= -f2- || true)
  [ "$IMPORT" = 1 ] && [ -n "$cur" ] && return
  echo; echo "$2"
  [ -n "$cur" ] && echo "(déjà défini : Entrée pour garder)"
  if [ "$3" = 1 ]; then read -rsp "$1 = " v; echo; else read -rp "$1 = " v; fi
  [ -z "$v" ] && v=$cur
  sed -i "/^$1=/d" $ENV; [ -n "$v" ] && echo "$1=$v" >> $ENV
}

ask CLAUDE_CODE_OAUTH_TOKEN "Jeton Claude : sur ton Mac, lance 'claude setup-token' et colle le jeton (sk-ant-oat…)." 1
ask TELEGRAM_BOT_TOKEN "Jeton du bot : crée-le avec @BotFather sur Telegram (/newbot)." 1
ask TELEGRAM_ALLOWED_USER_ID "Ton identifiant Telegram (chiffres) : envoie un message à @userinfobot." 0
ask TELEGRAM_API_ID "api_id Telegram (my.telegram.org > API development tools), pour envoyer des vidéos jusqu'à 2 Go." 0
ask TELEGRAM_API_HASH "api_hash Telegram (même page)." 1
ask ELEVENLABS_API_KEY "Clé ElevenLabs (optionnel, Entrée pour passer)." 1

grep -q '^TELEGRAM_API_ID=' $ENV && ! grep -q '^TELEGRAM_API_URL=' $ENV && \
  echo "TELEGRAM_API_URL=http://127.0.0.1:8081/bot" >> $ENV
grep -q '^WHISPER_MODEL=' $ENV || echo "WHISPER_MODEL=large-v3-turbo" >> $ENV
grep -q '^WHISPER_LANG=' $ENV || echo "WHISPER_LANG=fr" >> $ENV

echo; echo "Clés enregistrées dans $ENV (lisible par root uniquement)."
if grep -q '^TELEGRAM_API_ID=' $ENV; then
  # Passage du serveur Telegram officiel au serveur local (vidéos de 2 Go) : à faire une seule fois.
  # Ça déconnecte aussi le bot du Mac, qui s'arrête tout seul.
  if [ ! -f /var/lib/telegram-bot-api/.logout-done ]; then
    T=$(grep -E '^TELEGRAM_BOT_TOKEN=' $ENV | cut -d= -f2-)
    curl -fsS -o /dev/null "https://api.telegram.org/bot$T/logOut" && touch /var/lib/telegram-bot-api/.logout-done || true
  fi
  systemctl enable --now telegram-bot-api
  sleep 5
fi
systemctl enable --now video-bot
sleep 3; systemctl --no-pager status video-bot | head -5
echo; echo "C'est fini. Dans 1 à 2 minutes, le bot du Mac s'arrête tout seul et le VPS prend le relais."
echo "Envoie /aide à ton bot sur Telegram pour tester. Tu peux fermer cette fenêtre."
