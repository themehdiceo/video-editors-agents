#!/usr/bin/env bash
# Lance le bot sur le Mac. Laisse cette fenêtre de Terminal ouverte (Ctrl+C pour arrêter).
# caffeinate empêche le Mac de se mettre en veille tant que le bot tourne.
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
set -a; . "$HOME/.video-editors-agents.env"; set +a
export REPO_DIR="$APP_DIR" PATH="$APP_DIR/.venv/bin:$PATH"
cd "$APP_DIR/bot"
echo "Bot lancé. Écris /aide à ton bot sur Telegram."
exec caffeinate -i python bot.py
