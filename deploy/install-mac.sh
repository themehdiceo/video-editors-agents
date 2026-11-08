#!/usr/bin/env bash
# Installation sur Mac (Apple Silicon ou Intel). À lancer dans le Terminal, sans sudo :
#   git clone https://github.com/themehdiceo/video-editors-agents.git ~/video-editors-agents
#   bash ~/video-editors-agents/deploy/install-mac.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV="$HOME/.video-editors-agents.env"

if ! command -v brew >/dev/null; then
  echo "==> Installation de Homebrew (mot de passe du Mac demandé)"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
fi

echo "==> Outils : ffmpeg, Python, Node, yt-dlp"
brew install ffmpeg node yt-dlp
# Python via uv : version précompilée, pas de compilation (rapide même sur un macOS ancien)
command -v uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }
command -v claude >/dev/null || npm install -g @anthropic-ai/claude-code

echo "==> Environnement Python"
uv venv --python 3.12 "$APP_DIR/.venv"
VIRTUAL_ENV="$APP_DIR/.venv" uv pip install -q -r "$APP_DIR/requirements.txt"

echo "==> Police Montserrat"
for w in ExtraBold Bold Black; do
  curl -fsSL -o "$APP_DIR/assets/fonts/Montserrat-$w.ttf" \
    "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-$w.ttf" || true
done
cp "$APP_DIR"/assets/fonts/*.ttf "$HOME/Library/Fonts/" 2>/dev/null || true

echo "==> Modèle Whisper"
"$APP_DIR/.venv/bin/python" -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

echo "==> Clés (saisie masquée, stockées dans $ENV, jamais dans Git)"
touch "$ENV"; chmod 600 "$ENV"
ask() {
  grep -q "^$1=" "$ENV" && { echo "$1 déjà défini."; return; }
  echo; echo "$2"
  if [ "$3" = 1 ]; then read -rsp "$1 = " v; echo; else read -rp "$1 = " v; fi
  [ -n "$v" ] && echo "$1=$v" >> "$ENV"
}
if ! claude auth status >/dev/null 2>&1; then
  ask CLAUDE_CODE_OAUTH_TOKEN "Jeton Claude : dans un autre onglet du Terminal, lance 'claude setup-token' et colle le jeton." 1
fi
ask TELEGRAM_BOT_TOKEN "Jeton du bot donné par @BotFather." 1
ask TELEGRAM_ALLOWED_USER_ID "Ton identifiant Telegram (chiffres, via @userinfobot)." 0
ask ELEVENLABS_API_KEY "Clé ElevenLabs (optionnel, Entrée pour passer)." 1
grep -q '^WHISPER_LANG=' "$ENV" || echo "WHISPER_LANG=fr" >> "$ENV"

echo
echo "Installation terminée. Pour lancer le bot :  bash $APP_DIR/deploy/run-mac.sh"
