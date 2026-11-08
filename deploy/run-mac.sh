#!/usr/bin/env bash
# Lance le bot sur le Mac et le relance tout seul (après une mise à jour ou un plantage).
# Fenêtre de Terminal ouverte automatiquement à l'ouverture de session (voir install-autostart.sh).
# Ctrl+C dans cette fenêtre arrête le bot. caffeinate empêche la mise en veille tant qu'il tourne.
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
pkill -f "python bot.py" 2>/dev/null && sleep 2   # un seul bot à la fois
trap 'echo; echo "Bot arrêté."; exit 0' INT TERM
cd "$APP_DIR/bot"
while true; do
  set -a; . "$HOME/.video-editors-agents.env"; set +a   # relu à chaque redémarrage (nouvelles clés)
  export REPO_DIR="$APP_DIR" PATH="$APP_DIR/.venv/bin:$HOME/.local/bin:$HOME/.local/node/bin:$HOME/.claude/local:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  echo "$(date '+%H:%M') Bot lancé. Parle-lui sur Telegram, tu peux réduire cette fenêtre."
  caffeinate -i python bot.py
  code=$?
  if [ "$code" -eq 3 ]; then echo "Le bot tourne maintenant sur le VPS : rien à faire sur ce Mac. Tu peux fermer cette fenêtre."; exit 0; fi
  if [ "$code" -eq 0 ]; then echo "Redémarrage après mise à jour…"; sleep 1; else echo "Le bot s'est arrêté (code $code), relance dans 10 s…"; sleep 10; fi
done
