#!/usr/bin/env bash
# Installation sur Mac, SANS Homebrew : uniquement des binaires précompilés,
# donc rapide même sur un macOS ancien (rien n'est compilé).
#   git clone https://github.com/themehdiceo/video-editors-agents.git ~/video-editors-agents
#   bash ~/video-editors-agents/deploy/install-mac.sh
set -euo pipefail
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV="$HOME/.video-editors-agents.env"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"
export PATH="$BIN:$HOME/.local/node/bin:$PATH"
ARCH=$(uname -m)   # arm64 (Apple Silicon) ou x86_64 (Intel)
echo "==> macOS $(sw_vers -productVersion), $ARCH"

fetch_zip() { # url, binaire attendu
  local tmp; tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/x.zip" "$1" && unzip -qo "$tmp/x.zip" -d "$tmp" && \
    mv "$(find "$tmp" -type f -name "$2" | head -1)" "$BIN/$2" && chmod +x "$BIN/$2" && \
    xattr -d com.apple.quarantine "$BIN/$2" 2>/dev/null; rm -rf "$tmp"
  "$BIN/$2" -version >/dev/null 2>&1
}

echo "==> ffmpeg + ffprobe (binaires statiques)"
for tool in ffmpeg ffprobe; do
  if "$BIN/$tool" -version >/dev/null 2>&1; then continue; fi
  A=$([ "$ARCH" = arm64 ] && echo arm64 || echo amd64)
  fetch_zip "https://ffmpeg.martin-riedl.de/redirect/latest/macos/$A/release/$tool.zip" $tool \
    || fetch_zip "https://evermeet.cx/ffmpeg/getrelease/$tool/zip" $tool \
    || { echo "(!) Impossible de télécharger $tool. Envoie cette erreur à Claude."; exit 1; }
done
"$BIN/ffmpeg" -hide_banner -filters 2>/dev/null | grep -q " subtitles " || echo "(!) ffmpeg sans sous-titres (libass) : préviens Claude."

echo "==> Node.js 22 (pour HyperFrames, optionnel)"
if ! command -v node >/dev/null; then
  N=$(curl -fsSL https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt | grep -o "node-v[0-9.]*-darwin-$( [ "$ARCH" = arm64 ] && echo arm64 || echo x64).tar.gz" | head -1)
  mkdir -p "$HOME/.local/node"
  curl -fsSL "https://nodejs.org/dist/latest-v22.x/$N" | tar xz -C "$HOME/.local/node" --strip-components 1 \
    || echo "(!) Node non installé : les animations HyperFrames seront indisponibles."
fi

echo "==> Claude Code"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
export PATH="$HOME/.local/bin:$HOME/.claude/local:$PATH"

echo "==> Python 3.12 (uv, précompilé) + dépendances (Whisper, Telegram, yt-dlp)"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv --allow-existing --python 3.12 "$APP_DIR/.venv"
VIRTUAL_ENV="$APP_DIR/.venv" uv pip install -q -r "$APP_DIR/requirements.txt"

echo "==> Police Montserrat"
for w in ExtraBold Bold Black; do
  curl -fsSL -o "$APP_DIR/assets/fonts/Montserrat-$w.ttf" \
    "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-$w.ttf" || true
done
cp "$APP_DIR"/assets/fonts/*.ttf "$HOME/Library/Fonts/" 2>/dev/null || true

echo "==> Modèle Whisper (téléchargement unique)"
"$APP_DIR/.venv/bin/python" -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

echo "==> Clés (saisie masquée, stockées dans $ENV, jamais dans Git)"
touch "$ENV"; chmod 600 "$ENV"
ask() {
  grep -q "^$1=" "$ENV" && { echo "$1 déjà défini."; return; }
  echo; echo "$2"
  if [ "$3" = 1 ]; then read -rsp "$1 = " v; echo; else read -rp "$1 = " v; fi
  [ -n "$v" ] && echo "$1=$v" >> "$ENV"
}
ask CLAUDE_CODE_OAUTH_TOKEN "Jeton Claude : ouvre un 2e onglet du Terminal (Cmd+T), lance 'claude setup-token', connecte-toi, puis colle le jeton ici." 1
ask TELEGRAM_BOT_TOKEN "Jeton du bot (bouton Copy dans BotFather)." 1
ask TELEGRAM_ALLOWED_USER_ID "Ton identifiant Telegram (le nombre donné par @userinfobot)." 0
ask ELEVENLABS_API_KEY "Clé ElevenLabs (optionnel, Entrée pour passer)." 1
grep -q '^WHISPER_LANG=' "$ENV" || echo "WHISPER_LANG=fr" >> "$ENV"

echo
echo "Installation terminée. Pour lancer le bot :  bash $APP_DIR/deploy/run-mac.sh"
