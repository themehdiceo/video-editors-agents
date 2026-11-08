#!/usr/bin/env bash
# Installation complète sur un VPS Ubuntu 22.04 / 24.04 (Contabo, Hetzner…).
# Depuis le Mac, une seule commande (copie les clés du Mac sans les afficher, puis installe) :
#   scp ~/.video-editors-agents.env root@IP:/root/vea.env && ssh -t root@IP 'bash <(curl -fsSL https://raw.githubusercontent.com/themehdiceo/video-editors-agents/main/deploy/install.sh) /root/vea.env'
# Ou directement sur le VPS, en root :  bash <(curl -fsSL https://raw.githubusercontent.com/themehdiceo/video-editors-agents/main/deploy/install.sh)
# Options : WITH_BLENDER=1 pour installer Blender (3D).
set -euo pipefail

APP_USER=editor
APP_DIR=/opt/video-editors-agents
REPO_URL=${REPO_URL:-https://github.com/themehdiceo/video-editors-agents.git}
ENV_DIR=/etc/video-editors-agents

[ "$(id -u)" = 0 ] || { echo "Lance ce script en root (sudo -i)."; exit 1; }
. /etc/os-release
echo "==> Système : $PRETTY_NAME, $(nproc) CPU, $(free -h | awk '/Mem/{print $2}') RAM"

if [ "$(swapon --show | wc -l)" = 0 ]; then
  echo "==> Ajout de 4 Go de swap (évite les plantages mémoire pendant les rendus)"
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "==> Paquets système"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -yq ffmpeg git curl unzip python3 python3-venv python3-pip fonts-dejavu-core \
  ca-certificates gnupg docker.io jq
if [ "${WITH_BLENDER:-0}" = 1 ]; then apt-get install -yq blender; fi

echo "==> Node.js 22 (Claude Code, HyperFrames)"
if ! command -v node >/dev/null || [ "$(node -v | cut -c2- | cut -d. -f1)" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -yq nodejs
fi
npm install -g @anthropic-ai/claude-code
# Navigateur pour HyperFrames (rendu HTML -> vidéo)
npx -y playwright@1 install --with-deps chromium || echo "(!) Chromium non installé : HyperFrames indisponible, le reste fonctionne."

echo "==> Utilisateur dédié sans sudo : $APP_USER"
id -u $APP_USER >/dev/null 2>&1 || useradd -m -s /bin/bash $APP_USER
usermod -aG docker $APP_USER || true

echo "==> Code"
if [ -d $APP_DIR/.git ]; then sudo -u $APP_USER git -C $APP_DIR pull --ff-only
else git clone $REPO_URL $APP_DIR && chown -R $APP_USER:$APP_USER $APP_DIR; fi

echo "==> Environnement Python"
sudo -u $APP_USER python3 -m venv $APP_DIR/.venv
sudo -u $APP_USER $APP_DIR/.venv/bin/pip install -q --upgrade pip
sudo -u $APP_USER $APP_DIR/.venv/bin/pip install -q -r $APP_DIR/requirements.txt
ln -sf $APP_DIR/.venv/bin/yt-dlp /usr/local/bin/yt-dlp

echo "==> Police des sous-titres (Montserrat)"
mkdir -p $APP_DIR/assets/fonts /usr/local/share/fonts/montserrat
for w in ExtraBold Bold Black; do
  curl -fsSL -o /usr/local/share/fonts/montserrat/Montserrat-$w.ttf \
    "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-$w.ttf" || true
done
cp /usr/local/share/fonts/montserrat/*.ttf $APP_DIR/assets/fonts/ 2>/dev/null || true
fc-cache -f >/dev/null || true

echo "==> Modèle Whisper (premier téléchargement)"
sudo -u $APP_USER $APP_DIR/.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" || true

echo "==> Services"
mkdir -p $ENV_DIR && chmod 700 $ENV_DIR
cp $APP_DIR/deploy/video-bot.service /etc/systemd/system/
cp $APP_DIR/deploy/telegram-bot-api.service /etc/systemd/system/
systemctl daemon-reload

if [ -d /root/vea-private ]; then  # notes privées envoyées par le bot du Mac (hors Git)
  mkdir -p $APP_DIR/private && cp -r /root/vea-private/. $APP_DIR/private/ && rm -rf /root/vea-private
fi
mkdir -p /var/lib/telegram-bot-api && chmod 755 /var/lib/telegram-bot-api
chown -R $APP_USER:$APP_USER $APP_DIR

echo
echo "Installation terminée. Il reste les clés :"
bash $APP_DIR/deploy/setup-secrets.sh "${1:-}"
